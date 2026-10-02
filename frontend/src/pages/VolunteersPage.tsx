import { useEffect, useState, useCallback } from "react";
import {
  listVolunteers,
  approveVolunteer,
  rejectVolunteer,
  registerVolunteer,
} from "../services/endpoints";
import { parseApiError } from "../services/api";
import { useAuth } from "../context/AuthContext";
import { Link } from "react-router-dom";

interface Vol {
  volunteer_id: string;
  name: string;
  email?: string;
  phone: string;
  status: string;
  registered_at?: string;
}

export default function VolunteersPage() {
  const { isAuthenticated, userType } = useAuth();
  const isMaster = userType === "master_user";

  const [vols, setVols] = useState<Vol[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  // Self-registration form (open to anyone)
  const [reg, setReg] = useState({ name: "", phone: "", email: "", event_id: "" });

  const load = useCallback(async () => {
    if (!isMaster) return;
    try {
      const res = await listVolunteers();
      setVols(res.volunteers || []);
      setError(null);
    } catch (err) {
      setError(parseApiError(err).message);
    }
  }, [isMaster]);

  useEffect(() => {
    if (isAuthenticated && isMaster) load();
  }, [isAuthenticated, isMaster, load]);

  async function doRegister(e: React.FormEvent) {
    e.preventDefault();
    setMessage(null);
    setError(null);
    try {
      const res = await registerVolunteer(reg);
      setMessage(res.message || `Registered. Status: ${res.status}.`);
      setReg({ name: "", phone: "", email: "", event_id: "" });
      if (isMaster) load();
    } catch (err) {
      setError(parseApiError(err).message);
    }
  }

  async function act(id: string, action: "approve" | "reject") {
    try {
      if (action === "approve") await approveVolunteer(id);
      else await rejectVolunteer(id);
      load();
    } catch (err) {
      setError(parseApiError(err).message);
    }
  }

  return (
    <div className="page">
      <h1>Volunteers</h1>

      {/* Self-registration — available to all */}
      <div className="card">
        <h2>Register as Volunteer</h2>
        <form className="form" onSubmit={doRegister}>
          <div className="field-row">
            <label className="field"><span>Name *</span>
              <input value={reg.name} onChange={(e) => setReg({ ...reg, name: e.target.value })} required />
            </label>
            <label className="field"><span>Phone (+CC-XXXXXXXXXX) *</span>
              <input value={reg.phone} onChange={(e) => setReg({ ...reg, phone: e.target.value })} placeholder="+91-9876543210" required />
            </label>
          </div>
          <div className="field-row">
            <label className="field"><span>Email</span>
              <input type="email" value={reg.email} onChange={(e) => setReg({ ...reg, email: e.target.value })} />
            </label>
            <label className="field"><span>Event ID (2 digits) *</span>
              <input value={reg.event_id} onChange={(e) => setReg({ ...reg, event_id: e.target.value })} placeholder="42" maxLength={2} required />
            </label>
          </div>
          <small className="muted">Enter the event ID your master gave you.</small>
          <button className="btn btn-primary">Register</button>
        </form>
      </div>

      {message && <div className="alert alert-ok">{message}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      {/* Master-only approval UI */}
      {!isAuthenticated && (
        <div className="alert alert-error">
          <Link to="/login">Log in</Link> as master to review pending volunteers.
        </div>
      )}
      {isAuthenticated && !isMaster && (
        <div className="phase-notice">Only master users can review and approve volunteers.</div>
      )}
      {isMaster && (
        <div className="card">
          <h2>Manage Volunteers</h2>
          <table className="data-table">
            <thead>
              <tr><th>Name</th><th>Phone</th><th>Status</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {vols.map((v) => (
                <tr key={v.volunteer_id}>
                  <td>{v.name}</td>
                  <td>{v.phone}</td>
                  <td><span className={`badge badge-${v.status}`}>{v.status.replace(/_/g, " ")}</span></td>
                  <td>
                    {v.status === "pending_approval" && (
                      <>
                        <button className="btn btn-sm btn-primary" onClick={() => act(v.volunteer_id, "approve")}>Approve</button>{" "}
                        <button className="btn btn-sm" onClick={() => act(v.volunteer_id, "reject")}>Reject</button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
              {vols.length === 0 && <tr><td colSpan={4} className="muted">No volunteers.</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
