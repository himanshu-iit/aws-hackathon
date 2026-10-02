import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="page page-narrow">
      <h1>404</h1>
      <p>That page does not exist.</p>
      <Link className="btn btn-primary" to="/status">
        Go to Backend Status
      </Link>
    </div>
  );
}
