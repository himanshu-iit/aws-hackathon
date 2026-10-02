import { useEffect, useState, useCallback } from "react";
import { listGuests, Guest } from "../services/endpoints";
import { parseApiError } from "../services/api";
import { useAuth } from "../context/AuthContext";
import { Link } from "react-router-dom";

export default function GuestsPage() {
  const { isAuthenticated } = useAuth();
  const [guests, setGuests] = useState<Guest[]>([]);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const params: Record<string, string> = {};
      if (statusFilter) params.current_status = statusFilter;
      const res = await listGuests(params);
      setGuests(res.guests || []);
      setTotal(res.total || 0);
      setError(null);
    } catch (err) {
      setError(parseApiError(err).message);
    }
  }, [statusFilter]);

  useEffect(() => {
    if (isAuthenticated) load();
  }, [isAuthenticated, load]);

  if (!isAuthenticated) {
    return (
      <div className="page page-narrow">
        <h1>Guests</h1>
        <div className="alert alert-error">Please <Link to="/login">log in</Link> to view guests.</div>
      </div>
    );
  }

  return (
    <div className="page">
      <h1>Guests <span className="muted">({total})</span></h1>
      <div className="card">
        <label className="field">
          <span>Filter by status</span>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">All</option>
            <option value="present">Present</option>
            <option value="departed">Departed</option>
            <option value="not_checked_in">Not checked in</option>
          </select>
        </label>
      </div>
      {error && <div className="alert alert-error">{error}</div>}
      <div className="card">
        <table className="data-table">
          <thead>
            <tr><th>Name</th><th>Category</th><th>Company</th><th>Status</th></tr>
          </thead>
          <tbody>
            {guests.map((g) => (
              <tr key={g.guest_id}>
                <td>{g.name}</td>
                <td>{g.category.replace(/_/g, " ")}</td>
                <td>{g.company || "—"}</td>
                <td><span className={`badge badge-${g.current_status}`}>{g.current_status.replace(/_/g, " ")}</span></td>
              </tr>
            ))}
            {guests.length === 0 && <tr><td colSpan={4} className="muted">No guests.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
