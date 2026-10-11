from app.services.incident_analysis import (
    IncidentAnalysisConfigError,
    IncidentAnalysisError,
)


def test_analyze_incident_success(client, monkeypatch, engineer_headers):
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
    client.post(
        f"/incidents/{incident['id']}/logs/",
        headers=engineer_headers,
        json={
            "level": "ERROR",
            "message": "Connection timeout",
            "source": "test-api",
        },
    )
    client.post(
        f"/incidents/{incident['id']}/logs/",
        headers=engineer_headers,
        json={
            "level": "WARN",
            "message": "Pool nearly exhausted",
            "source": "database-pool",
        },
    )

    def fake_analyze_incident(received_incident, logs):
        assert received_incident.id == incident["id"]
        assert received_incident.title == "Test API Outage"
        assert len(logs) == 2
        assert {log.message for log in logs} == {
            "Connection timeout",
            "Pool nearly exhausted",
        }
        return {
            "root_cause": "Database connection pool exhaustion",
            "evidence": ["Connection timeout", "Pool nearly exhausted"],
            "recommended_actions": [
                "Inspect pool metrics",
                "Review connection handling",
            ],
            "confidence": "high",
        }

    monkeypatch.setattr(
        "app.routes.analysis.analyze_incident",
        fake_analyze_incident,
    )

    response = client.post(
        f"/incidents/{incident['id']}/analyze",
        headers=engineer_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["root_cause"] == "Database connection pool exhaustion"
    assert body["evidence"] == ["Connection timeout", "Pool nearly exhausted"]
    assert body["recommended_actions"] == [
        "Inspect pool metrics",
        "Review connection handling",
    ]
    assert body["confidence"] == "high"


def test_analyze_missing_incident_returns_404(client, monkeypatch, engineer_headers):
    def fake_analyze_incident(incident, logs):
        raise AssertionError("analyze_incident should not be called")

    monkeypatch.setattr(
        "app.routes.analysis.analyze_incident",
        fake_analyze_incident,
    )

    response = client.post(
        "/incidents/999999/analyze",
        headers=engineer_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"


def test_analyze_incident_without_logs(client, monkeypatch, engineer_headers):
    incident = client.post(
        "/incidents/",
        headers=engineer_headers,
        json={
            "title": "Empty log incident",
            "description": "No logs have been recorded.",
            "severity": "low",
            "service": "test-api",
        },
    ).json()

    def fake_analyze_incident(received_incident, logs):
        assert received_incident.id == incident["id"]
        assert logs == []
        return {
            "root_cause": "Insufficient evidence",
            "evidence": [],
            "recommended_actions": ["Collect logs"],
            "confidence": "low",
        }

    monkeypatch.setattr(
        "app.routes.analysis.analyze_incident",
        fake_analyze_incident,
    )

    response = client.post(
        f"/incidents/{incident['id']}/analyze",
        headers=engineer_headers,
    )

    assert response.status_code == 200
    assert response.json()["root_cause"] == "Insufficient evidence"


def test_analyze_service_failure_returns_502(client, monkeypatch, engineer_headers):
    incident = client.post(
        "/incidents/",
        headers=engineer_headers,
        json={
            "title": "Analysis failure",
            "description": "Claude cannot complete this analysis.",
            "severity": "high",
            "service": "test-api",
        },
    ).json()

    def fake_analyze_incident(received_incident, logs):
        raise IncidentAnalysisError("Incident analysis service failed")

    monkeypatch.setattr(
        "app.routes.analysis.analyze_incident",
        fake_analyze_incident,
    )

    response = client.post(
        f"/incidents/{incident['id']}/analyze",
        headers=engineer_headers,
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "Incident analysis service failed"


def test_analyze_missing_api_key_returns_500(client, monkeypatch, engineer_headers):
    incident = client.post(
        "/incidents/",
        headers=engineer_headers,
        json={
            "title": "Missing configuration",
            "description": "The analysis service is not configured.",
            "severity": "medium",
            "service": "test-api",
        },
    ).json()

    def fake_analyze_incident(received_incident, logs):
        raise IncidentAnalysisConfigError("ANTHROPIC_API_KEY is not configured")

    monkeypatch.setattr(
        "app.routes.analysis.analyze_incident",
        fake_analyze_incident,
    )

    response = client.post(
        f"/incidents/{incident['id']}/analyze",
        headers=engineer_headers,
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "ANTHROPIC_API_KEY is not configured"


def test_viewer_cannot_analyze_incident(client, viewer_headers):
    response = client.post(
        "/incidents/1/analyze",
        headers=viewer_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Engineer access required"
