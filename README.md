# UK Wind Forecast Dashboard

A dashboard that compares UK wind generation forecasts with actual generation to understand how accurate the forecasts are.

The project uses data from Elexon BMRS for January 2026 and focuses on one key question: **How accurate was the wind forecast available when the day-ahead purchasing decision had to be made?**

## Features

- Compare forecasted and actual wind generation.
- View forecast errors for a selected day.
- Check accuracy metrics such as MAE, RMSE and bias.
- Analyse how forecast accuracy changes as delivery time approaches.

## Tech Stack

- React and Vite
- Python and FastAPI
- Elexon BMRS API
- Docker

## Getting Started

**Backend**

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload --port 8000
```

**Frontend** — open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the frontend at the URL shown in your terminal. The API documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).

## AI Assistance

I used Antigravity, an AI coding assistant, to help with the frontend UI and styling, along with some backend implementation. I reviewed the code and tested the main functionality to check that it worked as expected.

## Future Improvements

- Add more months of data.
- Allow users to change the forecast cutoff time.
- Improve data storage and refresh.

## Deployment

Coming soon.
