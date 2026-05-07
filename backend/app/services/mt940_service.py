import hashlib
import re
from decimal import Decimal

import mt940
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.document import Document, DocumentSource, DocumentStatus
from app.models.rule import Rule
from app.models.transaction import Transaction, TransactionStatus
from app.services import rule as rule_svc


def _extract_counterparty(details: str) -> str | None:
    m = re.search(r'/NAME/([^/\n]+)', details, re.IGNORECASE)
    if m:
        return m.group(1).strip()[:200] or None
    return None


def _normalize_iban(raw) -> str:
    if raw is None:
        return ""
    s = str(raw)
    # mt940 may return "CH12 3456..." style with spaces
    return s.replace(" ", "").upper()


def _parse_file(content: bytes):
    """Try to parse mt940 bytes; return Transactions object."""
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            decoded = content.decode(encoding)
            transactions = mt940.models.Transactions()
            transactions.parse(decoded)
            return transactions
        except Exception:
            continue
    raise HTTPException(status_code=422, detail="MT940-Datei konnte nicht geparst werden.")


def import_mt940(content: bytes, db: Session, filename: str | None = None) -> dict:
    transactions = _parse_file(content)

    # Extract IBAN from header
    acct_id = transactions.data.get("account_identification")
    iban = _normalize_iban(getattr(acct_id, "account_number", acct_id))

    # Find matching bank account
    bank_account: Account | None = None
    if iban:
        bank_account = (
            db.query(Account)
            .filter(Account.iban.isnot(None))
            .all()
        )
        bank_account = next(
            (a for a in bank_account if _normalize_iban(a.iban) == iban),
            None,
        )

    # Create document
    doc = Document(
        source=DocumentSource.mt940,
        original_file=filename,
        raw_text=content.decode("latin-1", errors="replace")[:65000],
        status=DocumentStatus.pending,
    )
    db.add(doc)
    db.flush()

    created_txs: list[Transaction] = []
    skipped = 0

    for t in transactions:
        data = t.data
        tx_date = data.get("date")
        amount_obj = data.get("amount")
        if not tx_date or amount_obj is None:
            continue

        amount = abs(Decimal(str(amount_obj.amount)))
        # 'C' = credit (money in), 'D' = debit (money out), 'RC'/'RD' = reversals
        status_code = str(data.get("status", "C")).upper().strip()
        reference = str(data.get("customer_reference", "") or "")[:50] or None
        description = str(data.get("transaction_details", "") or "")[:500] or None
        counterparty = _extract_counterparty(description or "")

        tx_hash = hashlib.sha256(
            f"{tx_date}|{amount}|{reference}|{description}".encode()
        ).hexdigest()

        if db.query(Transaction).filter(Transaction.hash == tx_hash).first():
            skipped += 1
            continue

        # C/RC → money into account → bank is debit side (asset increases)
        # D/RD → money out of account → bank is credit side (asset decreases)
        if status_code in ("C", "RC"):
            debit_account_id = bank_account.id if bank_account else None
            credit_account_id = None
        else:
            debit_account_id = None
            credit_account_id = bank_account.id if bank_account else None

        tx = Transaction(
            date=tx_date,
            amount=amount,
            reference=reference,
            description=description,
            counterparty=counterparty,
            debit_account_id=debit_account_id,
            credit_account_id=credit_account_id,
            document_id=doc.id,
            status=TransactionStatus.suggested,
            hash=tx_hash,
        )
        db.add(tx)
        created_txs.append(tx)

    if not created_txs:
        db.rollback()
        return {
            "document_id": None,
            "iban": iban,
            "bank_account_name": None,
            "created": 0,
            "skipped": skipped,
        }

    db.flush()

    # Apply active rules to newly created transactions
    rules = db.query(Rule).filter(Rule.active.is_(True)).order_by(Rule.priority.desc()).all()
    for tx in created_txs:
        rule_svc.apply_to_transaction(tx, rules)

    # If nothing remains open, mark document as booked right away
    still_pending = any(t.status == TransactionStatus.suggested for t in created_txs)
    if not still_pending:
        doc.status = DocumentStatus.booked

    db.commit()

    return {
        "document_id": doc.id,
        "iban": iban,
        "bank_account_name": f"{bank_account.number} {bank_account.name}" if bank_account else None,
        "created": len(created_txs),
        "skipped": skipped,
    }


def book_document(document_id: int, db: Session) -> int:
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")

    txs = (
        db.query(Transaction)
        .filter(
            Transaction.document_id == document_id,
            Transaction.status == TransactionStatus.suggested,
        )
        .all()
    )

    incomplete = [t for t in txs if not t.debit_account_id or not t.credit_account_id]
    if incomplete:
        raise HTTPException(
            status_code=422,
            detail=f"{len(incomplete)} Buchung(en) haben noch kein Gegenkonto.",
        )

    for t in txs:
        t.status = TransactionStatus.booked

    doc.status = DocumentStatus.booked
    db.commit()
    return len(txs)
