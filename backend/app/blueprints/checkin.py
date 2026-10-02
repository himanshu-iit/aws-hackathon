"""Check-in / check-out endpoints (Phase 6 implements the logic)."""
from flask import Blueprint, jsonify

checkin_bp = Blueprint("checkin", __name__, url_prefix="/api/events")


def _todo(name: str):
    return jsonify({"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": f"{name} is implemented in Phase 6"}}), 501


@checkin_bp.route("/<event_id>/check-in", methods=["POST"])
def check_in(event_id):
    return _todo("check-in")


@checkin_bp.route("/<event_id>/check-out", methods=["POST"])
def check_out(event_id):
    return _todo("check-out")


@checkin_bp.route("/<event_id>/status", methods=["GET"])
def guest_status(event_id):
    return _todo("guest status")
