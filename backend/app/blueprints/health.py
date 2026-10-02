"""Health check endpoint used by the ALB target group."""
from flask import Blueprint, jsonify

from app.extensions import db
from sqlalchemy import text

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.route("/health", methods=["GET"])
def health():
    """Return 200 when the app and DB connection are healthy."""
    db_ok = True
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_ok = False

    status_code = 200 if db_ok else 503
    return (
        jsonify(
            {
                "success": db_ok,
                "service": "event-tracker-backend",
                "database": "ok" if db_ok else "unavailable",
            }
        ),
        status_code,
    )
