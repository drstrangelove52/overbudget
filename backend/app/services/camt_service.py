import hashlib
from decimal import Decimal
from xml.etree import ElementTree as ET

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.document import Document, DocumentSource, DocumentStatus
from app.models.rule import Rule
from app.models.transaction import Transaction, TransactionStatus
from app.services import rule as rule_svc


def _strip_ns(tag: str) -> str:
    return tag.split('}', 1)[-1] if '}' in tag else tag


def _find(elem, *tags):
    current = elem
    for tag in tags:
        found = next((c for c in current if _strip_ns(c.tag) == tag), None)
        if found is None:
            return None
        current = found
    return current


def _findall(elem, tag: str):
    return [c for c in elem if _strip_ns(c.tag) == tag]


def _text(elem, *tags) -> str | None:
    node = _find(elem, *tags)
    return node.text.strip() if node is not None and node.text else None


def _normalize_iban(raw: str | None) -> str:
    return raw.replace(" ", "").upper() if raw else ""


def _parse_xml(content: bytes) -> ET.Element:
    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            return ET.fromstring(content.decode(enc))
        except Exception:
            continue
    raise HTTPException(status_code=422, detail="CAMT.053-Datei konnte nicht geparst werden.")


def import_camt053(content: bytes, db: Session, filename: str | None = None) -> dict:
    root = _parse_xml(content)

    bk_stmt = _find(root, 'BkToCstmrStmt')
    if bk_stmt is None:
        raise HTTPException(status_code=422, detail="Kein BkToCstmrStmt-Element gefunden — ist das eine CAMT.053-Datei?")

    stmt = _find(bk_stmt, 'Stmt')
    if stmt is None:
        raise HTTPException(status_code=422, detail="Kein Stmt-Element gefunden.")

    iban = _normalize_iban(_text(stmt, 'Acct', 'Id', 'IBAN'))

    bank_account: Account | None = None
    if iban:
        all_accounts = db.query(Account).filter(Account.iban.isnot(None)).all()
        bank_account = next(
            (a for a in all_accounts if _normalize_iban(a.iban) == iban),
            None,
        )

    doc = Document(
        source=DocumentSource.camt053,
        original_file=filename,
        raw_text=content.decode("utf-8", errors="replace")[:65000],
        status=DocumentStatus.pending,
    )
    db.add(doc)
    db.flush()

    created_txs: list[Transaction] = []
    skipped = 0

    for ntry in _findall(stmt, 'Ntry'):
        amt_elem = _find(ntry, 'Amt')
        cdi = _text(ntry, 'CdtDbtInd')  # CRDT/CDT = money in, DBIT/DBT = money out
        date_str = (
            _text(ntry, 'BookgDt', 'Dt')
            or _text(ntry, 'BookgDt', 'DtTm', )
            or _text(ntry, 'ValDt', 'Dt')
            or _text(ntry, 'ValDt', 'DtTm')
        )
        # Some banks put the date only in TxDtls
        if not date_str:
            dtls_elem = _find(ntry, 'NtryDtls', 'TxDtls')
            if dtls_elem is not None:
                date_str = (
                    _text(dtls_elem, 'RltdDts', 'AccptncDtTm')
                    or _text(dtls_elem, 'RltdDts', 'IntrBkSttlmDt')
                )
        # Truncate datetime to date if needed
        if date_str and 'T' in date_str:
            date_str = date_str.split('T')[0]

        if amt_elem is None or not cdi or not date_str:
            skipped += 1
            continue
        try:
            amount = abs(Decimal(amt_elem.text.strip()))
        except Exception:
            skipped += 1
            continue

        tx_dtls = _find(ntry, 'NtryDtls', 'TxDtls')

        reference = None
        description = None
        counterparty = None

        if tx_dtls is not None:
            reference = (
                _text(tx_dtls, 'Refs', 'EndToEndId')
                or _text(tx_dtls, 'Refs', 'AcctSvcrRef')
                or _text(ntry, 'AcctSvcrRef')
            )
            rmtinf = _find(tx_dtls, 'RmtInf')
            if rmtinf is not None:
                parts = [c.text.strip() for c in rmtinf if c.text]
                description = ' '.join(parts)[:500] or None

            rltd = _find(tx_dtls, 'RltdPties')
            if rltd is not None:
                # CRDT/CDT: money arrives from Debtor; DBIT/DBT: money goes to Creditor
                if cdi.upper().startswith('C'):
                    counterparty = _text(rltd, 'Dbtr', 'Nm') or _text(rltd, 'DbtrAcct', 'Id', 'IBAN')
                else:
                    counterparty = _text(rltd, 'Cdtr', 'Nm') or _text(rltd, 'CdtrAcct', 'Id', 'IBAN')
        else:
            reference = _text(ntry, 'AcctSvcrRef')

        if not description:
            description = _text(ntry, 'AddtlNtryInf')

        tx_hash = hashlib.sha256(
            f"{date_str}|{amount}|{reference}|{description}".encode()
        ).hexdigest()

        if db.query(Transaction).filter(Transaction.hash == tx_hash).first():
            skipped += 1
            continue

        if cdi.upper().startswith('C'):
            debit_account_id = bank_account.id if bank_account else None
            credit_account_id = None
        else:
            debit_account_id = None
            credit_account_id = bank_account.id if bank_account else None

        tx = Transaction(
            date=date_str,
            amount=amount,
            reference=(reference or '')[:50] or None,
            description=description,
            counterparty=(counterparty or '')[:200] or None,
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

    rules = db.query(Rule).filter(Rule.active.is_(True)).order_by(Rule.priority.desc()).all()
    for tx in created_txs:
        rule_svc.apply_to_transaction(tx, rules)

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
