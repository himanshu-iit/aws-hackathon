import { useEffect, useState, useCallback } from "react";
import { getHealth, HealthResponse } from "../services/endpoints";
import { parseApiError, API_BASE } from "../services/api";

type Status = "checking" | "ok" | "error";

export default function StatusPage() {
  const [status, setStatus] = useState<Status>("checking");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<string>("");

  const check = useCallback(async () => {
    setStatus("checking");
    setError(null);
    try {
      const data = await getHealth();
      setHealth(data);
      setStatus("ok");
    } catch (err) {
      setError(parseApiError(err).message);
      setStatus("error");
    } finally {
      setLastChecked(new Date().toLocaleTimeString());
    }
  }, []);

  useEffect(() => {
    check();
  }, [check]);

  return (
    <div className="page">
      <h1>Backend Status</h1>
      <p className="page-intro">
        This page calls the live <code>/api/health</code> endpoint on the
        backend through the Application Load Balancer.
      </p>

      <div className="card">
        <div className="status-row">
          <span
            className={
              status === "ok"
                ? "status-dot status-dot-ok"
                : status === "error"
                ? "status-dot status-dot-error"
                : "status-dot status-dot-checking"
            }
          />
          <span className="status-label">
            {status === "checking" && "Checking backend…"}
            {status === "ok" && "Backend is healthy"}
            {status === "error" && "Backend unreachable"}
          </span>
          <button className="btn btn-sm" onClick={check}>
            Re-check
          </button>
        </div>

        {status === "ok" && health && (
          <dl className="kv">
            <dt>Service</dt>
            <dd>{health.service}</dd>
            <dt>Database</dt>
            <dd>{health.database}</dd>
            <dt>Success</dt>
            <dd>{String(health.success)}</dd>
          </dl>
        )}

        {status === "error" && <div className="alert alert-error">{error}</div>}

        <div className="status-meta">
          <div>
            API base: <code>{API_BASE}</code>
          </div>
          {lastChecked && <div>Last checked: {lastChecked}</div>}
        </div>
      </div>

      <div className="card">
        <h2>Architecture</h2>
        <p className="arch-flow">
          React SPA (S3 + CloudFront) → ALB → ECS Fargate (Flask) → RDS MySQL,
          with logs in CloudWatch.
        </p>
      </div>
    </div>
  );
}
