"""
FastAPI backend for Wind Forecast Decision & Accuracy app.

Endpoints:
  GET /api/health        — health check
  GET /api/forecast      — forecast vs actual for a single date
  GET /api/accuracy      — accuracy metrics over a date range
  GET /api/errors        — raw error data for charting
"""
import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .elexon import fetch_actuals, fetch_forecasts
from .analysis import (
    decision_forecasts, build_errors, metrics, error_by_horizon,
    CUTOFF_HOUR, JAN_START, JAN_END, FORECAST_PUB_START, FORECAST_PUB_END,
    LONDON,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Wind Forecast Decision & Accuracy",
    description="Shows the wind forecast available at decision time and quantifies its accuracy.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten for production
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cache — January 2026 data is small (~744 hourly records)
CACHE: dict = {}


def _validate_jan_date(d: str, label: str) -> date:
    """Parse and validate that a date string falls within January 2026."""
    try:
        dt = date.fromisoformat(d)
    except ValueError:
        raise HTTPException(400, f"Invalid {label} date format. Use YYYY-MM-DD.")
    if dt < JAN_START or dt > JAN_END:
        raise HTTPException(400, f"{label} must be between 2026-01-01 and 2026-01-31.")
    return dt


def _load_data():
    """Fetch and cache all January 2026 data on first request."""
    if "errors" in CACHE:
        return CACHE["errors"]

    logger.info("Loading January 2026 data from Elexon...")
    try:
        actuals = fetch_actuals(str(JAN_START), str(JAN_END))
        forecast_rows = fetch_forecasts(FORECAST_PUB_START, FORECAST_PUB_END)
    except Exception as e:
        logger.error("Failed to fetch Elexon data: %s", e)
        raise HTTPException(502, f"Failed to fetch data from Elexon API: {e}")

    best = decision_forecasts(forecast_rows)
    errors = build_errors(best, actuals)

    if not errors:
        raise HTTPException(502, "No matched forecast/actual pairs found. Check Elexon data availability.")

    CACHE["errors"] = errors
    CACHE["total_possible_hours"] = 744  # 31 days * 24 hours
    logger.info("Loaded %d error records (of %d possible hours)", len(errors), 744)
    return errors


def _dt_to_iso(dt: datetime) -> str:
    """Convert a datetime to ISO string for JSON response."""
    return dt.isoformat()


@app.get("/api/health")
def health():
    """Health check endpoint."""
    return {"ok": True, "cutoff_hour": CUTOFF_HOUR, "timezone": "Europe/London"}


@app.get("/api/forecast")
def forecast_for_date(date: str = Query(..., description="Date in YYYY-MM-DD format, January 2026")):
    """
    Return forecast vs actual for each hour on the given date.
    Includes the publish time of the selected forecast and the cutoff used.
    """
    dt = _validate_jan_date(date, "date")
    errors = _load_data()

    day_rows = []
    for r in errors:
        r_date = r["start"].astimezone(LONDON).date()
        if r_date == dt:
            day_rows.append({
                "startTime": _dt_to_iso(r["start"]),
                "forecast": r["forecast"],
                "actual": round(r["actual"], 1),
                "error": round(r["error"], 1),
                "publishTime": _dt_to_iso(r["pub"]),
                "horizon_h": round(r["horizon_h"], 1),
            })

    if not day_rows:
        raise HTTPException(404, f"No data found for {date}.")

    return {
        "date": date,
        "cutoff_hour": CUTOFF_HOUR,
        "cutoff_timezone": "Europe/London",
        "records": day_rows,
    }


@app.get("/api/accuracy")
def accuracy(
    start: str = Query("2026-01-01", description="Start date YYYY-MM-DD"),
    end: str = Query("2026-01-31", description="End date YYYY-MM-DD"),
):
    """
    Return accuracy metrics and error-by-horizon breakdown for a date range.
    """
    start_dt = _validate_jan_date(start, "start")
    end_dt = _validate_jan_date(end, "end")
    if start_dt > end_dt:
        raise HTTPException(400, "start must be <= end.")

    errors = _load_data()

    filtered = [
        r for r in errors
        if start_dt <= r["start"].astimezone(LONDON).date() <= end_dt
    ]

    m = metrics(filtered)
    by_horizon = error_by_horizon(filtered)

    return {
        "start": start,
        "end": end,
        "cutoff_hour": CUTOFF_HOUR,
        "cutoff_timezone": "Europe/London",
        "error_convention": "forecast - actual (positive = over-forecast)",
        "metrics": m,
        "by_horizon": by_horizon,
    }


@app.get("/api/errors")
def errors_list(
    start: str = Query("2026-01-01", description="Start date YYYY-MM-DD"),
    end: str = Query("2026-01-31", description="End date YYYY-MM-DD"),
):
    """
    Return raw error records for charting (forecast vs actual over time).
    """
    start_dt = _validate_jan_date(start, "start")
    end_dt = _validate_jan_date(end, "end")
    errors = _load_data()

    filtered = [
        {
            "startTime": _dt_to_iso(r["start"]),
            "forecast": r["forecast"],
            "actual": round(r["actual"], 1),
            "error": round(r["error"], 1),
        }
        for r in errors
        if start_dt <= r["start"].astimezone(LONDON).date() <= end_dt
    ]

    return {"records": filtered, "n": len(filtered)}
