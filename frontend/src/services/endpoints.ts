import { api } from "./api";

export interface HealthResponse {
  success: boolean;
  service: string;
  database: string;
}

export const EVENT_ID = "demo-event";

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
  const { data } = await api.post("/api/guests", { ...payload, event_id: EVENT_ID });
  return data;
}

export async function listGuests(params: Record<string, string> = {}) {
  const { data } = await api.get("/api/guests", { params: { event_id: EVENT_ID, ...params } });
  return data;
}

export async function searchGuests(params: Record<string, string>) {
  const { data } = await api.get("/api/guests/search", { params: { event_id: EVENT_ID, ...params } });
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
  const { data } = await api.post(`/api/events/${EVENT_ID}/check-in`, payload);
  return data;
}

export async function checkOutGuest(payload: Record<string, unknown>) {
  const { data } = await api.post(`/api/events/${EVENT_ID}/check-out`, payload);
  return data;
}

// ── Dashboard / Analytics ────────────────────────────────────────────────────
export async function getDashboard() {
  const { data } = await api.get(`/api/events/${EVENT_ID}/dashboard`);
  return data;
}

export async function getByCategory() {
  const { data } = await api.get(`/api/events/${EVENT_ID}/analytics/by-category`);
  return data;
}

export async function getCapacity() {
  const { data } = await api.get(`/api/events/${EVENT_ID}/capacity`);
  return data;
}

export async function getAnalytics() {
  const { data } = await api.get(`/api/events/${EVENT_ID}/analytics`);
  return data;
}

export async function getHourly() {
  const { data } = await api.get(`/api/events/${EVENT_ID}/analytics/hourly`);
  return data;
}

export async function getCategoryAnalytics() {
  const { data } = await api.get(`/api/events/${EVENT_ID}/analytics/categories`);
  return data;
}

// ── Volunteers ────────────────────────────────────────────────────────────
export async function registerVolunteer(payload: { name: string; phone: string; email?: string }) {
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
