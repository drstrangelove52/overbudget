import enum
from decimal import Decimal
from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BudgetPeriod(str, enum.Enum):
    monthly = "monthly"
    yearly = "yearly"


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    period: Mapped[BudgetPeriod] = mapped_column(Enum(BudgetPeriod), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    account: Mapped["Account"] = relationship("Account", back_populates="budgets")  # noqa: F821
