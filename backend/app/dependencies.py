from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth import get_current_username, validate_session

SESSION_COOKIE_NAME = "session"


def get_current_user(request: Request, db: Session = Depends(get_db)) -> str:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token or not validate_session(db, token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nicht angemeldet")
    username = get_current_username(db)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nicht angemeldet")
    return username
