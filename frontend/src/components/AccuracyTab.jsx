import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend
} from 'recharts';
import { getAccuracy } from '../api';

/**
 * AccuracyTab: Quantifies forecast accuracy over a date range in January 2026.
 * Shows KPI metric cards, buyer headline, and error breakdown by forecast horizon.
 */
export default function AccuracyTab() {
  const [start, setStart] = useState('2026-01-01');
  const [end, setEnd] = useState('2026-01-31');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!start || !end) return;
    setLoading(true);
    setError(null);
    getAccuracy(start, end)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [start, end]);

  const metrics = data?.metrics;
  const byHorizon = data?.by_horizon?.map(h => ({
    horizon: `${h.horizon_h}h–${h.horizon_h + 6}h`,
    MAE: h.mae,
    P90: h.p90,
    Samples: h.n,
  })) || [];

  return (
    <div>
      <div className="controls">
        <div className="control-group">
          <label htmlFor="start-date">From</label>
          <input
            id="start-date"
            type="date"
            value={start}
            min="2026-01-01"
            max="2026-01-31"
            onChange={e => setStart(e.target.value)}
          />
        </div>
        <div className="control-group">
          <label htmlFor="end-date">To</label>
          <input
            id="end-date"
            type="date"
            value={end}
            min="2026-01-01"
            max="2026-01-31"
            onChange={e => setEnd(e.target.value)}
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
          <div>Calculating accuracy metrics…</div>
        </div>
      )}

      {error && <div className="state-message error">{error}</div>}

      {data && !loading && metrics && (
        <>
          {metrics.n > 0 && (
            <div className="headline">
              Next-day wind forecast is typically off by{' '}
              <strong>{metrics.mae?.toLocaleString()} MW</strong> (MAE);{' '}
              90% of the time errors remain within{' '}
              <strong>{metrics.p90_abs?.toLocaleString()} MW</strong> (P90).
            </div>
          )}

          <div className="cards">
            <div className="card">
              <div className="card-label">Mean Absolute Error (MAE)</div>
              <div className="card-value">
                {metrics.mae?.toLocaleString() ?? '—'}
                <span className="card-unit">MW</span>
              </div>
            </div>
            <div className="card">
              <div className="card-label">Root Mean Sq Error (RMSE)</div>
              <div className="card-value">
                {metrics.rmse?.toLocaleString() ?? '—'}
                <span className="card-unit">MW</span>
              </div>
            </div>
            <div className="card">
              <div className="card-label">Mean Bias (F − A)</div>
              <div className="card-value">
                {metrics.bias > 0 ? `+${metrics.bias}` : metrics.bias ?? '—'}
                <span className="card-unit">MW</span>
              </div>
            </div>
            <div className="card">
              <div className="card-label">P90 Absolute Error</div>
              <div className="card-value">
                {metrics.p90_abs?.toLocaleString() ?? '—'}
                <span className="card-unit">MW</span>
              </div>
            </div>
            <div className="card">
              <div className="card-label">Normalized MAE</div>
              <div className="card-value">
                {metrics.nmae_pct != null ? `${metrics.nmae_pct}%` : '—'}
              </div>
            </div>
            <div className="card">
              <div className="card-label">Coverage (Evaluated Hours)</div>
              <div className="card-value">
                {metrics.n}
                <span className="card-unit">hrs</span>
              </div>
            </div>
          </div>

          <div className="info-box">
            <strong>Key Insights for Day-Ahead Power Buyers:</strong>
            <ul style={{ paddingLeft: '1.2rem', marginTop: '6px' }}>
              <li>
                <strong>Error Sign:</strong> Defined as <code>Forecast − Actual</code>. Positive bias indicates over-forecasting (buying less external power than actually needed).
              </li>
              <li>
                <strong>P90 Safety Margin:</strong> Sizing a reserve or flexibility buffer up to the P90 value ({metrics.p90_abs} MW) covers unpredicted wind swings 90% of the time.
              </li>
              <li>
                <strong>Horizon Sensitivity:</strong> Forecasts made further ahead (e.g. 30h+ before delivery) exhibit higher dispersion than shorter horizons.
              </li>
            </ul>
          </div>

          {byHorizon.length > 0 && (
            <div className="chart-container">
              <div className="chart-title">Error by Forecast Horizon (Lead Time)</div>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={byHorizon} margin={{ top: 10, right: 20, bottom: 5, left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2d3148" />
                  <XAxis dataKey="horizon" stroke="#6b7280" fontSize={12} />
                  <YAxis stroke="#6b7280" fontSize={11} tickFormatter={v => `${v} MW`} />
                  <Tooltip
                    contentStyle={{ background: '#1e2130', border: '1px solid #2d3148', borderRadius: 8, fontSize: 13 }}
                    labelStyle={{ color: '#9ca3b8' }}
                    formatter={(value, name) => [`${value.toLocaleString()} MW`, name]}
                  />
                  <Legend />
                  <Bar dataKey="MAE" fill="#818cf8" radius={[4, 4, 0, 0]} name="MAE (Typical Error)" />
                  <Bar dataKey="P90" fill="#f87171" radius={[4, 4, 0, 0]} name="P90 (Worst 10% Bound)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </div>
  );
}
