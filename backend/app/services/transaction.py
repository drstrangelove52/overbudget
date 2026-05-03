from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.transaction import Transaction, TransactionStatus
from app.schemas.transaction import TransactionCreate, TransactionUpdate, SplitCreate


def _with_accounts(q):
    return q.options(
        joinedload(Transaction.debit_account),
        joinedload(Transaction.credit_account),
    )


def get_all(db: Session, year: int | None = None) -> list[Transaction]:
    from sqlalchemy import extract
    q = (
        _with_accounts(db.query(Transaction))
        .filter(Transaction.status == TransactionStatus.booked)
    )
    if year is not None:
        q = q.filter(extract('year', Transaction.date) == year)
    return q.order_by(Transaction.date.asc(), Transaction.id.asc()).all()


def get_by_document(db: Session, document_id: int) -> list[Transaction]:
    return (
        _with_accounts(db.query(Transaction))
        .filter(Transaction.document_id == document_id)
        .order_by(Transaction.date.asc(), Transaction.id.asc())
        .all()
    )


def get_by_id(db: Session, transaction_id: int) -> Transaction:
    t = _with_accounts(db.query(Transaction)).filter(Transaction.id == transaction_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Buchung nicht gefunden")
    return t


def create(db: Session, data: TransactionCreate) -> Transaction:
    t = Transaction(**data.model_dump(), status=TransactionStatus.booked)
    db.add(t)
    db.commit()
    return get_by_id(db, t.id)


def update(db: Session, transaction_id: int, data: TransactionUpdate) -> Transaction:
    t = get_by_id(db, transaction_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(t, field, value)
    db.commit()
    return get_by_id(db, t.id)


def delete(db: Session, transaction_id: int) -> None:
    t = db.get(Transaction, transaction_id)
    if not t:
        raise HTTPException(status_code=404, detail="Buchung nicht gefunden")
    if t.group_id is not None:
        db.query(Transaction).filter(Transaction.group_id == t.group_id).delete()
    else:
        db.delete(t)
    db.commit()


def split_transaction(db: Session, transaction_id: int, data: SplitCreate) -> list[Transaction]:
    original = get_by_id(db, transaction_id)
    doc_id = original.document_id
    original_hash = original.hash
    original_status = original.status
    db.delete(original)
    db.flush()
    next_group_id = (db.query(func.max(Transaction.group_id)).scalar() or 0) + 1
    created = []
    for i, line in enumerate(data.lines):
        t = Transaction(
            date=data.date,
            reference=data.reference,
            description=line.description,
            group_description=data.description,
            credit_account_id=data.credit_account_id,
            debit_account_id=line.debit_account_id,
            amount=line.amount,
            status=original_status,
            group_id=next_group_id,
            document_id=doc_id,
            hash=original_hash if i == 0 else None,
        )
        db.add(t)
        created.append(t)
    db.commit()
    return [get_by_id(db, t.id) for t in created]


def update_split(db: Session, group_id: int, data: SplitCreate) -> list[Transaction]:
    existing = db.query(Transaction).filter(Transaction.group_id == group_id).order_by(Transaction.id.asc()).all()
    if not existing:
        raise HTTPException(status_code=404, detail="Splittbuchung nicht gefunden")
    doc_id = existing[0].document_id
    preserved_status = existing[0].status
    preserved_hash = next((t.hash for t in existing if t.hash), None)
    db.query(Transaction).filter(Transaction.group_id == group_id).delete()
    db.flush()
    created = []
    for i, line in enumerate(data.lines):
        t = Transaction(
            date=data.date,
            reference=data.reference,
            description=line.description,
            group_description=data.description,
            credit_account_id=data.credit_account_id,
            debit_account_id=line.debit_account_id,
            amount=line.amount,
            status=preserved_status,
            group_id=group_id,
            document_id=doc_id,
            hash=preserved_hash if i == 0 else None,
        )
        db.add(t)
        created.append(t)
    db.commit()
    return [get_by_id(db, t.id) for t in created]


def create_split(db: Session, data: SplitCreate) -> list[Transaction]:
    next_group_id = (db.query(func.max(Transaction.group_id)).scalar() or 0) + 1
    created = []
    for line in data.lines:
        t = Transaction(
            date=data.date,
            reference=data.reference,
            description=line.description,
            group_description=data.description,
            credit_account_id=data.credit_account_id,
            debit_account_id=line.debit_account_id,
            amount=line.amount,
            status=TransactionStatus.booked,
            group_id=next_group_id,
        )
        db.add(t)
        created.append(t)
    db.commit()
    return [get_by_id(db, t.id) for t in created]
