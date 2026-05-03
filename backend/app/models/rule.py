import enum
from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ConditionField(str, enum.Enum):
    counterparty = "counterparty"
    description = "description"
    amount = "amount"
    iban = "iban"


class ConditionOperator(str, enum.Enum):
    contains = "contains"
    equals = "equals"
    lt = "lt"
    gt = "gt"
    regex = "regex"


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    condition_field: Mapped[ConditionField] = mapped_column(Enum(ConditionField), nullable=False)
    condition_operator: Mapped[ConditionOperator] = mapped_column(Enum(ConditionOperator), nullable=False)
    condition_value: Mapped[str] = mapped_column(String(500), nullable=False)
    debit_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    credit_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    auto_confirm: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    learned_from_transaction_id: Mapped[int | None] = mapped_column(
        ForeignKey("transactions.id"), nullable=True
    )

    debit_account: Mapped["Account | None"] = relationship(  # noqa: F821
        "Account", foreign_keys=[debit_account_id]
    )
    credit_account: Mapped["Account | None"] = relationship(  # noqa: F821
        "Account", foreign_keys=[credit_account_id]
    )
    transactions: Mapped[list["Transaction"]] = relationship(  # noqa: F821
        "Transaction", foreign_keys="Transaction.rule_id", back_populates="rule"
    )
