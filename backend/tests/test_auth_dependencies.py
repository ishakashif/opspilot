from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import Depends

from app.dependencies.auth import get_current_user, require_engineer
from app.main import app
from app.models.user import User
from tests.conftest import TestSessionLocal

TEST_JWT_SECRET = "a" * 32
CURRENT_USER_PATH = "/test-only/current-user"
ENGINEER_PATH = "/test-only/engineer"


@pytest.fixture
def protected_routes():
    @app.get(CURRENT_USER_PATH)
    def read_current_user(user: User = Depends(get_current_user)):
        return {"id": user.id, "role": user.role}

    @app.get(ENGINEER_PATH)
    def read_engineer(user: User = Depends(require_engineer)):
        return {"id": user.id, "role": user.role}

    yield

    app.router.routes[:] = [
        route
        for route in app.router.routes
        if getattr(route, "path", None) not in {CURRENT_USER_PATH, ENGINEER_PATH}
    ]


def register_and_login(client, email):
    registered = client.post(
        "/auth/register",
        json={"email": email, "password": "correct-horse"},
    )
    assert registered.status_code == 201
    token = client.post(
        "/auth/login",
        json={"email": email, "password": "correct-horse"},
    )
    assert token.status_code == 200
    return registered.json(), token.json()["access_token"]


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_missing_bearer_token_returns_401(client, protected_routes):
    response = client.get(CURRENT_USER_PATH)

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
    assert response.headers["www-authenticate"] == "Bearer"


def test_invalid_bearer_token_returns_401(client, monkeypatch, protected_routes):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)

    response = client.get(
        CURRENT_USER_PATH,
        headers=bearer("not-a-valid-token"),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"
    assert response.headers["www-authenticate"] == "Bearer"


def test_expired_bearer_token_returns_401(client, monkeypatch, protected_routes):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)
    registered, _token = register_and_login(client, "expired.token@example.com")
    issued_at = datetime.now(timezone.utc) - timedelta(hours=2)
    expired_token = jwt.encode(
        {
            "sub": str(registered["id"]),
            "iat": issued_at,
            "exp": issued_at + timedelta(minutes=30),
        },
        TEST_JWT_SECRET,
        algorithm="HS256",
    )

    response = client.get(CURRENT_USER_PATH, headers=bearer(expired_token))

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"
    assert response.headers["www-authenticate"] == "Bearer"


def test_valid_token_returns_200(client, monkeypatch, protected_routes):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)
    registered, token = register_and_login(client, "valid.token@example.com")

    response = client.get(CURRENT_USER_PATH, headers=bearer(token))

    assert response.status_code == 200
    assert response.json() == {"id": registered["id"], "role": "viewer"}


def test_deleted_user_token_returns_401(client, monkeypatch, protected_routes):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)
    registered, token = register_and_login(client, "deleted.user@example.com")
    db = TestSessionLocal()
    try:
        user = db.query(User).filter(User.id == registered["id"]).one()
        db.delete(user)
        db.commit()
    finally:
        db.close()

    response = client.get(CURRENT_USER_PATH, headers=bearer(token))

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"
    assert response.headers["www-authenticate"] == "Bearer"


def test_viewer_cannot_access_engineer_route(client, monkeypatch, protected_routes):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)
    _registered, token = register_and_login(client, "viewer.user@example.com")

    response = client.get(ENGINEER_PATH, headers=bearer(token))

    assert response.status_code == 403
    assert response.json()["detail"] == "Engineer access required"


def test_engineer_can_access_engineer_route(client, monkeypatch, protected_routes):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)
    registered, token = register_and_login(client, "engineer.user@example.com")
    db = TestSessionLocal()
    try:
        user = db.query(User).filter(User.id == registered["id"]).one()
        user.role = "engineer"
        db.commit()
    finally:
        db.close()

    response = client.get(ENGINEER_PATH, headers=bearer(token))

    assert response.status_code == 200
    assert response.json() == {"id": registered["id"], "role": "engineer"}
