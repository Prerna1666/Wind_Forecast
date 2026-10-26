import { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend
} from 'recharts';
import { getForecast } from '../api';

/**
 * ForecastTab: Shows forecast vs actual wind generation for a single day.
 * User picks a date in January 2026. Chart shows hourly values.
 */
export default function ForecastTab() {
  const [date, setDate] = useState('2026-01-15');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!date) return;
    setLoading(true);
    setError(null);
    getForecast(date)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [date]);

  // Format hour from ISO string for chart axis
  const chartData = data?.records?.map(r => ({
    hour: new Date(r.startTime).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' }),
    Forecast: r.forecast,
    Actual: Math.round(r.actual),
    Error: Math.round(r.error),
  })) || [];

  return (
    <div>
      <div className="controls">
        <div className="control-group">
          <label htmlFor="forecast-date">Delivery date</label>
          <input
            id="forecast-date"
            type="date"
            value={date}
            min="2026-01-01"
            max="2026-01-31"
            onChange={e => setDate(e.target.value)}
          />
        </div>
        {data && (
          <span className="cutoff-badge">
            Cutoff: {data.cutoff_hour}:00 {data.cutoff_timezone} on D-1
          </span>
        )}
      </div>

      {loading && (
        <div className="state-message">
          <div className="spinner"></div>
          <div>Loading forecast data…</div>
        </div>
      )}

      {error && <div className="state-message error">{error}</div>}

      {data && !loading && (
        <>
          {data.records.length > 0 && (
            <div className="info-box">
              Showing the <strong>latest forecast published before {data.cutoff_hour}:00 {data.cutoff_timezone}</strong> on the day before delivery.
              Forecast published at <strong>{new Date(data.records[0].publishTime).toUTCString()}</strong>.
              {' '}Error = forecast − actual (positive = over-forecast).
            </div>
          )}

          <div className="chart-container">
            <div className="chart-title">Forecast vs Actual — {date}</div>
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2d3148" />
                <XAxis dataKey="hour" stroke="#6b7280" fontSize={11} />
                <YAxis stroke="#6b7280" fontSize={11} tickFormatter={v => `${(v / 1000).toFixed(0)}k`} />
                <Tooltip
                  contentStyle={{ background: '#1e2130', border: '1px solid #2d3148', borderRadius: 8, fontSize: 13 }}
                  labelStyle={{ color: '#9ca3b8' }}
                  formatter={(value) => [`${value.toLocaleString()} MW`]}
                />
                <Legend />
                <Line type="monotone" dataKey="Forecast" stroke="#818cf8" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="Actual" stroke="#34d399" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <div className="chart-title">Forecast Error (forecast − actual)</div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2d3148" />
                <XAxis dataKey="hour" stroke="#6b7280" fontSize={11} />
                <YAxis stroke="#6b7280" fontSize={11} />
                <Tooltip
                  contentStyle={{ background: '#1e2130', border: '1px solid #2d3148', borderRadius: 8, fontSize: 13 }}
                  formatter={(value) => [`${value.toLocaleString()} MW`]}
                />
                <Line type="monotone" dataKey="Error" stroke="#f87171" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}
