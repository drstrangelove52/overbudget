import csv as csv_module
import hashlib
import io
from datetime import date as date_type
from datetime import datetime
from decimal import Decimal, InvalidOperation

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.document import Document, DocumentSource, DocumentStatus
from app.models.rule import Rule
from app.models.transaction import Transaction, TransactionStatus
from app.services import rule as rule_svc


def _decode(content: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            return content.decode(enc)
        except UnicodeDecodeError:
            continue
    raise HTTPException(422, "CSV-Datei konnte nicht gelesen werden.")


def _detect_delimiter(text: str) -> str:
    first_line = text.split("\n")[0]
    counts = {";": first_line.count(";"), ",": first_line.count(","), "\t": first_line.count("\t")}
    return max(counts, key=counts.get)


def _parse_date(s: str) -> date_type | None:
    s = s.strip()
    for fmt in ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _parse_amount(s: str) -> Decimal | None:
    s = s.strip().replace("\xa0", "").replace(" ", "").replace("'", "")
    if not s:
        return None

    negative = s.startswith("-") or (s.startswith("(") and s.endswith(")"))
    s = s.lstrip("-+").strip("()")

    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        parts = s.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")

    try:
        val = Decimal(s)
        return -val if negative else val
    except InvalidOperation:
        return None


def import_csv(
    content: bytes,
    date_col: int,
    amount_col: int,
    description_col: int | None,
    account_id: int | None,
    account_on_credit_side: bool,
    db: Session,
    filename: str | None = None,
) -> dict:
    text = _decode(content)
    delimiter = _detect_delimiter(text)

    reader = csv_module.reader(io.StringIO(text), delimiter=delimiter)
    rows = list(reader)

    if len(rows) < 2:
        raise HTTPException(422, "CSV-Datei enthält keine Daten.")

    fixed_account: Account | None = db.get(Account, account_id) if account_id else None

    doc = Document(
        source=DocumentSource.csv,
        original_file=filename,
        raw_text=text[:65000],
        status=DocumentStatus.pending,
    )
    db.add(doc)
    db.flush()

    created_txs: list[Transaction] = []
    skipped = 0

    for row in rows[1:]:
        if not row or all(c.strip() == "" for c in row):
            continue

        try:
            date_val = _parse_date(row[date_col]) if date_col < len(row) else None
            amount_raw = row[amount_col].strip() if amount_col < len(row) else ""
            amount = _parse_amount(amount_raw)
            desc_raw = row[description_col].strip() if description_col is not None and description_col < len(row) else None
            desc = desc_raw or None
        except IndexError:
            continue

        if not date_val or amount is None:
            continue

        amount_abs = abs(amount)
        amount_negative = amount < 0

        tx_hash = hashlib.sha256(
            f"{date_val}|{amount_abs}|{desc}|csv".encode()
        ).hexdigest()

        if db.query(Transaction).filter(Transaction.hash == tx_hash).first():
            skipped += 1
            continue

        # Determine account sides based on sign and account_on_credit_side flag
        # account_on_credit_side=True (credit card): positive → fixed account on credit side
        # account_on_credit_side=False (bank): positive → fixed account on debit side
        if fixed_account:
            positive_is_credit = account_on_credit_side
            fixed_on_credit = positive_is_credit if not amount_negative else not positive_is_credit
            if fixed_on_credit:
                debit_account_id = None
                credit_account_id = fixed_account.id
            else:
                debit_account_id = fixed_account.id
                credit_account_id = None
        else:
            debit_account_id = None
            credit_account_id = None

        tx = Transaction(
            date=date_val,
            amount=amount_abs,
            description=desc,
            debit_account_id=debit_account_id,
            credit_account_id=credit_account_id,
            document_id=doc.id,
            status=TransactionStatus.suggested,
            hash=tx_hash,
        )
        db.add(tx)
        created_txs.append(tx)

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
        "account_name": f"{fixed_account.number} {fixed_account.name}" if fixed_account else None,
        "created": len(created_txs),
        "skipped": skipped,
    }
