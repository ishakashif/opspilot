import os

# Set this before importing the app so pytest cannot open the development database.
os.environ["DATABASE_URL"] = "postgresql+psycopg://localhost/opspilot_test"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base, get_db
from app.main import app
from app.models.incident import Incident
from app.models.log import Log
from app.models.user import User
from app.services.password import hash_password


_MODELS = (Incident, Log, User)

TEST_DATABASE_URL = "postgresql+psycopg://localhost/opspilot_test"
TEST_JWT_SECRET = "a" * 32
TEST_PASSWORD = "correct-horse"

test_engine = create_engine(TEST_DATABASE_URL)

TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


def _get_test_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True, scope="session")
def override_get_db():
    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(setup_database):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def test_jwt_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)


@pytest.fixture
def viewer_user(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "viewer@example.com",
            "password": TEST_PASSWORD,
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def engineer_user(setup_database):
    db = TestSessionLocal()
    try:
        user = User(
            email="engineer@example.com",
            password_hash=hash_password(TEST_PASSWORD),
            role="engineer",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"id": user.id, "email": user.email, "role": user.role}
    finally:
        db.close()


def _login_headers(client, email):
    response = client.post(
        "/auth/login",
        json={"email": email, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewer_headers(client, viewer_user, test_jwt_secret):
    return _login_headers(client, viewer_user["email"])


@pytest.fixture
def engineer_headers(client, engineer_user, test_jwt_secret):
    return _login_headers(client, engineer_user["email"])
