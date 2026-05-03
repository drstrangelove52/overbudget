import enum
from sqlalchemy import Boolean, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AccountType(str, enum.Enum):
    asset = "asset"
    liability = "liability"
    equity = "equity"
    income = "income"
    expense = "expense"


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[AccountType] = mapped_column(Enum(AccountType), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="CHF")
    sum_in: Mapped[str | None] = mapped_column(String(20), nullable=True)
    iban: Mapped[str | None] = mapped_column(String(34), nullable=True)
    is_group: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    debit_transactions: Mapped[list["Transaction"]] = relationship(  # noqa: F821
        "Transaction", foreign_keys="Transaction.debit_account_id", back_populates="debit_account"
    )
    credit_transactions: Mapped[list["Transaction"]] = relationship(  # noqa: F821
        "Transaction", foreign_keys="Transaction.credit_account_id", back_populates="credit_account"
    )
    budgets: Mapped[list["Budget"]] = relationship("Budget", back_populates="account")  # noqa: F821
