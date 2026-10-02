import { useState } from "react";
import { searchGuests, checkInGuest, checkOutGuest, Guest } from "../services/endpoints";
import { parseApiError } from "../services/api";
import { useAuth } from "../context/AuthContext";
import { Link } from "react-router-dom";

export default function CheckInPage() {
  const { isAuthenticated } = useAuth();
  const [nameQuery, setNameQuery] = useState("");
  const [results, setResults] = useState<Guest[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function doSearch(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setMessage(null);
    try {
      const res = await searchGuests({ name: nameQuery });
      setResults(res.guests || []);
      if (!res.guests?.length) setMessage("No matching guests.");
    } catch (err) {
      setError(parseApiError(err).message);
    }
  }

  async function act(guest: Guest, action: "in" | "out", confirmRecheck = false) {
    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      const payload: Record<string, unknown> = { guest_id: guest.guest_id };
      if (confirmRecheck) payload.confirm_recheck = true;
      const res = action === "in" ? await checkInGuest(payload) : await checkOutGuest(payload);
      const g = res.guest;
      const vip = g.is_vip_or_speaker ? " ⭐ VIP/Speaker" : "";
      const special = g.special_requirements
        ? ` · Special: ${JSON.stringify(g.special_requirements)}`
        : "";
      if (action === "in") {
        setMessage(`✅ ${g.name} checked in${vip}${special}${res.warning ? ` · ${res.warning}` : ""}`);
      } else {
        setMessage(`👋 ${g.name} checked out · duration ${res.duration_minutes} min`);
      }
      await doSearchSilent();
    } catch (err) {
      const e2 = parseApiError(err);
      if (e2.code === "ALREADY_CHECKED_IN") {
        if (window.confirm(`${e2.message}\n\nCheck in again?`)) {
          await act(guest, "in", true);
          return;
        }
      } else {
        setError(e2.message);
      }
    } finally {
      setLoading(false);
    }
  }

  async function doSearchSilent() {
    try {
      const res = await searchGuests({ name: nameQuery });
      setResults(res.guests || []);
    } catch {
      /* ignore */
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="page page-narrow">
        <h1>Check-In / Check-Out</h1>
        <div className="alert alert-error">Please <Link to="/login">log in</Link> to process check-ins.</div>
      </div>
    );
  }

  return (
    <div className="page">
      <h1>Check-In / Check-Out</h1>
      <form className="card form" onSubmit={doSearch}>
        <label className="field">
          <span>Find guest by name</span>
          <input value={nameQuery} onChange={(e) => setNameQuery(e.target.value)} placeholder="Type a name…" required />
        </label>
        <button className="btn btn-primary">Search</button>
      </form>

      {message && <div className="alert alert-ok">{message}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      {results.length > 0 && (
        <div className="card">
          <table className="data-table">
            <thead>
              <tr><th>Name</th><th>Category</th><th>Status</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {results.map((g) => (
                <tr key={g.guest_id}>
                  <td>{g.name}</td>
                  <td>{g.category.replace(/_/g, " ")}</td>
                  <td><span className={`badge badge-${g.current_status}`}>{g.current_status.replace(/_/g, " ")}</span></td>
                  <td>
                    <button className="btn btn-sm btn-primary" disabled={loading} onClick={() => act(g, "in")}>Check In</button>{" "}
                    <button className="btn btn-sm" disabled={loading} onClick={() => act(g, "out")}>Check Out</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
