from fastapi import APIRouter, Depends, Form, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document
from app.models.transaction import Transaction, TransactionStatus
from app.schemas.document import Camt053ImportResult, CsvImportResult, DocumentResponse, Mt940ImportResult
from app.schemas.transaction import TransactionResponse
from app.services import camt_service, csv_service, mt940_service, transaction as tx_svc

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.received_at.desc()).all()
    result = []
    for doc in docs:
        txs = db.query(Transaction).filter(Transaction.document_id == doc.id).all()
        result.append(DocumentResponse(
            id=doc.id,
            source=doc.source,
            status=doc.status,
            received_at=doc.received_at,
            original_file=doc.original_file,
            transaction_count=len(txs),
            suggested_count=sum(1 for t in txs if t.status == TransactionStatus.suggested),
            total_amount=float(sum(t.amount for t in txs)),
        ))
    return result


@router.post("/mt940", response_model=Mt940ImportResult, status_code=201)
async def upload_mt940(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    return mt940_service.import_mt940(content, db, filename=file.filename)


@router.post("/camt053", response_model=Camt053ImportResult, status_code=201)
async def upload_camt053(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    return camt_service.import_camt053(content, db, filename=file.filename)


@router.post("/csv", response_model=CsvImportResult, status_code=201)
async def upload_csv(
    file: UploadFile = File(...),
    date_col: int = Form(...),
    amount_col: int = Form(...),
    description_col: int | None = Form(None),
    account_id: int | None = Form(None),
    account_on_credit_side: bool = Form(False),
    db: Session = Depends(get_db),
):
    content = await file.read()
    return csv_service.import_csv(
        content, date_col, amount_col, description_col,
        account_id, account_on_credit_side, db,
        filename=file.filename,
    )


@router.get("/{document_id}/transactions", response_model=list[TransactionResponse])
def document_transactions(document_id: int, db: Session = Depends(get_db)):
    return tx_svc.get_by_document(db, document_id)


@router.post("/{document_id}/book")
def book_document(document_id: int, db: Session = Depends(get_db)):
    booked = mt940_service.book_document(document_id, db)
    return {"booked": booked}


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Import nicht gefunden")
    db.query(Transaction).filter(Transaction.document_id == document_id).delete()
    db.delete(doc)
    db.commit()
