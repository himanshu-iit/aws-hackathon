"""Event, session, and location management endpoints (later phases)."""
from flask import Blueprint, jsonify

events_bp = Blueprint("events", __name__, url_prefix="/api/events")


def _todo(name: str):
    return jsonify({"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": f"{name} is implemented in a later phase"}}), 501


@events_bp.route("", methods=["POST"])
def create_event():
    return _todo("create event")


@events_bp.route("", methods=["GET"])
def list_events():
    return _todo("list events")


@events_bp.route("/<event_id>/sessions", methods=["POST"])
def create_session(event_id):
    return _todo("create session")


@events_bp.route("/<event_id>/sessions", methods=["GET"])
def list_sessions(event_id):
    return _todo("list sessions")


@events_bp.route("/<event_id>/locations", methods=["POST"])
def create_location(event_id):
    return _todo("create location")


@events_bp.route("/<event_id>/locations", methods=["GET"])
def list_locations(event_id):
    return _todo("list locations")
