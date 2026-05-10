from pydantic import BaseModel

from app.models.rule import ConditionField, ConditionLogic, ConditionOperator
from app.schemas.transaction import AccountRef


class ConditionCreate(BaseModel):
    field: ConditionField
    operator: ConditionOperator
    value: str


class ConditionResponse(ConditionCreate):
    id: int

    model_config = {"from_attributes": True}


class RuleCreate(BaseModel):
    name: str
    priority: int = 0
    active: bool = True
    condition_logic: ConditionLogic = ConditionLogic.AND
    conditions: list[ConditionCreate]
    debit_account_id: int | None = None
    credit_account_id: int | None = None
    auto_confirm: bool = False


class RuleUpdate(BaseModel):
    name: str | None = None
    priority: int | None = None
    active: bool | None = None
    condition_logic: ConditionLogic | None = None
    conditions: list[ConditionCreate] | None = None
    debit_account_id: int | None = None
    credit_account_id: int | None = None
    auto_confirm: bool | None = None


class RuleResponse(BaseModel):
    id: int
    name: str
    priority: int
    active: bool
    condition_logic: ConditionLogic
    conditions: list[ConditionResponse]
    debit_account_id: int | None
    credit_account_id: int | None
    debit_account: AccountRef | None
    credit_account: AccountRef | None
    auto_confirm: bool

    model_config = {"from_attributes": True}
