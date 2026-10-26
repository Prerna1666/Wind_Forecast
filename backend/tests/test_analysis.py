"""
Tests for analysis.py: decision_forecasts, metrics, build_errors, and related functions.

Uses small hand-made inputs to verify core logic independently of the Elexon API.
"""
import math
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.analysis import (
    cutoff_for, decision_forecasts, build_errors, metrics,
    percentile, error_by_horizon, CUTOFF_HOUR, LONDON,
)

UTC = timezone.utc


def _utc(year, month, day, hour=0, minute=0):
    """Shortcut to create a UTC datetime."""
    return datetime(year, month, day, hour, minute, tzinfo=UTC)


# --- cutoff_for ---

def test_cutoff_for_jan_2():
    """For a delivery at 2026-01-02 14:00 UTC, cutoff should be 2026-01-01 09:00 London (= 09:00 UTC in January)."""
    start = _utc(2026, 1, 2, 14, 0)
    cutoff = cutoff_for(start)
    # January: London = UTC, so cutoff is 2026-01-01 09:00 UTC
    assert cutoff.hour == CUTOFF_HOUR
    assert cutoff.astimezone(UTC).date() == datetime(2026, 1, 1).date()


def test_cutoff_for_jan_1():
    """Delivery on Jan 1 means decision on Dec 31 at 09:00 London."""
    start = _utc(2026, 1, 1, 0, 0)
    cutoff = cutoff_for(start)
    assert cutoff.astimezone(UTC).date() == datetime(2025, 12, 31).date()
    assert cutoff.hour == CUTOFF_HOUR


# --- decision_forecasts ---

def test_decision_forecasts_picks_latest_before_cutoff():
    """Given two forecasts for the same target, only the later one (before cutoff) is kept."""
    # Target: 2026-01-02 12:00 UTC => delivery date Jan 2 => cutoff = Jan 1 09:00 UTC
    target = "2026-01-02T12:00:00Z"
    rows = [
        {"startTime": target, "publishTime": "2026-01-01T02:00:00Z", "generation": 1000},
        {"startTime": target, "publishTime": "2026-01-01T08:00:00Z", "generation": 1200},  # later, still before cutoff
        {"startTime": target, "publishTime": "2026-01-01T10:00:00Z", "generation": 1500},  # after cutoff, excluded
    ]
    best = decision_forecasts(rows)
    target_dt = _utc(2026, 1, 2, 12, 0)
    assert target_dt in best
    assert best[target_dt]["forecast"] == 1200
    assert best[target_dt]["pub"] == _utc(2026, 1, 1, 8, 0)


def test_decision_forecasts_excludes_all_after_cutoff():
    """If all forecasts are after the cutoff, no forecast is selected."""
    target = "2026-01-02T12:00:00Z"
    rows = [
        {"startTime": target, "publishTime": "2026-01-01T10:00:00Z", "generation": 1000},
        {"startTime": target, "publishTime": "2026-01-01T12:00:00Z", "generation": 1200},
    ]
    best = decision_forecasts(rows)
    assert len(best) == 0


def test_decision_forecasts_multiple_targets():
    """Different target times each get their own best forecast."""
    rows = [
        {"startTime": "2026-01-02T10:00:00Z", "publishTime": "2026-01-01T06:00:00Z", "generation": 500},
        {"startTime": "2026-01-02T14:00:00Z", "publishTime": "2026-01-01T08:00:00Z", "generation": 700},
    ]
    best = decision_forecasts(rows)
    assert len(best) == 2


# --- build_errors ---

def test_build_errors_inner_join():
    """build_errors only includes targets present in both forecasts and actuals."""
    best = {
        _utc(2026, 1, 2, 10): {"pub": _utc(2026, 1, 1, 6), "forecast": 500},
        _utc(2026, 1, 2, 14): {"pub": _utc(2026, 1, 1, 8), "forecast": 700},
    }
    actuals = {
        _utc(2026, 1, 2, 10): 480.0,
        # 14:00 missing from actuals
    }
    errors = build_errors(best, actuals)
    assert len(errors) == 1
    assert errors[0]["forecast"] == 500
    assert errors[0]["actual"] == 480.0
    assert errors[0]["error"] == 20.0  # 500 - 480


def test_build_errors_sign_convention():
    """error = forecast - actual: over-forecast is positive."""
    best = {_utc(2026, 1, 5, 12): {"pub": _utc(2026, 1, 4, 8), "forecast": 3000}}
    actuals = {_utc(2026, 1, 5, 12): 3500.0}
    errors = build_errors(best, actuals)
    assert errors[0]["error"] == -500.0  # under-forecast


def test_build_errors_horizon():
    """Horizon = (startTime - publishTime) in hours."""
    best = {_utc(2026, 1, 5, 12): {"pub": _utc(2026, 1, 4, 6), "forecast": 3000}}
    actuals = {_utc(2026, 1, 5, 12): 3000.0}
    errors = build_errors(best, actuals)
    assert errors[0]["horizon_h"] == 30.0  # 12:00 Jan 5 - 06:00 Jan 4 = 30 hours


# --- metrics ---

def test_metrics_empty():
    """Empty input returns n=0."""
    assert metrics([])["n"] == 0


def test_metrics_known_values():
    """Check MAE, RMSE, bias with known hand-calculated values."""
    rows = [
        {"error": 10, "actual": 100},
        {"error": -20, "actual": 200},
        {"error": 30, "actual": 300},
    ]
    m = metrics(rows)
    assert m["n"] == 3
    # MAE = (10 + 20 + 30) / 3 = 20.0
    assert m["mae"] == 20.0
    # bias = (10 - 20 + 30) / 3 = 20/3 ≈ 6.7
    assert abs(m["bias"] - 6.7) < 0.1
    # RMSE = sqrt((100 + 400 + 900) / 3) = sqrt(1400/3) ≈ 21.6
    expected_rmse = math.sqrt((100 + 400 + 900) / 3)
    assert abs(m["rmse"] - expected_rmse) < 0.1
    # NMAE = 100 * 60 / 600 = 10.0%
    assert m["nmae_pct"] == 10.0


def test_metrics_all_zero_error():
    """Perfect forecast: all metrics should be 0."""
    rows = [
        {"error": 0, "actual": 1000},
        {"error": 0, "actual": 2000},
    ]
    m = metrics(rows)
    assert m["mae"] == 0.0
    assert m["rmse"] == 0.0
    assert m["bias"] == 0.0


# --- percentile ---

def test_percentile_basic():
    vals = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert percentile(vals, 0.5) == 6  # 50th percentile
    assert percentile(vals, 0.9) == 10  # 90th percentile


def test_percentile_single():
    assert percentile([42], 0.9) == 42


# --- error_by_horizon ---

def test_error_by_horizon_buckets():
    """Records with horizons 20h and 25h should fall in the same 6h bucket (18-24)."""
    rows = [
        {"error": 100, "horizon_h": 20.0},
        {"error": -200, "horizon_h": 25.0},
        {"error": 50, "horizon_h": 32.0},
    ]
    # Add abs error values the function needs
    result = error_by_horizon(rows, bin_h=6)
    # 20h -> bucket 18, 25h -> bucket 24, 32h -> bucket 30
    buckets = {r["horizon_h"]: r for r in result}
    assert 18 in buckets
    assert 24 in buckets
    assert 30 in buckets
    assert buckets[18]["mae"] == 100.0
    assert buckets[24]["mae"] == 200.0
    assert buckets[30]["mae"] == 50.0
