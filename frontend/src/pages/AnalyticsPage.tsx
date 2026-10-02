import { useEffect, useState, useCallback } from "react";
import { getAnalytics, getCategoryAnalytics, getHourly } from "../services/endpoints";
import { parseApiError } from "../services/api";
import { useAuth } from "../context/AuthContext";
import { Link } from "react-router-dom";

export default function AnalyticsPage() {
  const { isAuthenticated } = useAuth();
  const [summary, setSummary] = useState<any>(null);
  const [cats, setCats] = useState<any[]>([]);
  const [hourly, setHourly] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [s, c, h] = await Promise.all([getAnalytics(), getCategoryAnalytics(), getHourly()]);
      setSummary(s);
      setCats(c.categories || []);
      setHourly(h.hourly_breakdown || []);
      setError(null);
    } catch (err) {
      setError(parseApiError(err).message);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) load();
  }, [isAuthenticated, load]);

  if (!isAuthenticated) {
    return (
      <div className="page page-narrow">
        <h1>Analytics</h1>
        <div className="alert alert-error">Please <Link to="/login">log in</Link> to view analytics.</div>
      </div>
    );
  }

  const maxCheckins = Math.max(1, ...hourly.map((h) => h.checkins));

  return (
    <div className="page">
      <h1>Analytics &amp; Reporting</h1>
      {error && <div className="alert alert-error">{error}</div>}

      {summary && (
        <div className="metric-grid">
          <div className="metric-card"><div className="metric-value">{summary.total_registered}</div><div className="metric-label">Registered</div></div>
          <div className="metric-card"><div className="metric-value">{summary.total_checked_in}</div><div className="metric-label">Checked In</div></div>
          <div className="metric-card"><div className="metric-value">{summary.total_checked_out}</div><div className="metric-label">Checked Out</div></div>
          <div className="metric-card"><div className="metric-value">{summary.peak_attendance}</div><div className="metric-label">Peak</div></div>
        </div>
      )}

      <div className="card">
        <h2>By Category</h2>
        <table className="data-table">
          <thead><tr><th>Category</th><th>Count</th><th>Check-in rate</th><th>Check-out rate</th></tr></thead>
          <tbody>
            {cats.map((c) => (
              <tr key={c.category}>
                <td>{c.category.replace(/_/g, " ")}</td>
                <td>{c.count}</td>
                <td>{c.checkin_rate}%</td>
                <td>{c.checkout_rate}%</td>
              </tr>
            ))}
            {cats.length === 0 && <tr><td colSpan={4} className="muted">No category data.</td></tr>}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2>Hourly Check-Ins</h2>
        {hourly.length === 0 && <p className="muted">No check-in activity yet.</p>}
        <div className="bar-chart">
          {hourly.map((h) => (
            <div className="bar-row" key={h.hour}>
              <span className="bar-label">{h.hour.slice(11)}</span>
              <div className="bar-track">
                <div className="bar-fill" style={{ width: `${(h.checkins / maxCheckins) * 100}%` }} />
              </div>
              <span className="bar-value">{h.checkins}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
