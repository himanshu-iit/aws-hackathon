import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { masterSetup } from "../services/endpoints";
import { parseApiError } from "../services/api";
import { useAuth } from "../context/AuthContext";

export default function SetupPage() {
  const { login: setSession } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({ name: "", email: "", phone: "" });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function update(f: string, v: string) {
    setForm((s) => ({ ...s, [f]: v }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      // OTP is bypassed server-side; empty OTP fields are accepted.
      const res = await masterSetup({
        email: form.email,
        phone: form.phone,
        name: form.name,
        otp_email: "",
        otp_phone: "",
      });
      if (res.token) {
        setSession(res.token, res.user?.type || "master_user", res.permissions || []);
        navigate("/dashboard");
      } else {
        setError(res.message || "Setup did not return a session.");
      }
    } catch (err) {
      setError(parseApiError(err).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page page-narrow">
      <h1>Master Account Setup</h1>
      <p className="page-intro">Create a master (admin) account.</p>
      <form className="card form" onSubmit={handleSubmit}>
        <label className="field">
          <span>Name</span>
          <input value={form.name} onChange={(e) => update("name", e.target.value)} placeholder="Admin User" />
        </label>
        <label className="field">
          <span>Email *</span>
          <input type="email" value={form.email} onChange={(e) => update("email", e.target.value)} placeholder="admin@eventtracker.io" required />
        </label>
        <label className="field">
          <span>Phone (+CC-XXXXXXXXXX) *</span>
          <input value={form.phone} onChange={(e) => update("phone", e.target.value)} placeholder="+91-9876543210" required />
        </label>
        <button className="btn btn-primary" disabled={loading}>
          {loading ? "Creating…" : "Create Master Account"}
        </button>
        {error && <div className="alert alert-error">{error}</div>}
      </form>
    </div>
  );
}
