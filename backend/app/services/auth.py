import secrets
from datetime import datetime, timedelta

from jose import JWTError, jwt

from app.config import settings

_ALGORITHM = "HS256"
_TOKEN_EXPIRE_DAYS = 30


def verify_credentials(username: str, password: str) -> bool:
    return (
        secrets.compare_digest(username, settings.app_username)
        and secrets.compare_digest(password, settings.app_password)
    )


def create_access_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(days=_TOKEN_EXPIRE_DAYS)
    return jwt.encode({"sub": username, "exp": expire}, settings.jwt_secret, algorithm=_ALGORITHM)


def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
