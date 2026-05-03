from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.transaction import TransactionCreate, TransactionResponse, TransactionUpdate, SplitCreate
from app.services import transaction as svc

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionResponse])
def list_transactions(year: int | None = None, db: Session = Depends(get_db)):
    return svc.get_all(db, year=year)


@router.post("", response_model=TransactionResponse, status_code=201)
def create_transaction(data: TransactionCreate, db: Session = Depends(get_db)):
    return svc.create(db, data)


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(transaction_id: int, data: TransactionUpdate, db: Session = Depends(get_db)):
    return svc.update(db, transaction_id, data)


@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    svc.delete(db, transaction_id)


@router.post("/split", response_model=list[TransactionResponse], status_code=201)
def create_split(data: SplitCreate, db: Session = Depends(get_db)):
    return svc.create_split(db, data)


@router.put("/split/{group_id}", response_model=list[TransactionResponse])
def update_split(group_id: int, data: SplitCreate, db: Session = Depends(get_db)):
    return svc.update_split(db, group_id, data)


@router.post("/{transaction_id}/split", response_model=list[TransactionResponse], status_code=201)
def split_transaction(transaction_id: int, data: SplitCreate, db: Session = Depends(get_db)):
    return svc.split_transaction(db, transaction_id, data)
