"""Request lifecycle middleware: request IDs, logging, security headers, errors."""
import logging
import time
import uuid

from flask import g, jsonify, request

logger = logging.getLogger(__name__)


def register_middleware(app) -> None:
    @app.before_request
    def _start_timer_and_request_id():
        g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        g.start_time = time.monotonic()

    @app.after_request
    def _log_and_secure(response):
        # Timing
        duration_ms = None
        if hasattr(g, "start_time"):
            duration_ms = round((time.monotonic() - g.start_time) * 1000, 2)

        # Structured access log (skip health checks to reduce noise)
        if request.path != "/api/health":
            logger.info(
                "request",
                extra={
                    "request_id": getattr(g, "request_id", None),
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                    "remote_addr": request.remote_addr,
                },
            )

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if getattr(g, "request_id", None):
            response.headers["X-Request-ID"] = g.request_id
        return response

    # ── Consistent JSON error responses ─────────────────────────────────────
    def _error(code: str, message: str, status: int, details=None):
        payload = {"success": False, "error": {"code": code, "message": message}}
        if details is not None:
            payload["error"]["details"] = details
        return jsonify(payload), status

    @app.errorhandler(400)
    def _bad_request(e):
        return _error("BAD_REQUEST", getattr(e, "description", "Bad request"), 400)

    @app.errorhandler(401)
    def _unauthorized(e):
        return _error("UNAUTHORIZED", "Authentication required", 401)

    @app.errorhandler(403)
    def _forbidden(e):
        return _error("FORBIDDEN", "Access denied", 403)

    @app.errorhandler(404)
    def _not_found(e):
        return _error("NOT_FOUND", "Resource not found", 404)

    @app.errorhandler(409)
    def _conflict(e):
        return _error("CONFLICT", getattr(e, "description", "Conflict"), 409)

    @app.errorhandler(429)
    def _rate_limited(e):
        return _error("RATE_LIMITED", "Too many requests", 429)

    @app.errorhandler(500)
    def _server_error(e):
        logger.exception("Unhandled server error", extra={"request_id": getattr(g, "request_id", None)})
        return _error("INTERNAL_ERROR", "An internal error occurred", 500)
