from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.rule import RuleCreate, RulePreviewRequest, RulePreviewResponse, RuleResponse, RuleUpdate
from app.services import rule as svc

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("", response_model=list[RuleResponse])
def list_rules(db: Session = Depends(get_db)):
    return svc.get_all(db)


@router.post("", response_model=RuleResponse, status_code=201)
def create_rule(data: RuleCreate, db: Session = Depends(get_db)):
    return svc.create(db, data)


@router.put("/{rule_id}", response_model=RuleResponse)
def update_rule(rule_id: int, data: RuleUpdate, db: Session = Depends(get_db)):
    return svc.update(db, rule_id, data)


@router.delete("/{rule_id}", status_code=204)
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    svc.delete(db, rule_id)


@router.post("/preview", response_model=RulePreviewResponse)
def preview_rule(data: RulePreviewRequest, db: Session = Depends(get_db)):
    return svc.preview(db, data.condition_logic, data.conditions)


@router.post("/apply")
def apply_rules(db: Session = Depends(get_db)):
    return svc.apply_all(db)
