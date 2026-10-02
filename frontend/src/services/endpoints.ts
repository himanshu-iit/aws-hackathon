import { api } from "./api";

export interface HealthResponse {
  success: boolean;
  service: string;
  database: string;
}

/** The current logged-in user's event ID (set at login/setup). */
export function currentEventId(): string {
  return localStorage.getItem("event_id") || "";
}

// ── Health ────────────────────────────────────────────────────────────────
export async function getHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>("/api/health");
  return data;
}

// ── Auth ────────────────────────────────────────────────────────────────────
export async function requestOtp(phoneOrEmail: string, purpose = "login") {
  const { data } = await api.post("/api/auth/otp-request", {
    phone_or_email: phoneOrEmail,
    purpose,
  });
  return data;
}

export async function login(phoneOrEmail: string) {
  const { data } = await api.post("/api/auth/login", { phone_or_email: phoneOrEmail });
  return data;
}

export async function verifyOtp(phoneOrEmail: string, otpCode: string) {
  const { data } = await api.post("/api/auth/otp-verify", {
    phone_or_email: phoneOrEmail,
    otp_code: otpCode,
  });
  return data;
}

export async function masterSetup(payload: {
  email: string;
  phone: string;
  event_id: string;
  otp_email: string;
  otp_phone: string;
  name?: string;
}) {
  const { data } = await api.post("/api/auth/master-setup", payload);
  return data;
}

export async function logout() {
  const { data } = await api.post("/api/auth/logout", {});
  return data;
}

// ── Guests ────────────────────────────────────────────────────────────────
export interface Guest {
  guest_id: string;
  name: string;
  email?: string;
  phone?: string;
  company?: string;
  profession?: string;
  category: string;
  current_status: string;
  current_location?: string;
}

export async function registerGuest(payload: Record<string, unknown>) {
  // Backend forces the guest into the session's event; event_id here is informational.
  const { data } = await api.post("/api/guests", { ...payload, event_id: currentEventId() });
  return data;
}

export async function listGuests(params: Record<string, string> = {}) {
  const { data } = await api.get("/api/guests", { params });
  return data;
}

export async function searchGuests(params: Record<string, string>) {
  const { data } = await api.get("/api/guests/search", { params });
  return data;
}

export async function getGuest(guestId: string) {
  const { data } = await api.get(`/api/guests/${guestId}`);
  return data;
}

export async function updateGuest(guestId: string, payload: Record<string, unknown>) {
  const { data } = await api.put(`/api/guests/${guestId}`, payload);
  return data;
}

export async function deleteGuest(guestId: string) {
  const { data } = await api.delete(`/api/guests/${guestId}`);
  return data;
}

// ── Check-in / Check-out ────────────────────────────────────────────────────
export async function checkInGuest(payload: Record<string, unknown>) {
  const { data } = await api.post(`/api/events/${currentEventId()}/check-in`, payload);
  return data;
}

export async function checkOutGuest(payload: Record<string, unknown>) {
  const { data } = await api.post(`/api/events/${currentEventId()}/check-out`, payload);
  return data;
}

// ── Dashboard / Analytics ────────────────────────────────────────────────────
export async function getDashboard() {
  const { data } = await api.get(`/api/events/${currentEventId()}/dashboard`);
  return data;
}

export async function getByCategory() {
  const { data } = await api.get(`/api/events/${currentEventId()}/analytics/by-category`);
  return data;
}

export async function getCapacity() {
  const { data } = await api.get(`/api/events/${currentEventId()}/capacity`);
  return data;
}

export async function getAnalytics() {
  const { data } = await api.get(`/api/events/${currentEventId()}/analytics`);
  return data;
}

export async function getHourly() {
  const { data } = await api.get(`/api/events/${currentEventId()}/analytics/hourly`);
  return data;
}

export async function getCategoryAnalytics() {
  const { data } = await api.get(`/api/events/${currentEventId()}/analytics/categories`);
  return data;
}

// ── Volunteers ────────────────────────────────────────────────────────────
export async function registerVolunteer(payload: { name: string; phone: string; email?: string; event_id: string }) {
  const { data } = await api.post("/api/volunteers/register", payload);
  return data;
}

export async function listVolunteers(status?: string) {
  const { data } = await api.get("/api/volunteers", { params: status ? { status } : {} });
  return data;
}

export async function approveVolunteer(volunteerId: string) {
  const { data } = await api.put(`/api/volunteers/${volunteerId}/approve`, {});
  return data;
}

export async function rejectVolunteer(volunteerId: string) {
  const { data } = await api.delete(`/api/volunteers/${volunteerId}/reject`);
  return data;
}
