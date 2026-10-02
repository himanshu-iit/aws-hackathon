import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import StatusPage from "./pages/StatusPage";
import LoginPage from "./pages/LoginPage";
import SetupPage from "./pages/SetupPage";
import DashboardPage from "./pages/DashboardPage";
import GuestRegistrationPage from "./pages/GuestRegistrationPage";
import GuestsPage from "./pages/GuestsPage";
import CheckInPage from "./pages/CheckInPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import VolunteersPage from "./pages/VolunteersPage";
import NotFoundPage from "./pages/NotFoundPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/status" element={<StatusPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/setup" element={<SetupPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/guests" element={<GuestsPage />} />
        <Route path="/guests/register" element={<GuestRegistrationPage />} />
        <Route path="/check-in" element={<CheckInPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/volunteers" element={<VolunteersPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
