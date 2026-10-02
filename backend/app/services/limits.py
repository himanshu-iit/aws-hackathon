"""System capacity limits (configurable via ECS task env vars).

- MAX_TOTAL_USERS: cap on master + volunteers + guests combined.
- MAX_CONCURRENT_SESSIONS: cap on simultaneously-active login sessions.

These are app-enforced because neither ALB nor ECS can count application
entities (user rows, active sessions). They are surfaced as environment
variables so they can be tuned from the ECS task definition without a code
change.
"""
from flask import current_app, jsonify

from app.models.user import User
from app.models.guest import Guest


def total_user_count() -> int:
    """Count all non-deleted users (master + volunteers) plus guests."""
    users = User.query_active().count()
    guests = Guest.query_active().count()
    return users + guests


def enforce_user_cap():
    """Return a JSON 403 response if the total-user cap is reached, else None."""
    cap = current_app.config.get("MAX_TOTAL_USERS", 200)
    if total_user_count() >= cap:
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "USER_LIMIT_REACHED",
                    "message": f"Maximum of {cap} total users (masters, volunteers, guests) reached.",
                },
            }),
            403,
        )
    return None
