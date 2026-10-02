import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../services/endpoints";
import { parseApiError } from "../services/api";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { login: setSession } = useAuth();
  const navigate = useNavigate();

  const [contact, setContact] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await login(contact);
      if (res.token) {
        setSession(res.token, res.user_type, res.permissions || []);
        navigate("/dashboard");
      } else {
        // OTP mode (if ever re-enabled) returns a message instead of a token.
        setError(res.message || "Login did not return a session. Is OTP enabled?");
      }
    } catch (err) {
      setError(parseApiError(err).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page page-narrow">
      <h1>Login</h1>
      <p className="page-intro">
        Enter the email or phone of a registered master or volunteer. New here?{" "}
        Register as a <a href="/volunteers">volunteer</a> or set up a{" "}
        <a href="/setup">master account</a>.
      </p>
      <form className="card form" onSubmit={handleLogin}>
        <label className="field">
          <span>Email or phone (+CC-XXXXXXXXXX)</span>
          <input
            value={contact}
            onChange={(e) => setContact(e.target.value)}
            placeholder="admin@eventtracker.io"
            required
          />
        </label>
        <button className="btn btn-primary" disabled={loading}>
          {loading ? "Logging in…" : "Login"}
        </button>
        {error && <div className="alert alert-error">{error}</div>}
      </form>
    </div>
  );
}
