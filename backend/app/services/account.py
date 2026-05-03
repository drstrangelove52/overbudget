from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.account import Account
from app.schemas.account import AccountCreate, AccountUpdate


def get_all(db: Session) -> list[Account]:
    return db.query(Account).order_by(Account.number).all()


def get_by_id(db: Session, account_id: int) -> Account:
    account = db.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Konto nicht gefunden")
    return account


def create(db: Session, data: AccountCreate) -> Account:
    account = Account(**data.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def update(db: Session, account_id: int, data: AccountUpdate) -> Account:
    account = get_by_id(db, account_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    db.commit()
    db.refresh(account)
    return account


def delete(db: Session, account_id: int) -> None:
    account = get_by_id(db, account_id)
    from app.models.account import Account as AccountModel
    has_members = db.query(AccountModel).filter(AccountModel.sum_in == account.number).first()
    if has_members:
        raise HTTPException(status_code=400, detail="Konto ist Sammelkonto mit zugeordneten Konten")
    db.delete(account)
    db.commit()
