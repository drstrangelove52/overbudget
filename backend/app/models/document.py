import enum
from datetime import datetime
from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class DocumentSource(str, enum.Enum):
    camera = "camera"
    email = "email"
    upload = "upload"
    mt940 = "mt940"
    csv = "csv"


class DocumentStatus(str, enum.Enum):
    new = "new"
    processing = "processing"
    pending = "pending"
    booked = "booked"
    error = "error"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[DocumentSource] = mapped_column(Enum(DocumentSource), nullable=False)
    original_file: Mapped[str | None] = mapped_column(String(500), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus), default=DocumentStatus.new, nullable=False
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    transactions: Mapped[list["Transaction"]] = relationship(  # noqa: F821
        "Transaction", back_populates="document"
    )
