import axios, { AxiosError, AxiosInstance } from "axios";

// An empty string is an intentional "same-origin" setting (production, where
// CloudFront proxies /api/* to the ALB). Only fall back to localhost when the
// variable is genuinely undefined (local dev without an env file).
const RAW_BASE = import.meta.env.VITE_API_BASE_URL;
const API_BASE_URL = RAW_BASE === undefined ? "http://localhost:5000" : RAW_BASE;

export const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// Attach session token (if present) to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("session_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401, clear session and bounce to login
api.interceptors.response.use(
  (res) => res,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("session_token");
    }
    return Promise.reject(error);
  }
);

export interface ApiError {
  code: string;
  message: string;
  details?: unknown;
}

/** Normalize an axios error into a consistent shape for the UI. */
export function parseApiError(err: unknown): ApiError {
  const axiosErr = err as AxiosError<{ error?: ApiError }>;
  if (axiosErr.response?.data?.error) {
    return axiosErr.response.data.error;
  }
  if (axiosErr.code === "ERR_NETWORK") {
    return {
      code: "NETWORK_ERROR",
      message:
        "Could not reach the backend. The API may be unavailable or blocked by CORS.",
    };
  }
  return {
    code: "UNKNOWN",
    message: axiosErr.message || "An unexpected error occurred.",
  };
}

export const API_BASE = API_BASE_URL;
