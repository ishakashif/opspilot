import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from dotenv import load_dotenv

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_LIFETIME = timedelta(minutes=30)
_MIN_SECRET_LENGTH = 32
_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


class TokenConfigError(Exception):
    """Raised when JWT signing is not configured."""


def create_access_token(user_id: int) -> str:
    secret = _load_jwt_secret()
    issued_at = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": issued_at,
        "exp": issued_at + ACCESS_TOKEN_LIFETIME,
    }
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> int | None:
    secret = _load_jwt_secret()
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "iat", "exp"]},
        )
    except jwt.InvalidTokenError:
        return None

    try:
        return int(payload["sub"])
    except (TypeError, ValueError):
        return None


def _load_jwt_secret() -> str:
    load_dotenv(_ENV_PATH)
    secret = os.environ.get("JWT_SECRET_KEY")
    if secret is None or not secret.strip():
        raise TokenConfigError("JWT_SECRET_KEY is not configured")
    secret = secret.strip()
    if len(secret) < _MIN_SECRET_LENGTH:
        raise TokenConfigError("JWT_SECRET_KEY must be at least 32 characters")
    return secret
