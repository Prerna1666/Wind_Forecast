"""
Analysis module: decision-time forecast selection and accuracy metrics.

Key concept: For each target hour in January 2026, select the latest wind
forecast published at or before the decision cutoff (09:00 London time on D-1).
Then compare that forecast with the actual generation to compute error metrics.

Error sign convention: error = forecast - actual
  Positive = over-forecast (bought less than needed)
  Negative = under-forecast (bought more than needed)
"""
import math
from collections import defaultdict
from datetime import datetime, timedelta, time, date
from zoneinfo import ZoneInfo
from .elexon import parse

LONDON = ZoneInfo("Europe/London")
CUTOFF_HOUR = 9  # 09:00 Europe/London on D-1


def cutoff_for(start: datetime) -> datetime:
    """
    Decision cutoff for a given target delivery time.
    The buyer decides on D-1 at 09:00 London time.
    D is the delivery date (in London time).
    """
    delivery_date = start.astimezone(LONDON).date()
    d_minus_1 = delivery_date - timedelta(days=1)
    return datetime.combine(d_minus_1, time(CUTOFF_HOUR, 0), tzinfo=LONDON)


def decision_forecasts(rows: list) -> dict:
    """
    For each target startTime, keep the latest forecast published at or before
    the decision cutoff.

    Args:
        rows: Raw WINDFOR records with publishTime, startTime, generation.

    Returns:
        {startTime(datetime): {"pub": publishTime, "forecast": generation_MW}}
    """
    best = {}
    for r in rows:
        start = parse(r["startTime"])
        pub = parse(r["publishTime"])
        cutoff = cutoff_for(start)
        if pub > cutoff:
            continue
        if start not in best or pub > best[start]["pub"]:
            best[start] = {"pub": pub, "forecast": r["generation"]}
    return best


def build_errors(best: dict, actuals: dict) -> list:
    """
    Inner-join decision forecasts with actuals and compute errors.
    Returns a sorted list of error records.
    """
    out = []
    for start, f in best.items():
        if start not in actuals:
            continue
        out.append({
            "start": start,
            "pub": f["pub"],
            "forecast": f["forecast"],
            "actual": actuals[start],
            "error": f["forecast"] - actuals[start],
            "horizon_h": (start - f["pub"]).total_seconds() / 3600,
        })
    return sorted(out, key=lambda x: x["start"])


def percentile(vals: list, p: float) -> float:
    """Simple percentile using nearest-rank method."""
    if not vals:
        return 0.0
    s = sorted(vals)
    return s[min(len(s) - 1, int(p * len(s)))]


def metrics(rows: list) -> dict:
    """
    Compute summary accuracy metrics from a list of error records.
    Returns dict with MAE, RMSE, mean bias, P50/P90 absolute error,
    normalized MAE, and count.
    """
    n = len(rows)
    if n == 0:
        return {"n": 0}
    errs = [r["error"] for r in rows]
    abs_errs = [abs(e) for e in errs]
    total_actual = sum(r["actual"] for r in rows)
    return {
        "n": n,
        "mae": round(sum(abs_errs) / n, 1),
        "rmse": round(math.sqrt(sum(e * e for e in errs) / n), 1),
        "bias": round(sum(errs) / n, 1),
        "p50_abs": round(percentile(abs_errs, 0.5), 1),
        "p90_abs": round(percentile(abs_errs, 0.9), 1),
        "nmae_pct": round(100 * sum(abs_errs) / total_actual, 2) if total_actual else None,
    }


def error_by_horizon(rows: list, bin_h: int = 6) -> list:
    """
    Bucket errors by forecast horizon and compute MAE and P90 per bucket.
    bin_h controls the bucket width in hours.
    """
    buckets: dict[int, list[float]] = defaultdict(list)
    for r in rows:
        bucket_key = int(r["horizon_h"] // bin_h) * bin_h
        buckets[bucket_key].append(abs(r["error"]))
    return [
        {
            "horizon_h": k,
            "mae": round(sum(v) / len(v), 1),
            "p90": round(percentile(v, 0.9), 1),
            "n": len(v),
        }
        for k, v in sorted(buckets.items())
    ]


# January 2026 date range constants
JAN_START = date(2026, 1, 1)
JAN_END = date(2026, 1, 31)
# Forecast publish range: need forecasts from Dec 30 (D-1 for Jan 1) through Jan 30
FORECAST_PUB_START = date(2025, 12, 30)
FORECAST_PUB_END = date(2026, 1, 31)
