from app.services.similar_incidents import (
    SimilarIncidentsConfigError,
    SimilarIncidentsError,
)


def test_find_similar_incidents_success(client, monkeypatch, engineer_headers):
    current = client.post(
        "/incidents/",
        headers=engineer_headers,
        json={
            "title": "Payment API pool exhaustion",
            "description": "Payments fail after database timeouts.",
            "severity": "critical",
            "service": "payment-api",
        },
    ).json()
    checkout = client.post(
        "/incidents/",
        headers=engineer_headers,
        json={
            "title": "Checkout timeouts",
            "description": "Checkout waits on the database.",
            "severity": "high",
            "service": "checkout-api",
        },
    ).json()
    portal = client.post(
        "/incidents/",
        headers=engineer_headers,
        json={
            "title": "Portal database errors",
            "description": "The portal returns HTTP 500.",
            "severity": "critical",
            "service": "citizen-portal",
        },
    ).json()

    client.post(
        f"/incidents/{current['id']}/logs/",
        headers=engineer_headers,
        json={
            "level": "ERROR",
            "message": "Payment connection timed out.",
            "source": "payment-api",
        },
    )
    client.post(
        f"/incidents/{current['id']}/logs/",
        headers=engineer_headers,
        json={
            "level": "WARN",
            "message": "Payment pool is nearly exhausted.",
            "source": "database-pool",
        },
    )
    client.post(
        f"/incidents/{checkout['id']}/logs/",
        headers=engineer_headers,
        json={
            "level": "ERROR",
            "message": "Checkout connection timed out.",
            "source": "checkout-api",
        },
    )
    client.post(
        f"/incidents/{portal['id']}/logs/",
        headers=engineer_headers,
        json={
            "level": "ERROR",
            "message": "Portal connection timed out.",
            "source": "citizen-portal",
        },
    )

    def fake_find_similar_incidents(incident, logs, candidates):
        assert incident.id == current["id"]
        assert incident.title == "Payment API pool exhaustion"
        assert [log.message for log in logs] == [
            "Payment connection timed out.",
            "Payment pool is nearly exhausted.",
        ]
        assert all(log.incident_id == current["id"] for log in logs)

        candidates_by_id = {
            candidate.id: candidate_logs for candidate, candidate_logs in candidates
        }
        assert current["id"] not in candidates_by_id
        assert set(candidates_by_id) == {checkout["id"], portal["id"]}
        assert [log.message for log in candidates_by_id[checkout["id"]]] == [
            "Checkout connection timed out.",
        ]
        assert [log.message for log in candidates_by_id[portal["id"]]] == [
            "Portal connection timed out.",
        ]
        return {
            "incidents": [
                {
                    "incident_id": portal["id"],
                    "title": portal["title"],
                    "service": portal["service"],
                    "severity": portal["severity"],
                    "status": "open",
                    "similarity": "high",
                    "reason": "The portal also fails after database timeouts.",
                    "relevant_pattern": "Database connection timeout followed by HTTP 500.",
                },
                {
                    "incident_id": checkout["id"],
                    "title": checkout["title"],
                    "service": checkout["service"],
                    "severity": checkout["severity"],
                    "status": "open",
                    "similarity": "medium",
                    "reason": "Checkout waits on the same database.",
                    "relevant_pattern": "Request timeout while waiting for a database connection.",
                },
            ]
        }

    monkeypatch.setattr(
        "app.routes.similar_incidents.find_similar_incidents",
        fake_find_similar_incidents,
    )

    response = client.get(
        f"/incidents/{current['id']}/similar",
        headers=engineer_headers,
    )

    assert response.status_code == 200
    assert response.json() == {
        "incidents": [
            {
                "incident_id": portal["id"],
                "title": "Portal database errors",
                "service": "citizen-portal",
                "severity": "critical",
                "status": "open",
                "similarity": "high",
                "reason": "The portal also fails after database timeouts.",
                "relevant_pattern": "Database connection timeout followed by HTTP 500.",
            },
            {
                "incident_id": checkout["id"],
                "title": "Checkout timeouts",
                "service": "checkout-api",
                "severity": "high",
                "status": "open",
                "similarity": "medium",
                "reason": "Checkout waits on the same database.",
                "relevant_pattern": "Request timeout while waiting for a database connection.",
            },
        ]
    }


