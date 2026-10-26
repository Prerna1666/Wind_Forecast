import { useState, useEffect } from 'react';
import ForecastTab from './components/ForecastTab';
import AccuracyTab from './components/AccuracyTab';
import { getHealth } from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('forecast');
  const [health, setHealth] = useState(null);
  const [healthError, setHealthError] = useState(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((err) => {
        console.warn('Backend not yet reachable:', err.message);
        setHealthError(err.message);
      });
  }, []);

  return (
    <div className="app">
      <header className="header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h1>UK Wind Forecast & Decision Accuracy</h1>
            <p>Day-ahead power procurement analysis using Elexon BMRS data (January 2026)</p>
          </div>
          {health && (
            <span className="cutoff-badge" title="Decision cutoff assumption">
              Decision Cutoff: {health.cutoff_hour}:00 {health.timezone} on D-1
            </span>
          )}
          {healthError && (
            <span className="cutoff-badge" style={{ borderColor: 'rgba(248, 113, 113, 0.4)', color: '#f87171' }}>
              Backend offline
            </span>
          )}
        </div>
      </header>

      <nav className="tabs" aria-label="Dashboard navigation">
        <button
          className={`tab-btn ${activeTab === 'forecast' ? 'active' : ''}`}
          onClick={() => setActiveTab('forecast')}
          id="tab-btn-forecast"
        >
          Daily Forecast View
        </button>
        <button
          className={`tab-btn ${activeTab === 'accuracy' ? 'active' : ''}`}
          onClick={() => setActiveTab('accuracy')}
          id="tab-btn-accuracy"
        >
          Accuracy & Metrics
        </button>
      </nav>

      <main>
        {activeTab === 'forecast' && <ForecastTab />}
        {activeTab === 'accuracy' && <AccuracyTab />}
      </main>

      <footer style={{ marginTop: '48px', paddingTop: '20px', borderTop: '1px solid var(--border)', fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
        <span>Data source: Elexon BMRS datasets (<code>WINDFOR</code> forecast & <code>FUELHH</code> actuals).</span>
        <span>Decision window: 31 Dec 2025 – 30 Jan 2026 for January 2026 delivery.</span>
      </footer>
    </div>
  );
}
