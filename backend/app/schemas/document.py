from datetime import datetime
from pydantic import BaseModel

from app.models.document import DocumentSource, DocumentStatus


class DocumentResponse(BaseModel):
    id: int
    source: DocumentSource
    status: DocumentStatus
    received_at: datetime
    original_file: str | None = None
    transaction_count: int = 0
    suggested_count: int = 0
    total_amount: float = 0.0

    model_config = {"from_attributes": True}


class Mt940ImportResult(BaseModel):
    document_id: int
    iban: str
    bank_account_name: str | None
    created: int
    skipped: int


class CsvImportResult(BaseModel):
    document_id: int
    account_name: str | None
    created: int
    skipped: int
