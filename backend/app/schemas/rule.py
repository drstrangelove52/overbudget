from pydantic import BaseModel

from app.models.rule import ConditionField, ConditionOperator
from app.schemas.transaction import AccountRef


class RuleCreate(BaseModel):
    name: str
    priority: int = 0
    active: bool = True
    condition_field: ConditionField
    condition_operator: ConditionOperator
    condition_value: str
    debit_account_id: int | None = None
    credit_account_id: int | None = None
    auto_confirm: bool = False


class RuleUpdate(BaseModel):
    name: str | None = None
    priority: int | None = None
    active: bool | None = None
    condition_field: ConditionField | None = None
    condition_operator: ConditionOperator | None = None
    condition_value: str | None = None
    debit_account_id: int | None = None
    credit_account_id: int | None = None
    auto_confirm: bool | None = None


class RuleResponse(BaseModel):
    id: int
    name: str
    priority: int
    active: bool
    condition_field: ConditionField
    condition_operator: ConditionOperator
    condition_value: str
    debit_account_id: int | None
    credit_account_id: int | None
    debit_account: AccountRef | None
    credit_account: AccountRef | None
    auto_confirm: bool

    model_config = {"from_attributes": True}