def test_similar_missing_incident_returns_404(client, monkeypatch, engineer_headers):
    def fake_find_similar_incidents(incident, logs, candidates):
        raise AssertionError("find_similar_incidents should not be called")

    monkeypatch.setattr(
        "app.routes.similar_incidents.find_similar_incidents",
        fake_find_similar_incidents,
    )

    response = client.get(
        "/incidents/999999/similar",
        headers=engineer_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"


def test_no_historical_incidents_returns_empty(client, monkeypatch, engineer_headers):
    incident = client.post(
        "/incidents/",
        headers=engineer_headers,
        json={
            "title": "Only incident",
            "description": "Nothing historical exists yet.",
            "severity": "low",
            "service": "test-api",
        },
    ).json()

    def fake_find_similar_incidents(incident, logs, candidates):
        raise AssertionError("find_similar_incidents should not be called")

    monkeypatch.setattr(
        "app.routes.similar_incidents.find_similar_incidents",
        fake_find_similar_incidents,
    )

    response = client.get(
        f"/incidents/{incident['id']}/similar",
        headers=engineer_headers,
    )

    assert response.status_code == 200
    assert response.json() == {"incidents": []}


def test_similar_incidents_without_logs(client, monkeypatch, engineer_headers):
    current = client.post(
        "/incidents/",
        headers=engineer_headers,
        json={
            "title": "Current incident",
            "description": "No logs were recorded.",
            "severity": "medium",
            "service": "test-api",
        },
    ).json()
    historical = client.post(
        "/incidents/",
        headers=engineer_headers,
        json={
            "title": "Historical incident",
            "description": "This incident also has no logs.",
            "severity": "medium",
            "service": "history-api",
        },
    ).json()

    def fake_find_similar_incidents(incident, logs, candidates):
        assert incident.id == current["id"]
        assert logs == []
        assert len(candidates) == 1
        candidate, candidate_logs = candidates[0]
        assert candidate.id == historical["id"]
        assert candidate_logs == []
        return {
            "incidents": [
                {
                    "incident_id": historical["id"],
                    "title": historical["title"],
                    "service": historical["service"],
                    "severity": historical["severity"],
                    "status": "open",
                    "similarity": "low",
                    "reason": "Both incidents describe the same service failure.",
                    "relevant_pattern": "Repeated service errors without log evidence.",
                }
            ]
        }

    monkeypatch.setattr(
        "app.routes.similar_incidents.find_similar_incidents",
        fake_find_similar_incidents,
    )

    response = client.get(
        f"/incidents/{current['id']}/similar",
        headers=engineer_headers,
    )

    assert response.status_code == 200
    assert response.json()["incidents"][0]["incident_id"] == historical["id"]
    assert response.json()["incidents"][0]["similarity"] == "low"


def test_similar_service_failure_returns_502(client, monkeypatch, engineer_headers):
    current = client.post(
        "/incidents/",
        headers=engineer_headers,
        json={
            "title": "Current incident",
            "description": "Comparison should fail.",
            "severity": "high",
            "service": "test-api",
        },
    ).json()
    client.post(
        "/incidents/",
        headers=engineer_headers,
        json={
            "title": "Historical incident",
            "description": "A candidate exists.",
            "severity": "high",
            "service": "history-api",
        },
    )

    def fake_find_similar_incidents(incident, logs, candidates):
        raise SimilarIncidentsError("Similar incidents service failed")

    monkeypatch.setattr(
        "app.routes.similar_incidents.find_similar_incidents",
        fake_find_similar_incidents,
    )

    response = client.get(
        f"/incidents/{current['id']}/similar",
        headers=engineer_headers,
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "Similar incidents service failed"


def test_similar_missing_api_key_returns_500(client, monkeypatch, engineer_headers):
    current = client.post(
        "/incidents/",
        headers=engineer_headers,
        json={
            "title": "Current incident",
            "description": "The comparison service is not configured.",
            "severity": "medium",
            "service": "test-api",
        },
    ).json()
    client.post(
        "/incidents/",
        headers=engineer_headers,
        json={
            "title": "Historical incident",
            "description": "A candidate exists.",
            "severity": "medium",
            "service": "history-api",
        },
    )

    def fake_find_similar_incidents(incident, logs, candidates):
        raise SimilarIncidentsConfigError("ANTHROPIC_API_KEY is not configured")

    monkeypatch.setattr(
        "app.routes.similar_incidents.find_similar_incidents",
        fake_find_similar_incidents,
    )

    response = client.get(
        f"/incidents/{current['id']}/similar",
        headers=engineer_headers,
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "ANTHROPIC_API_KEY is not configured"


def test_candidate_limit_is_20(client, monkeypatch, engineer_headers):
    current = client.post(
        "/incidents/",
        headers=engineer_headers,
        json={
            "title": "Current incident",
            "description": "This incident is being compared.",
            "severity": "critical",
            "service": "test-api",
        },
    ).json()
    historical = []
    for index in range(25):
        historical.append(
            client.post(
                "/incidents/",
                headers=engineer_headers,
                json={
                    "title": f"Historical incident {index}",
                    "description": "A historical candidate.",
                    "severity": "low",
                    "service": "history-api",
                },
            ).json()
        )

    newest_ids = [
        incident["id"]
        for incident in sorted(
            historical,
            key=lambda incident: (incident["created_at"], incident["id"]),
            reverse=True,
        )[:20]
    ]

    def fake_find_similar_incidents(incident, logs, candidates):
        candidate_ids = [candidate.id for candidate, _logs in candidates]
        assert incident.id == current["id"]
        assert current["id"] not in candidate_ids
        assert len(candidates) == 20
        assert candidate_ids == newest_ids
        return {"incidents": []}

    monkeypatch.setattr(
        "app.routes.similar_incidents.find_similar_incidents",
        fake_find_similar_incidents,
    )

    response = client.get(
        f"/incidents/{current['id']}/similar",
        headers=engineer_headers,
    )

    assert response.status_code == 200
    assert response.json() == {"incidents": []}
