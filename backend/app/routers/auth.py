from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.services.auth import create_access_token, update_credentials, verify_credentials

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangeCredentialsRequest(BaseModel):
    current_password: str
    new_username: str | None = None
    new_password: str | None = None


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    if not verify_credentials(db, data.username, data.password):
        raise HTTPException(status_code=401, detail="Ungültige Anmeldedaten")
    return {"access_token": create_access_token(data.username), "token_type": "bearer"}


@router.put("/credentials", response_model=TokenResponse)
def change_credentials(
    data: ChangeCredentialsRequest,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not data.new_username and not data.new_password:
        raise HTTPException(status_code=400, detail="Mindestens Benutzername oder Passwort angeben.")
    if not verify_credentials(db, current_user, data.current_password):
        raise HTTPException(status_code=401, detail="Aktuelles Passwort falsch.")
    new_username = update_credentials(db, data.new_username, data.new_password)
    return {"access_token": create_access_token(new_username), "token_type": "bearer"}
