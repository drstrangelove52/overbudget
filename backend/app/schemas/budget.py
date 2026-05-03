from decimal import Decimal
from pydantic import BaseModel

from app.models.budget import BudgetPeriod
from app.schemas.transaction import AccountRef


class BudgetCreate(BaseModel):
    account_id: int
    name: str
    amount: Decimal
    period: BudgetPeriod
    active: bool = True


class BudgetUpdate(BaseModel):
    account_id: int | None = None
    name: str | None = None
    amount: Decimal | None = None
    period: BudgetPeriod | None = None
    active: bool | None = None


class BudgetResponse(BaseModel):
    id: int
    account_id: int
    account: AccountRef
    name: str
    amount: Decimal
    period: BudgetPeriod
    active: bool

    model_config = {"from_attributes": True}
