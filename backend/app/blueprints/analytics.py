"""Analytics, reporting, and export endpoints (Phase 7/8 implement the logic)."""
from flask import Blueprint, jsonify

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/events")


def _todo(name: str):
    return jsonify({"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": f"{name} is implemented in a later phase"}}), 501


@analytics_bp.route("/<event_id>/dashboard", methods=["GET"])
def dashboard(event_id):
    return _todo("dashboard")


@analytics_bp.route("/<event_id>/analytics", methods=["GET"])
def analytics(event_id):
    return _todo("analytics report")


@analytics_bp.route("/<event_id>/analytics/export", methods=["GET"])
def export(event_id):
    return _todo("export")
