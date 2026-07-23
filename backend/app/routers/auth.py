from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import SESSION_COOKIE_NAME, get_current_user
from app.limiter import limiter
from app.services.auth import create_session, delete_session, update_credentials, verify_credentials

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangeCredentialsRequest(BaseModel):
    current_password: str
    new_username: str | None = None
    new_password: str | None = None


def _set_session_cookie(response: Response, token: str, max_age: int) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
    )


@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    if not verify_credentials(db, data.username, data.password):
        raise HTTPException(status_code=401, detail="Ungültige Anmeldedaten")
    token, max_age = create_session(db)
    _set_session_cookie(response, token, max_age)
    return {"detail": "ok"}


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        delete_session(db, token)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"detail": "ok"}


@router.put("/credentials")
def change_credentials(
    data: ChangeCredentialsRequest,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not data.new_username and not data.new_password:
        raise HTTPException(status_code=400, detail="Mindestens Benutzername oder Passwort angeben.")
    if not verify_credentials(db, current_user, data.current_password):
        raise HTTPException(status_code=401, detail="Aktuelles Passwort falsch.")
    update_credentials(db, data.new_username, data.new_password)
    return {"detail": "ok"}
