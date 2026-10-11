def test_create_incident(client, engineer_headers):
    response = client.post(
        "/incidents/",
        headers=engineer_headers,
        json={
            "title": "Test API Outage",
            "description": "Test users are receiving errors.",
            "severity": "critical",
            "service": "test-api",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Test API Outage"
    assert body["description"] == "Test users are receiving errors."
    assert body["severity"] == "critical"
    assert body["service"] == "test-api"
    assert body["status"] == "open"
    assert isinstance(body["id"], int)
    assert body["created_at"]
    assert body["updated_at"]


def test_list_incidents(client, engineer_headers, viewer_headers):
    first = {
        "title": "Checkout timeouts",
        "description": "Customers cannot complete checkout.",
        "severity": "high",
        "service": "payments-api",
    }
    second = {
        "title": "Login failures",
        "description": "Users cannot sign in.",
        "severity": "medium",
        "service": "auth-service",
    }
    client.post("/incidents/", headers=engineer_headers, json=first)
    client.post("/incidents/", headers=engineer_headers, json=second)

    response = client.get("/incidents/", headers=viewer_headers)

    assert response.status_code == 200
    incidents = response.json()
    assert len(incidents) == 2
    assert {incident["title"] for incident in incidents} == {
        "Checkout timeouts",
        "Login failures",
    }


def test_get_incident(client, engineer_headers, viewer_headers):
    created = client.post(
        "/incidents/",
        headers=engineer_headers,
        json={
            "title": "Search degradation",
            "description": "Search results are timing out.",
            "severity": "high",
            "service": "search-api",
        },
    ).json()

    response = client.get(f"/incidents/{created['id']}", headers=viewer_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["title"] == "Search degradation"
    assert body["service"] == "search-api"


def test_get_missing_incident_returns_404(client, viewer_headers):
    response = client.get("/incidents/999999", headers=viewer_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"


def test_update_incident_status(client, engineer_headers):
    created = client.post(
        "/incidents/",
        headers=engineer_headers,
        json={
            "title": "Queue backup",
            "description": "Background jobs are delayed.",
            "severity": "medium",
            "service": "worker",
        },
    ).json()

    response = client.patch(
        f"/incidents/{created['id']}",
        headers=engineer_headers,
        json={"status": "investigating"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "investigating"
    assert body["id"] == created["id"]
    assert body["title"] == "Queue backup"


def test_missing_token_returns_401(client):
    response = client.get("/incidents/")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_viewer_cannot_create_incident(client, viewer_headers):
    response = client.post(
        "/incidents/",
        headers=viewer_headers,
        json={
            "title": "Viewer incident",
            "description": "A viewer should not be able to create this.",
            "severity": "low",
            "service": "test-api",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Engineer access required"


def test_engineer_can_create_incident(client, engineer_headers):
    response = client.post(
        "/incidents/",
        headers=engineer_headers,
        json={
            "title": "Engineer incident",
            "description": "An engineer can create this.",
            "severity": "low",
            "service": "test-api",
        },
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Engineer incident"


def test_viewer_can_read_incidents(client, viewer_headers):
    response = client.get("/incidents/", headers=viewer_headers)

    assert response.status_code == 200
    assert response.json() == []
