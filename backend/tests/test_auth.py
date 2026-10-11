from app.services.tokens import TokenConfigError, decode_access_token

TEST_JWT_SECRET = "a" * 32


def test_register_user_success(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "new.viewer@example.com",
            "password": "correct-horse",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new.viewer@example.com"
    assert body["role"] == "viewer"
    assert isinstance(body["id"], int)
    assert body["created_at"]
    assert "password_hash" not in body
    assert "password" not in body


def test_register_duplicate_email(client):
    payload = {
        "email": "duplicate.viewer@example.com",
        "password": "correct-horse",
    }
    client.post("/auth/register", json=payload)

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


def test_register_email_normalization(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "Ops.User@Example.com",
            "password": "correct-horse",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "ops.user@example.com"

    duplicate = client.post(
        "/auth/register",
        json={
            "email": "ops.user@example.com",
            "password": "another-secret",
        },
    )

    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Email already registered"


def test_register_short_password(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "short.password@example.com",
            "password": "too-short",
        },
    )

    assert response.status_code == 422

    created = client.post(
        "/auth/register",
        json={
            "email": "short.password@example.com",
            "password": "correct-horse",
        },
    )

    assert created.status_code == 201


def test_register_cannot_choose_engineer_role(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "role.choice@example.com",
            "password": "correct-horse",
            "role": "engineer",
        },
    )

    assert response.status_code == 201
    assert response.json()["role"] == "viewer"


def test_login_success(client, monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)
    registered = client.post(
        "/auth/register",
        json={
            "email": "login.success@example.com",
            "password": "correct-horse",
        },
    ).json()

    response = client.post(
        "/auth/login",
        json={
            "email": "login.success@example.com",
            "password": "correct-horse",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]
    assert decode_access_token(body["access_token"]) == registered["id"]


def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        json={
            "email": "wrong.password@example.com",
            "password": "correct-horse",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "wrong.password@example.com",
            "password": "incorrect-horse",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_nonexistent_user(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "missing.user@example.com",
            "password": "correct-horse",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_email_normalization(client, monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)
    client.post(
        "/auth/register",
        json={
            "email": "normalized.login@example.com",
            "password": "correct-horse",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "Normalized.Login@Example.com",
            "password": "correct-horse",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]


def test_login_missing_jwt_configuration(client, monkeypatch):
    client.post(
        "/auth/register",
        json={
            "email": "missing.config@example.com",
            "password": "correct-horse",
        },
    )

    def fail_create_access_token(user_id):
        raise TokenConfigError("JWT configuration is unavailable")

    monkeypatch.setattr(
        "app.routes.auth.create_access_token",
        fail_create_access_token,
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "missing.config@example.com",
            "password": "correct-horse",
        },
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Authentication service unavailable"


def test_me_missing_token_returns_401(client):
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_me_viewer(client, viewer_headers):
    response = client.get("/auth/me", headers=viewer_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "viewer@example.com"
    assert body["role"] == "viewer"
    assert isinstance(body["id"], int)
    assert body["created_at"]
    assert "password_hash" not in body
    assert "password" not in body


def test_me_engineer(client, engineer_headers):
    response = client.get("/auth/me", headers=engineer_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "engineer@example.com"
    assert body["role"] == "engineer"
    assert isinstance(body["id"], int)
    assert body["created_at"]
    assert "password_hash" not in body
    assert "password" not in body


def test_me_response_excludes_password_hash(client, viewer_headers):
    response = client.get("/auth/me", headers=viewer_headers)

    assert response.status_code == 200
    assert "password_hash" not in response.json()
