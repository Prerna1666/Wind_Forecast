"""
Tests for the FastAPI endpoints using TestClient with mocked Elexon data.
"""
from unittest.mock import patch
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app, CACHE

UTC = timezone.utc
client = TestClient(app)


def _make_mock_errors():
    """Create a small set of mock error records for testing endpoints."""
    return [
        {
            "start": datetime(2026, 1, 2, 10, 0, tzinfo=UTC),
            "pub": datetime(2026, 1, 1, 6, 0, tzinfo=UTC),
            "forecast": 5000,
            "actual": 4800.0,
            "error": 200.0,
            "horizon_h": 28.0,
        },
        {
            "start": datetime(2026, 1, 2, 14, 0, tzinfo=UTC),
            "pub": datetime(2026, 1, 1, 8, 0, tzinfo=UTC),
            "forecast": 6000,
            "actual": 6500.0,
            "error": -500.0,
            "horizon_h": 30.0,
        },
        {
            "start": datetime(2026, 1, 3, 12, 0, tzinfo=UTC),
            "pub": datetime(2026, 1, 2, 7, 0, tzinfo=UTC),
            "forecast": 7000,
            "actual": 7100.0,
            "error": -100.0,
            "horizon_h": 29.0,
        },
    ]


def setup_function():
    """Inject mock data before each test."""
    CACHE["errors"] = _make_mock_errors()


def teardown_function():
    """Clear cache after each test."""
    CACHE.clear()


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["cutoff_hour"] == 9


def test_forecast_valid_date():
    resp = client.get("/api/forecast", params={"date": "2026-01-02"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["cutoff_hour"] == 9
    assert len(data["records"]) == 2  # Two records on Jan 2


def test_forecast_invalid_date():
    resp = client.get("/api/forecast", params={"date": "2026-02-15"})
    assert resp.status_code == 400


def test_forecast_no_data_date():
    resp = client.get("/api/forecast", params={"date": "2026-01-15"})
    assert resp.status_code == 404


def test_accuracy_full_range():
    resp = client.get("/api/accuracy", params={"start": "2026-01-01", "end": "2026-01-31"})
    assert resp.status_code == 200
    data = resp.json()
    m = data["metrics"]
    assert m["n"] == 3
    assert "mae" in m
    assert "rmse" in m
    assert "bias" in m
    assert data["error_convention"] == "forecast - actual (positive = over-forecast)"


def test_accuracy_filtered_range():
    resp = client.get("/api/accuracy", params={"start": "2026-01-02", "end": "2026-01-02"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["metrics"]["n"] == 2  # Only Jan 2 records


def test_accuracy_invalid_range():
    resp = client.get("/api/accuracy", params={"start": "2026-01-15", "end": "2026-01-10"})
    assert resp.status_code == 400


def test_errors_endpoint():
    resp = client.get("/api/errors", params={"start": "2026-01-01", "end": "2026-01-31"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["n"] == 3
    assert len(data["records"]) == 3
