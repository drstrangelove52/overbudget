import enum
from datetime import date
from decimal import Decimal
from sqlalchemy import Boolean, Date, Enum, Float, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TransactionStatus(str, enum.Enum):
    suggested = "suggested"
    confirmed = "confirmed"
    booked = "booked"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    counterparty: Mapped[str | None] = mapped_column(String(200), nullable=True)
    debit_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    credit_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus), default=TransactionStatus.suggested, nullable=False
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_transfer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("rules.id"), nullable=True)
    hash: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    group_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    group_description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    debit_account: Mapped["Account | None"] = relationship(  # noqa: F821
        "Account", foreign_keys=[debit_account_id], back_populates="debit_transactions"
    )
    credit_account: Mapped["Account | None"] = relationship(  # noqa: F821
        "Account", foreign_keys=[credit_account_id], back_populates="credit_transactions"
    )
    document: Mapped["Document | None"] = relationship("Document", back_populates="transactions")  # noqa: F821
    rule: Mapped["Rule | None"] = relationship("Rule", foreign_keys=[rule_id], back_populates="transactions")  # noqa: F821
