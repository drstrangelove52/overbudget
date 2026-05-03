from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.budget import BudgetCreate, BudgetResponse, BudgetUpdate
from app.services import budget as svc

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.get("", response_model=list[BudgetResponse])
def list_budgets(db: Session = Depends(get_db)):
    return svc.get_all(db)


@router.post("", response_model=BudgetResponse, status_code=201)
def create_budget(data: BudgetCreate, db: Session = Depends(get_db)):
    return svc.create(db, data)


@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(budget_id: int, data: BudgetUpdate, db: Session = Depends(get_db)):
    return svc.update(db, budget_id, data)


@router.delete("/{budget_id}", status_code=204)
def delete_budget(budget_id: int, db: Session = Depends(get_db)):
    svc.delete(db, budget_id)
