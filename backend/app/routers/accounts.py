from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.account import AccountCreate, AccountResponse, AccountUpdate
from app.schemas.transaction import TransactionResponse
from app.services import account as svc
from app.services import transaction as tx_svc

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountResponse])
def list_accounts(db: Session = Depends(get_db)):
    return svc.get_all(db)


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account_id: int, db: Session = Depends(get_db)):
    return svc.get_by_id(db, account_id)


@router.post("", response_model=AccountResponse, status_code=201)
def create_account(data: AccountCreate, db: Session = Depends(get_db)):
    return svc.create(db, data)


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(account_id: int, data: AccountUpdate, db: Session = Depends(get_db)):
    return svc.update(db, account_id, data)


@router.get("/{account_id}/transactions", response_model=list[TransactionResponse])
def account_transactions(account_id: int, year: int | None = None, db: Session = Depends(get_db)):
    return tx_svc.get_by_account(db, account_id, year=year)


@router.delete("/{account_id}", status_code=204)
def delete_account(account_id: int, db: Session = Depends(get_db)):
    svc.delete(db, account_id)
