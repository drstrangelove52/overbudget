import secrets
from datetime import datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy.orm import Session as DBSession

from app.config import settings
from app.models.app_setting import AppSetting
from app.models.auth_session import AuthSession

_KEY_USERNAME = "auth.username"
_KEY_PASSWORD_HASH = "auth.password_hash"
SESSION_MAX_AGE_DAYS = 30

_ph = PasswordHasher()


def _hash(password: str) -> str:
    return _ph.hash(password)


def _verify(password: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, password)
    except VerifyMismatchError:
        return False


def _get(db: DBSession, key: str) -> str | None:
    row = db.get(AppSetting, key)
    return row.value if row else None


def _set(db: DBSession, key: str, value: str) -> None:
    row = db.get(AppSetting, key)
    if row:
        row.value = value
    else:
        db.add(AppSetting(key=key, value=value))
    db.commit()


def seed_credentials(db: DBSession) -> None:
    if _get(db, _KEY_USERNAME) is None:
        _set(db, _KEY_USERNAME, settings.app_username)
    if _get(db, _KEY_PASSWORD_HASH) is None:
        _set(db, _KEY_PASSWORD_HASH, _hash(settings.app_password))


def get_current_username(db: DBSession) -> str | None:
    return _get(db, _KEY_USERNAME)


def verify_credentials(db: DBSession, username: str, password: str) -> bool:
    stored_username = _get(db, _KEY_USERNAME)
    stored_hash = _get(db, _KEY_PASSWORD_HASH)
    if stored_username is None or stored_hash is None:
        return False
    return (
        secrets.compare_digest(username, stored_username)
        and _verify(password, stored_hash)
    )


def update_credentials(db: DBSession, new_username: str | None, new_password: str | None) -> str:
    current_username = _get(db, _KEY_USERNAME) or settings.app_username
    if new_username:
        _set(db, _KEY_USERNAME, new_username)
        current_username = new_username
    if new_password:
        _set(db, _KEY_PASSWORD_HASH, _hash(new_password))
    return current_username


def create_session(db: DBSession) -> tuple[str, int]:
    """Creates a new session token and opportunistically prunes expired ones.
    Returns (token, max_age_seconds) for the Set-Cookie header."""
    db.query(AuthSession).filter(AuthSession.expires_at < datetime.utcnow()).delete()
    token = secrets.token_urlsafe(32)
    now = datetime.utcnow()
    db.add(AuthSession(token=token, created_at=now, expires_at=now + timedelta(days=SESSION_MAX_AGE_DAYS)))
    db.commit()
    return token, SESSION_MAX_AGE_DAYS * 24 * 3600


def validate_session(db: DBSession, token: str) -> bool:
    row = db.get(AuthSession, token)
    if row is None:
        return False
    if row.expires_at < datetime.utcnow():
        db.delete(row)
        db.commit()
        return False
    return True


def delete_session(db: DBSession, token: str) -> None:
    row = db.get(AuthSession, token)
    if row:
        db.delete(row)
        db.commit()
