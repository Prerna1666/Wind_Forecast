"""
Elexon BMRS API client for FUELHH (actuals) and WINDFOR (forecasts).

Uses the public v1 streaming endpoints — no API key required.
Fetches in weekly chunks to avoid response-size limits.
"""
import requests
import logging
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"


def parse(ts: str) -> datetime:
    """Parse an ISO timestamp from Elexon into a timezone-aware UTC datetime."""
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def fetch_actuals(start: str, end: str) -> dict:
    """
    Fetch half-hourly wind generation actuals (FUELHH) for a settlement date range.
    Returns {startTime (datetime, UTC): generation_MW}.

    FUELHH reports half-hourly; WINDFOR reports hourly.
    To align, we average every pair of half-hours into the hour starting at the
    even-hour boundary. E.g. 00:00 and 00:30 -> hour starting 00:00.
    """
    url = f"{BASE}/FUELHH/stream"
    params = {
        "settlementDateFrom": start,
        "settlementDateTo": end,
        "fuelType": "WIND",
    }
    logger.info("Fetching actuals %s to %s", start, end)
    r = requests.get(url, params=params, timeout=120)
    r.raise_for_status()
    data = r.json()
    logger.info("Got %d half-hourly actual records", len(data))

    # Group half-hours into hours and average
    hourly: dict[datetime, list[float]] = {}
    for rec in data:
        st = parse(rec["startTime"])
        # Round down to the hour
        hour_start = st.replace(minute=0, second=0, microsecond=0)
        hourly.setdefault(hour_start, []).append(rec["generation"])

    return {k: sum(v) / len(v) for k, v in hourly.items()}


def fetch_forecasts_chunk(pub_from: str, pub_to: str) -> list:
    """Fetch WINDFOR rows for a single publish-date-time window."""
    url = f"{BASE}/WINDFOR/stream"
    params = {
        "publishDateTimeFrom": pub_from,
        "publishDateTimeTo": pub_to,
    }
    logger.info("Fetching forecasts %s to %s", pub_from, pub_to)
    r = requests.get(url, params=params, timeout=120)
    r.raise_for_status()
    data = r.json()
    logger.info("Got %d forecast records", len(data))
    return data


def fetch_forecasts(pub_from: date, pub_to: date, chunk_days: int = 7) -> list:
    """
    Fetch all WINDFOR rows in weekly chunks across a publish-date range.
    Returns the combined list of raw JSON records.
    """
    all_rows = []
    d = pub_from
    while d < pub_to:
        nxt = min(d + timedelta(days=chunk_days), pub_to)
        chunk = fetch_forecasts_chunk(
            f"{d}T00:00Z",
            f"{nxt}T00:00Z",
        )
        all_rows.extend(chunk)
        d = nxt
    logger.info("Total forecast records: %d", len(all_rows))
    return all_rows
