from app.workers.celery_app import celery


@celery.task
def process_document(document_id: int) -> dict:
    # Platzhalter — wird in späteren Schritten implementiert
    return {"document_id": document_id, "status": "ok"}
