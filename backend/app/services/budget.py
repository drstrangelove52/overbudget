from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.budget import Budget
from app.schemas.budget import BudgetCreate, BudgetUpdate


def _load(q):
    return q.options(joinedload(Budget.account))


def get_all(db: Session) -> list[Budget]:
    return _load(db.query(Budget)).order_by(Budget.id).all()


def get_by_id(db: Session, budget_id: int) -> Budget:
    b = _load(db.query(Budget)).filter(Budget.id == budget_id).first()
    if not b:
        raise HTTPException(404, "Budget nicht gefunden")
    return b


def create(db: Session, data: BudgetCreate) -> Budget:
    b = Budget(**data.model_dump())
    db.add(b)
    db.commit()
    return get_by_id(db, b.id)


def update(db: Session, budget_id: int, data: BudgetUpdate) -> Budget:
    b = get_by_id(db, budget_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(b, field, value)
    db.commit()
    return get_by_id(db, budget_id)


def delete(db: Session, budget_id: int) -> None:
    b = db.get(Budget, budget_id)
    if not b:
        raise HTTPException(404, "Budget nicht gefunden")
    db.delete(b)
    db.commit()
