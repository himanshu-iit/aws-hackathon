import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { logout as apiLogout } from "../services/endpoints";

const navItems = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/guests", label: "Guests" },
  { to: "/guests/register", label: "Register" },
  { to: "/check-in", label: "Check-In" },
  { to: "/analytics", label: "Analytics" },
  { to: "/volunteers", label: "Volunteers" },
  { to: "/status", label: "Status" },
];

export default function Layout() {
  const { isAuthenticated, userType, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    try {
      await apiLogout();
    } catch {
      /* ignore network errors on logout */
    }
    logout();
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark">ET</span>
          <div>
            <div className="brand-title">Event Entry Guest Tracker</div>
            <div className="brand-sub">AWS · Flask · React</div>
          </div>
        </div>
        <nav className="app-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? "nav-link nav-link-active" : "nav-link")}
            >
              {item.label}
            </NavLink>
          ))}
          {isAuthenticated ? (
            <button className="nav-link nav-logout" onClick={handleLogout}>
              Logout ({userType === "master_user" ? "Master" : "Volunteer"})
            </button>
          ) : (
            <NavLink to="/login" className={({ isActive }) => (isActive ? "nav-link nav-link-active" : "nav-link")}>
              Login
            </NavLink>
          )}
        </nav>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
      <footer className="app-footer">
        Event Entry Guest Tracker — S3 + CloudFront → ALB → ECS Fargate → RDS MySQL
      </footer>
    </div>
  );
}
