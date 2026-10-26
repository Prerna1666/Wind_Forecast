<<<<<<< HEAD
# UK Wind Forecast — Decision & Accuracy Dashboard

A web application for UK day-ahead power buyers that shows the **latest wind generation forecast available at decision time** and **quantifies forecast accuracy** against actual generation, using Elexon BMRS data for January 2026.

---

## Deployed Application

> **Link:** _(to be added after deployment)_

---

## Files & Directory Structure

```
Wind_forecast/
├── backend/                    # Python / FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI server — /api/health, /api/forecast,
│   │   │                       #   /api/accuracy, /api/errors endpoints
│   │   ├── elexon.py           # Elexon BMRS API client — fetches FUELHH (actuals)
│   │   │                       #   and WINDFOR (forecasts) in weekly chunks
│   │   └── analysis.py         # Core logic — decision-time forecast selection,
│   │                           #   error computation, MAE/RMSE/bias/P90 metrics,
│   │                           #   and error-by-horizon bucketing
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_analysis.py    # Unit tests for cutoff logic, joins, metrics (14 tests)
│   │   └── test_api.py         # API endpoint tests with mocked data (8 tests)
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                   # React / Vite frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── ForecastTab.jsx  # Daily view — date picker, forecast vs actual
│   │   │   │                    #   line chart, error chart, publish time display
│   │   │   └── AccuracyTab.jsx  # Accuracy view — date range picker, metric cards
│   │   │                        #   (MAE, RMSE, bias, P90, NMAE), buyer headline,
│   │   │                        #   error-by-horizon bar chart
│   │   ├── App.jsx              # Root component — tab navigation, header, health status
│   │   ├── api.js               # Fetch wrappers for backend API
│   │   ├── index.css            # Dark theme design system
│   │   └── main.jsx             # React entry point
│   ├── index.html
│   ├── Dockerfile
│   ├── vite.config.js
│   └── package.json
│
├── docker-compose.yml           # Runs backend (port 8000) + frontend (port 3000)
├── .gitignore
└── README.md
```

---

## How to Start the Application

### Option A: Local Development

**Prerequisites:** Python 3.12+ (or `uv`), Node.js 18+

**1. Backend (Terminal 1):**
```bash
# From project root
uv venv .venv
source .venv/bin/activate
uv pip install -r backend/requirements.txt
uvicorn backend.app.main:app --port 8000
```

**2. Frontend (Terminal 2):**
```bash
cd frontend
npm install
npm run dev
```

**3. Open:** http://localhost:3000

**4. Run tests:**
```bash
source .venv/bin/activate
pytest backend/tests -v
```

### Option B: Docker

```bash
docker compose up --build
```
Open http://localhost:3000

---

## How It Works

### The Core Problem
On day **D-1**, a power buyer must decide how much electricity to procure for delivery day **D**. They rely on wind generation forecasts, but multiple forecast updates exist for each delivery hour. The key question: **which forecast was actually available when the decision had to be made?**

### The Approach
1. **Decision cutoff:** 09:00 Europe/London on D-1 (assumption — configurable as a single constant `CUTOFF_HOUR`).
2. **Forecast selection:** For each target delivery hour, keep only the **latest forecast published at or before the cutoff**. Later forecasts are excluded because they weren't available at decision time.
3. **Error computation:** `Error = Forecast − Actual` (positive = over-forecast, negative = under-forecast).
4. **Accuracy metrics:** MAE, RMSE, mean bias, P50/P90 absolute error, normalized MAE (%), and error breakdown by forecast horizon in 6-hour buckets.

### Data Sources
- **Actuals:** Elexon BMRS `FUELHH` dataset (fuelType = WIND), half-hourly records averaged to hourly.
- **Forecasts:** Elexon BMRS `WINDFOR` dataset, fetched in weekly chunks across the publish date range (30 Dec 2025 – 31 Jan 2026).

### Scope
- National-level wind generation only.
- January 2026 delivery (target times 1–31 Jan 2026).
- 744 matched hours (31 days × 24 hours, 100% coverage).

---

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/health` | Server status, cutoff hour, timezone |
| `GET /api/forecast?date=YYYY-MM-DD` | Hourly forecast vs actual for a single delivery day |
| `GET /api/accuracy?start=...&end=...` | Accuracy metrics + error-by-horizon for a date range |
| `GET /api/errors?start=...&end=...` | Raw error records for charting |

Interactive API docs available at http://localhost:8000/docs when the backend is running.

---

## Key Assumptions

- **Cutoff time:** 09:00 Europe/London on D-1 (constant, stated in UI and API responses).
- **Error sign:** `Forecast − Actual`. Positive = over-forecast (bought less external power than needed).
- **Timezone:** UTC internally; Europe/London only for cutoff and display.
- **Missing data:** Inner join — only hours with both a forecast and an actual are included. Coverage count is reported.
- **No database:** In-memory cache. January data is small enough (~744 records).

---

## AI Tools Used

- **Tool:** Antigravity (Google DeepMind agentic coding assistant).
- **Used for:** Project scaffolding, writing unit tests, CSS theming, Docker configuration, README drafting.
- **Verified manually:** All mathematical formulas, forecast selection logic, API behavior, and data correctness were independently tested through the unit test suite and manual spot-checks against raw Elexon API output.

---

## Known Limitations & Next Steps

- **Single month scope:** Only January 2026. Extending to multi-month or rolling windows would reveal seasonal patterns.
- **No database:** In-memory cache works for this scope but wouldn't scale. A scheduled ETL into PostgreSQL/TimescaleDB would be the next step.
- **Fixed cutoff:** A configurable cutoff slider in the UI would let buyers evaluate accuracy at different decision times.
- **No intraday updates:** Currently loads data once on first request. A background refresh job would keep data current.
=======
# Wind_Forecast
>>>>>>> 5836dc58936db998cc773b10981f53b656d0a628
