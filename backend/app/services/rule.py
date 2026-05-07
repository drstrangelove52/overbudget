import re
from decimal import Decimal, InvalidOperation
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.rule import Rule, ConditionField, ConditionOperator
from app.models.transaction import Transaction, TransactionStatus
from app.schemas.rule import RuleCreate, RuleUpdate


def _load(q):
    return q.options(
        joinedload(Rule.debit_account),
        joinedload(Rule.credit_account),
    )


def get_all(db: Session) -> list[Rule]:
    return _load(db.query(Rule)).order_by(Rule.priority.desc(), Rule.id).all()


def get_by_id(db: Session, rule_id: int) -> Rule:
    r = _load(db.query(Rule)).filter(Rule.id == rule_id).first()
    if not r:
        raise HTTPException(404, "Regel nicht gefunden")
    return r


def create(db: Session, data: RuleCreate) -> Rule:
    r = Rule(**data.model_dump())
    db.add(r)
    db.commit()
    return get_by_id(db, r.id)


def update(db: Session, rule_id: int, data: RuleUpdate) -> Rule:
    r = get_by_id(db, rule_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(r, field, value)
    db.commit()
    return get_by_id(db, rule_id)


def delete(db: Session, rule_id: int) -> None:
    r = db.get(Rule, rule_id)
    if not r:
        raise HTTPException(404, "Regel nicht gefunden")
    db.delete(r)
    db.commit()


def _matches(tx: Transaction, rule: Rule) -> bool:
    field = rule.condition_field
    if field == ConditionField.description:
        target = tx.description or ""
    elif field == ConditionField.counterparty:
        target = tx.counterparty or ""
    elif field == ConditionField.amount:
        target = str(tx.amount)
    else:
        return False

    value = rule.condition_value
    op = rule.condition_operator
    if op == ConditionOperator.contains:
        return value.lower() in target.lower()
    elif op == ConditionOperator.equals:
        return value.lower() == target.lower()
    elif op == ConditionOperator.lt:
        try:
            return Decimal(target) < Decimal(value)
        except InvalidOperation:
            return False
    elif op == ConditionOperator.gt:
        try:
            return Decimal(target) > Decimal(value)
        except InvalidOperation:
            return False
    elif op == ConditionOperator.regex:
        try:
            return bool(re.search(value, target, re.IGNORECASE))
        except re.error:
            return False
    return False


def apply_to_transaction(tx: Transaction, rules: list[Rule], force: bool = False) -> bool:
    for rule in sorted(rules, key=lambda r: r.priority, reverse=True):
        if not rule.active:
            continue
        if _matches(tx, rule):
            if rule.debit_account_id and (force or not tx.debit_account_id):
                tx.debit_account_id = rule.debit_account_id
            if rule.credit_account_id and (force or not tx.credit_account_id):
                tx.credit_account_id = rule.credit_account_id
            tx.rule_id = rule.id
            if rule.auto_confirm and tx.debit_account_id and tx.credit_account_id:
                tx.status = TransactionStatus.booked
            return True
    return False


def apply_all(db: Session) -> dict:
    rules = db.query(Rule).filter(Rule.active.is_(True)).order_by(Rule.priority.desc()).all()
    suggested = db.query(Transaction).filter(Transaction.status == TransactionStatus.suggested).all()
    matched = sum(1 for t in suggested if apply_to_transaction(t, rules, force=True))
    db.commit()
    return {"total": len(suggested), "matched": matched}
