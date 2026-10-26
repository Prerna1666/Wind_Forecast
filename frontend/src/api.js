/**
 * API client for the Wind Forecast backend.
 * In development, Vite proxies /api to http://localhost:8000.
 * In production, set VITE_API_URL to the backend URL.
 */
const BASE = import.meta.env.VITE_API_URL || '';

async function fetchJSON(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    const text = await res.text();
    let msg;
    try {
      msg = JSON.parse(text).detail || text;
    } catch {
      msg = text;
    }
    throw new Error(`API error ${res.status}: ${msg}`);
  }
  return res.json();
}

export function getHealth() {
  return fetchJSON('/api/health');
}

export function getForecast(date) {
  return fetchJSON(`/api/forecast?date=${date}`);
}

export function getAccuracy(start, end) {
  return fetchJSON(`/api/accuracy?start=${start}&end=${end}`);
}

export function getErrors(start, end) {
  return fetchJSON(`/api/errors?start=${start}&end=${end}`);
}
