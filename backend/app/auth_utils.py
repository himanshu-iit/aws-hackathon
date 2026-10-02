"""Auth decorators and helpers for protecting endpoints."""
from functools import wraps

from flask import g, jsonify, request

from app.services.session_service import SessionManager


def _unauthorized(message="Authentication required"):
    return jsonify({"success": False, "error": {"code": "UNAUTHORIZED", "message": message}}), 401


def _forbidden(message="Access denied"):
    return jsonify({"success": False, "error": {"code": "FORBIDDEN", "message": message}}), 403


def _extract_token() -> str | None:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:].strip()
    return None


def require_auth(fn):
    """Require a valid session token. Sets g.session and g.current_user_id."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _extract_token()
        if not token:
            return _unauthorized("Missing bearer token")
        session = SessionManager.validate_session(token)
        if session is None:
            return _unauthorized("Invalid or expired session")
        g.session = session
        g.current_user_id = session.user_id
        g.current_user_type = session.user_type
        g.current_event_id = session.event_id
        return fn(*args, **kwargs)

    return wrapper


def event_scope_ok(event_id: str) -> bool:
    """True if the path event_id matches the session's event (or no scope set)."""
    scope = getattr(g, "current_event_id", None)
    return scope is None or scope == event_id


def require_role(*allowed_types: str):
    """Require the authenticated user to be one of the given user types."""

    def decorator(fn):
        @wraps(fn)
        @require_auth
        def wrapper(*args, **kwargs):
            if g.current_user_type not in allowed_types:
                return _forbidden(
                    f"Requires role: {', '.join(allowed_types)}"
                )
            return fn(*args, **kwargs)

        return wrapper

    return decorator
