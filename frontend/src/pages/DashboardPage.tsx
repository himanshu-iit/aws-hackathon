import { useEffect, useState, useCallback } from "react";
import { getDashboard, getByCategory, getCapacity } from "../services/endpoints";
import { parseApiError } from "../services/api";
import { useAuth } from "../context/AuthContext";
import { Link } from "react-router-dom";

interface Metrics {
  total_registered: number;
  current_present: number;
  departed: number;
  not_checked_in: number;
  peak_attendance: number;
  last_updated: string;
}

export default function DashboardPage() {
  const { isAuthenticated, eventId } = useAuth();
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [categories, setCategories] = useState<Record<string, { count: number; percentage: number }>>({});
  const [capacity, setCapacity] = useState<{ status: string; percentage: number | null } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [d, c, cap] = await Promise.all([getDashboard(), getByCategory(), getCapacity()]);
      setMetrics(d);
      setCategories(c.categories || {});
      setCapacity({ status: cap.status, percentage: cap.percentage });
      setError(null);
    } catch (err) {
      setError(parseApiError(err).message);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;
    load();
    const timer = setInterval(load, 8000); // poll every 8s
    return () => clearInterval(timer);
  }, [isAuthenticated, load]);

  if (!isAuthenticated) {
    return (
      <div className="page page-narrow">
        <h1>Attendance Dashboard</h1>
        <div className="alert alert-error">
          Please <Link to="/login">log in</Link> to view live attendance metrics.
        </div>
      </div>
    );
  }

  const cards = metrics
    ? [
        { label: "Total Registered", value: metrics.total_registered },
        { label: "Currently Present", value: metrics.current_present },
        { label: "Checked Out", value: metrics.departed },
        { label: "Not Checked In", value: metrics.not_checked_in },
        { label: "Peak Attendance", value: metrics.peak_attendance },
      ]
    : [];

  return (
    <div className="page">
      <h1>Attendance Dashboard {eventId && <span className="muted">· Event {eventId}</span>}</h1>
      {error && <div className="alert alert-error">{error}</div>}

      <div className="metric-grid">
        {cards.map((c) => (
          <div className="metric-card" key={c.label}>
            <div className="metric-value">{c.value}</div>
            <div className="metric-label">{c.label}</div>
          </div>
        ))}
      </div>

      {capacity && (
        <div className="card">
          <h2>Capacity</h2>
          <p className="muted">
            Status: <strong>{capacity.status}</strong>
            {capacity.percentage != null ? ` (${capacity.percentage}%)` : " (no limit configured)"}
          </p>
        </div>
      )}

      <div className="card">
        <h2>Attendance by Category</h2>
        <table className="data-table">
          <thead>
            <tr><th>Category</th><th>Count</th><th>Share</th></tr>
          </thead>
          <tbody>
            {Object.entries(categories).map(([cat, v]) => (
              <tr key={cat}>
                <td>{cat.replace(/_/g, " ")}</td>
                <td>{v.count}</td>
                <td>{v.percentage}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {metrics && (
        <p className="muted">Last updated: {new Date(metrics.last_updated).toLocaleTimeString()} · auto-refreshes every 8s</p>
      )}
    </div>
  );
}
