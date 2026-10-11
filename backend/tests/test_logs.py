def test_add_log_to_incident(client, engineer_headers):
    incident = client.post(
        "/incidents/",
        headers=engineer_headers,
        json={
            "title": "Test API Outage",
            "description": "Test users are receiving errors.",
            "severity": "critical",
            "service": "test-api",
        },
    ).json()

    response = client.post(
        f"/incidents/{incident['id']}/logs/",
        headers=engineer_headers,
        json={
            "level": "ERROR",
            "message": "Database connection timed out.",
            "source": "test-api",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["incident_id"] == incident["id"]
    assert body["level"] == "ERROR"
    assert body["message"] == "Database connection timed out."
    assert body["source"] == "test-api"
    assert isinstance(body["id"], int)
    assert body["timestamp"]


def test_get_incident_logs(client, engineer_headers, viewer_headers):
    incident = client.post(
        "/incidents/",
        headers=engineer_headers,
        json={
            "title": "Checkout timeouts",
            "description": "Customers cannot complete checkout.",
            "severity": "high",
            "service": "payments-api",
        },
    ).json()

    client.post(
        f"/incidents/{incident['id']}/logs/",
        headers=engineer_headers,
        json={
            "level": "ERROR",
            "message": "Provider timeout while charging the card.",
            "source": "payments-api",
        },
    )
    client.post(
        f"/incidents/{incident['id']}/logs/",
        headers=engineer_headers,
        json={
            "level": "WARN",
            "message": "Retry queue is backing up.",
            "source": "payments-worker",
        },
    )

    response = client.get(
        f"/incidents/{incident['id']}/logs/",
        headers=viewer_headers,
    )

    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 2
    assert {log["message"] for log in logs} == {
        "Provider timeout while charging the card.",
        "Retry queue is backing up.",
    }
    assert all(log["incident_id"] == incident["id"] for log in logs)


def test_bulk_add_logs(client, engineer_headers):
    incident = client.post(
        "/incidents/",
        headers=engineer_headers,
        json={
            "title": "Search degradation",
            "description": "Search results are timing out.",
            "severity": "high",
            "service": "search-api",
        },
    ).json()
    submitted = [
        {
            "level": "INFO",
            "message": "Search latency crossed the warning threshold.",
            "source": "search-api",
        },
        {
            "level": "WARN",
            "message": "Query cache miss rate increased.",
            "source": "search-cache",
        },
        {
            "level": "ERROR",
            "message": "Search index request timed out.",
            "source": "search-index",
        },
    ]

    response = client.post(
        f"/incidents/{incident['id']}/logs/bulk",
        headers=engineer_headers,
        json={"logs": submitted},
    )

    assert response.status_code == 201
    logs = response.json()
    assert len(logs) == 3
    assert all(log["incident_id"] == incident["id"] for log in logs)
    assert [log["message"] for log in logs] == [
        "Search latency crossed the warning threshold.",
        "Query cache miss rate increased.",
        "Search index request timed out.",
    ]


def test_add_log_to_missing_incident_returns_404(client, engineer_headers):
    response = client.post(
        "/incidents/999999/logs/",
        headers=engineer_headers,
        json={
            "level": "ERROR",
            "message": "Database connection timed out.",
            "source": "test-api",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"


def test_get_logs_for_missing_incident_returns_404(client, viewer_headers):
    response = client.get("/incidents/999999/logs/", headers=viewer_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"


def test_logs_are_isolated_between_incidents(
    client,
    engineer_headers,
    viewer_headers,
):
    first = client.post(
        "/incidents/",
        headers=engineer_headers,
        json={
            "title": "Checkout timeouts",
            "description": "Customers cannot complete checkout.",
            "severity": "high",
            "service": "payments-api",
        },
    ).json()
    second = client.post(
        "/incidents/",
        headers=engineer_headers,
        json={
            "title": "Login failures",
            "description": "Users cannot sign in.",
            "severity": "medium",
            "service": "auth-service",
        },
    ).json()

    client.post(
        f"/incidents/{first['id']}/logs/",
        headers=engineer_headers,
        json={
            "level": "ERROR",
            "message": "Checkout provider timed out.",
            "source": "payments-api",
        },
    )
    client.post(
        f"/incidents/{second['id']}/logs/",
        headers=engineer_headers,
        json={
            "level": "ERROR",
            "message": "Login token verification failed.",
            "source": "auth-service",
        },
    )

    first_logs = client.get(
        f"/incidents/{first['id']}/logs/",
        headers=viewer_headers,
    )
    assert first_logs.status_code == 200
    first_body = first_logs.json()
    assert len(first_body) == 1
    assert first_body[0]["message"] == "Checkout provider timed out."
    assert first_body[0]["incident_id"] == first["id"]

    second_logs = client.get(
        f"/incidents/{second['id']}/logs/",
        headers=viewer_headers,
    )
    assert second_logs.status_code == 200
    second_body = second_logs.json()
    assert len(second_body) == 1
    assert second_body[0]["message"] == "Login token verification failed."
    assert second_body[0]["incident_id"] == second["id"]
