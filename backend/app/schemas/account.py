from pydantic import BaseModel

from app.models.account import AccountType


class AccountBase(BaseModel):
    number: str
    name: str
    type: AccountType
    currency: str = "CHF"
    sum_in: str | None = None
    iban: str | None = None
    is_group: bool = False
    active: bool = True


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    number: str | None = None
    name: str | None = None
    type: AccountType | None = None
    currency: str | None = None
    sum_in: str | None = None
    iban: str | None = None
    is_group: bool | None = None
    active: bool | None = None


class AccountResponse(AccountBase):
    id: int

    model_config = {"from_attributes": True}
