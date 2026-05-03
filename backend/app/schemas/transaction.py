from datetime import date as Date
from decimal import Decimal
from pydantic import BaseModel, model_validator

from app.models.transaction import TransactionStatus


class AccountRef(BaseModel):
    id: int
    number: str
    name: str
    model_config = {"from_attributes": True}


class TransactionCreate(BaseModel):
    date: Date
    amount: Decimal
    reference: str | None = None
    description: str | None = None
    debit_account_id: int
    credit_account_id: int


class TransactionUpdate(BaseModel):
    date: Date | None = None
    amount: Decimal | None = None
    reference: str | None = None
    description: str | None = None
    debit_account_id: int | None = None
    credit_account_id: int | None = None


class TransactionResponse(BaseModel):
    id: int
    date: Date
    amount: Decimal
    reference: str | None
    description: str | None
    counterparty: str | None
    debit_account_id: int | None
    credit_account_id: int | None
    debit_account: AccountRef | None
    credit_account: AccountRef | None
    status: TransactionStatus
    document_id: int | None
    group_id: int | None
    group_description: str | None

    model_config = {"from_attributes": True}


class SplitLineCreate(BaseModel):
    description: str
    debit_account_id: int
    amount: Decimal


class SplitCreate(BaseModel):
    date: Date
    reference: str | None = None
    description: str | None = None
    credit_account_id: int
    lines: list[SplitLineCreate]

    @model_validator(mode="after")
    def at_least_two_lines(self):
        if len(self.lines) < 2:
            raise ValueError("Eine Splittbuchung benötigt mindestens 2 Zeilen.")
        return self
