from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.services.tokens import (
    TokenConfigError,
    create_access_token,
    decode_access_token,
)

TEST_JWT_SECRET = "a" * 32
OTHER_JWT_SECRET = "b" * 32


def test_create_and_decode_access_token(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)

    token = create_access_token(42)

    assert decode_access_token(token) == 42


def test_invalid_token_returns_none(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)

    assert decode_access_token("not-a-valid-token") is None


def test_token_signed_with_wrong_secret_is_rejected(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)
    token = create_access_token(42)

    monkeypatch.setenv("JWT_SECRET_KEY", OTHER_JWT_SECRET)

    assert decode_access_token(token) is None


def test_expired_token_returns_none(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)
    issued_at = datetime.now(timezone.utc) - timedelta(hours=1)
    token = jwt.encode(
        {
            "sub": "42",
            "iat": issued_at,
            "exp": issued_at + timedelta(minutes=30),
        },
        TEST_JWT_SECRET,
        algorithm="HS256",
    )

    assert decode_access_token(token) is None


def test_missing_secret_raises_configuration_error(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.setattr("app.services.tokens.load_dotenv", lambda *args, **kwargs: None)

    with pytest.raises(TokenConfigError):
        create_access_token(42)


def test_short_secret_raises_configuration_error(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "too-short")

    with pytest.raises(TokenConfigError):
        create_access_token(42)
