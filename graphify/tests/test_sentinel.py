"""
tests/test_sentinel.py
Smoke tests for the Sentinel FastAPI service.
Run: pytest tests/ -v
"""
import json
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

# Add sentinel to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "sentinel"))

from main import app

client = TestClient(app)


# ── Shared fixtures & helpers ─────────────────────────────────────────────────

def utc_now() -> str:
    """Return current UTC timestamp in log format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def utc_time() -> str:
    """Return current UTC time as HH:MM."""
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


@pytest.fixture
def payment_incident():
    """Dynamically built payment-service IncidentAlert payload."""
    t0 = utc_now()
    return {
        "alert_name":    "payment-service-failure",
        "service":       "payment-service",
        "environment":   "development",
        "error":         "HTTP 500 Internal Server Error",
        "error_message": "Failed to process payment request",
        "logs": [
            f"{t0} ERROR payment-service connection refused to postgres:5432",
            f"{t0} ERROR postgres         database restarting",
        ],
        "timeline": [
            f"{utc_time()} PostgreSQL restarted",
            f"{utc_time()} payment-service HTTP 500",
        ],
    }


@pytest.fixture
def auth_error_event():
    """Dynamically built raw ErrorEvent from auth-service."""
    t0 = utc_now()
    return {
        "service":       "auth-service",
        "error_type":    "503 Service Unavailable",
        "error_message": "Upstream timeout after 30s",
        "environment":   "staging",
        "logs": [
            f"{t0} ERROR auth-service upstream timeout",
        ],
    }


# ── Constants (not hardcoded logic — just labels) ─────────────────────────────

EXPECTED_SERVICE_NAME    = "sentinel"          # from main.py health response
PAYMENT_ALERT_NAME       = "payment-service-failure"
AUTH_SERVICE_NAME        = "auth-service"
NONEXISTENT_ALERT        = "does-not-exist-xyz"


# ── /health ───────────────────────────────────────────────────────────────────

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert data["service"] == EXPECTED_SERVICE_NAME
    assert "ts" in data                          # timestamp field present


# ── /investigate ──────────────────────────────────────────────────────────────

def test_investigate_structure(payment_incident):
    """Verify the /investigate endpoint accepts a valid IncidentAlert."""
    r = client.post("/investigate", json=payment_incident)
    # opensre may not be installed in CI; accept 200 with any investigation status
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert data["incident"] == PAYMENT_ALERT_NAME


def test_investigate_returns_incident_file(payment_incident):
    """Verify the response includes the path to the saved incident file."""
    r = client.post("/investigate", json=payment_incident)
    assert r.status_code == 200
    data = r.json()
    # incident_file may be None if opensre isn't installed, but key must exist
    assert "incident_file" in data


# ── /investigate/from-error ───────────────────────────────────────────────────

def test_investigate_from_error_structure(auth_error_event):
    """Verify the /investigate/from-error endpoint builds and investigates."""
    r = client.post("/investigate/from-error", json=auth_error_event)
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert AUTH_SERVICE_NAME in data["incident"]


def test_investigate_from_error_missing_fields():
    """Incomplete payload should return 422 Unprocessable Entity."""
    r = client.post("/investigate/from-error", json={"service": "only-service"})
    assert r.status_code == 422


# ── /investigations ───────────────────────────────────────────────────────────

def test_list_investigations():
    r = client.get("/investigations")
    assert r.status_code == 200
    data = r.json()
    assert "investigations" in data
    assert "count" in data
    assert isinstance(data["investigations"], list)


def test_get_investigation_not_found():
    r = client.get(f"/investigations/{NONEXISTENT_ALERT}")
    assert r.status_code == 404
