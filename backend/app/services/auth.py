import secrets
from datetime import datetime, timedelta

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models.app_setting import AppSetting

_ALGORITHM = "HS256"
_TOKEN_EXPIRE_DAYS = 30
_KEY_USERNAME = "auth.username"
_KEY_PASSWORD_HASH = "auth.password_hash"


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def _get(db: Session, key: str) -> str | None:
    row = db.get(AppSetting, key)
    return row.value if row else None


def _set(db: Session, key: str, value: str) -> None:
    row = db.get(AppSetting, key)
    if row:
        row.value = value
    else:
        db.add(AppSetting(key=key, value=value))
    db.commit()


def seed_credentials(db: Session) -> None:
    if _get(db, _KEY_USERNAME) is None:
        _set(db, _KEY_USERNAME, settings.app_username)
        _set(db, _KEY_PASSWORD_HASH, _hash(settings.app_password))


def verify_credentials(db: Session, username: str, password: str) -> bool:
    stored_username = _get(db, _KEY_USERNAME)
    stored_hash = _get(db, _KEY_PASSWORD_HASH)
    if stored_username is None or stored_hash is None:
        return False
    return (
        secrets.compare_digest(username, stored_username)
        and _verify(password, stored_hash)
    )


def update_credentials(db: Session, new_username: str | None, new_password: str | None) -> str:
    current_username = _get(db, _KEY_USERNAME) or settings.app_username
    if new_username:
        _set(db, _KEY_USERNAME, new_username)
        current_username = new_username
    if new_password:
        _set(db, _KEY_PASSWORD_HASH, _hash(new_password))
    return current_username


def create_access_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(days=_TOKEN_EXPIRE_DAYS)
    return jwt.encode({"sub": username, "exp": expire}, settings.jwt_secret, algorithm=_ALGORITHM)


def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
