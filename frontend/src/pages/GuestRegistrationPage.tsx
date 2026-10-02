import { useState } from "react";
import { registerGuest } from "../services/endpoints";
import { parseApiError } from "../services/api";
import { useAuth } from "../context/AuthContext";
import { Link } from "react-router-dom";

const CATEGORIES = [
  "General_Attendee", "VIP", "Speaker", "Staff", "Volunteer", "Press", "Sponsor",
];

export default function GuestRegistrationPage() {
  const { isAuthenticated } = useAuth();
  const [form, setForm] = useState({
    name: "", email: "", phone: "", company: "", profession: "",
    category: "General_Attendee", dietary_restrictions: "",
  });
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function update(f: string, v: string) {
    setForm((s) => ({ ...s, [f]: v }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const res = await registerGuest(form);
      setResult(`Registered ${res.guest.name} (${res.guest.guest_id})`);
      setForm({ name: "", email: "", phone: "", company: "", profession: "", category: "General_Attendee", dietary_restrictions: "" });
    } catch (err) {
      const e2 = parseApiError(err);
      const details = e2.details ? ` — ${JSON.stringify(e2.details)}` : "";
      setError(`${e2.message}${details}`);
    } finally {
      setLoading(false);
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="page page-narrow">
        <h1>Register Guest</h1>
        <div className="alert alert-error">Please <Link to="/login">log in</Link> as a master or volunteer to register guests.</div>
      </div>
    );
  }

  return (
    <div className="page page-narrow">
      <h1>Register Guest</h1>
      <form className="card form" onSubmit={handleSubmit}>
        <label className="field">
          <span>Full name *</span>
          <input value={form.name} onChange={(e) => update("name", e.target.value)} required />
        </label>
        <div className="field-row">
          <label className="field">
            <span>Email</span>
            <input type="email" value={form.email} onChange={(e) => update("email", e.target.value)} />
          </label>
          <label className="field">
            <span>Phone (+CC-XXXXXXXXXX)</span>
            <input value={form.phone} onChange={(e) => update("phone", e.target.value)} placeholder="+91-9876543210" />
          </label>
        </div>
        <div className="field-row">
          <label className="field">
            <span>Company</span>
            <input value={form.company} onChange={(e) => update("company", e.target.value)} />
          </label>
          <label className="field">
            <span>Profession</span>
            <input value={form.profession} onChange={(e) => update("profession", e.target.value)} />
          </label>
        </div>
        <div className="field-row">
          <label className="field">
            <span>Category</span>
            <select value={form.category} onChange={(e) => update("category", e.target.value)}>
              {CATEGORIES.map((c) => <option key={c} value={c}>{c.replace(/_/g, " ")}</option>)}
            </select>
          </label>
          <label className="field">
            <span>Dietary restrictions</span>
            <input value={form.dietary_restrictions} onChange={(e) => update("dietary_restrictions", e.target.value)} />
          </label>
        </div>
        <button className="btn btn-primary" disabled={loading}>
          {loading ? "Registering…" : "Register Guest"}
        </button>
        {error && <div className="alert alert-error">{error}</div>}
        {result && <div className="alert alert-ok">{result}</div>}
      </form>
    </div>
  );
}
