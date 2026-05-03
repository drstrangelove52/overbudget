from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.auth import create_access_token, verify_credentials

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    if not verify_credentials(data.username, data.password):
        raise HTTPException(status_code=401, detail="Ungültige Anmeldedaten")
    return {"access_token": create_access_token(data.username), "token_type": "bearer"}
