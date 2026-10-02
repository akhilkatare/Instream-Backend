import os
import jwt
import uuid
from datetime import datetime, timedelta, timezone


JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def _create_token(subject: str, token_type: str, expires_delta: timedelta, extra: dict | None = None) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": uuid.uuid4().hex,
    }

    if extra:
        payload.update(extra)

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_access_token(subject: str, extra: dict | None = None) -> str:
    return _create_token(subject, "access", timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES), extra)


def create_refresh_token(subject: str) -> str:
    return _create_token(subject, "refresh", timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))


def decode_token(token: str) -> dict:
    """Raises jwt.ExpiredSignatureError / jwt.InvalidTokenError on bad tokens."""
    
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
