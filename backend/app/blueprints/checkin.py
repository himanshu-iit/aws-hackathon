"""Check-in / check-out endpoints (Phase 6).

Volunteer-assisted check-in and check-out, with duplicate detection,
session-attendance tracking, and rich confirmation responses.
"""
import logging

from flask import Blueprint, g, jsonify, request

from app.extensions import db
from app.auth_utils import require_role, event_scope_ok
from app.models.guest import Guest, GuestCategory, GuestStatus
from app.models.user import User
from app.services.audit_service import record_audit
from app.services.checkin_service import CheckInError, check_in, check_out

logger = logging.getLogger(__name__)

checkin_bp = Blueprint("checkin", __name__, url_prefix="/api/events")

# Only master users and approved volunteers may process check-ins (Req 9.10/10.10)
_STAFF_ROLES = ("master_user", "volunteer")

_HIGHLIGHT_CATEGORIES = {GuestCategory.VIP.value, GuestCategory.SPEAKER.value}


def _json_error(code, message, status):
    return jsonify({"success": False, "error": {"code": code, "message": message}}), status


def _volunteer_label(user_id: str) -> str:
    user = db.session.get(User, user_id)
    return (user.name if user and user.name else user_id)


def _guest_confirmation(guest: Guest) -> dict:
    """Shared guest block for check-in/out confirmations (Req 9.9/10.9/8.4)."""
    special = {}
    if guest.dietary_restrictions:
        special["dietary_restrictions"] = guest.dietary_restrictions
    if guest.accessibility_needs:
        special["accessibility_needs"] = guest.accessibility_needs
    return {
        "guest_id": guest.id,
        "name": guest.name,
        "category": guest.category,
        "is_vip_or_speaker": guest.category in _HIGHLIGHT_CATEGORIES,
        "current_status": guest.current_status,
        "current_location": guest.current_location,
        "special_requirements": special or None,
    }


# ── Task 54: Check-in ────────────────────────────────────────────────────────
@checkin_bp.route("/<event_id>/check-in", methods=["POST"])
@require_role(*_STAFF_ROLES)
def do_check_in(event_id):
    if not event_scope_ok(event_id):
        return _json_error("EVENT_FORBIDDEN", "You can only check in guests for your own event.", 403)
    body = request.get_json(silent=True) or {}
    guest_id = body.get("guest_id")
    if not guest_id:
        return _json_error("MISSING_GUEST", "guest_id is required", 400)

    try:
        result = check_in(
            event_id=event_id,
            guest_id=guest_id,
            volunteer_id=g.current_user_id,
            location_id=body.get("location_id"),
            session_id=body.get("session_id"),
            identification_method=body.get("identification_method"),
            confirm_recheck=bool(body.get("confirm_recheck", False)),
        )
    except CheckInError as exc:
        record_audit("check_in_failed", "guest", guest_id, actor_user_id=g.current_user_id,
                     status="failure", notes=f"{exc.code}: {exc.message}")
        return _json_error(exc.code, exc.message, exc.status)

    guest = result["guest"]
    record_audit("check_in", "guest", guest.id, actor_user_id=g.current_user_id,
                 notes=f"location={result['location']} session={body.get('session_id')}")

    resp = {
        "success": True,
        "message": "Guest checked in",
        "timestamp": result["timestamp"],
        "location": result["location"],
        "volunteer": _volunteer_label(g.current_user_id),
        "guest": _guest_confirmation(guest),
    }
    if result.get("warning"):
        resp["warning"] = result["warning"]
    return jsonify(resp), 201


# ── Task 55: Check-out ───────────────────────────────────────────────────────
@checkin_bp.route("/<event_id>/check-out", methods=["POST"])
@require_role(*_STAFF_ROLES)
def do_check_out(event_id):
    if not event_scope_ok(event_id):
        return _json_error("EVENT_FORBIDDEN", "You can only check out guests for your own event.", 403)
    body = request.get_json(silent=True) or {}
    guest_id = body.get("guest_id")
    if not guest_id:
        return _json_error("MISSING_GUEST", "guest_id is required", 400)

    try:
        result = check_out(
            event_id=event_id,
            guest_id=guest_id,
            volunteer_id=g.current_user_id,
            location_id=body.get("location_id"),
            session_id=body.get("session_id"),
        )
    except CheckInError as exc:
        record_audit("check_out_failed", "guest", guest_id, actor_user_id=g.current_user_id,
                     status="failure", notes=f"{exc.code}: {exc.message}")
        return _json_error(exc.code, exc.message, exc.status)

    guest = result["guest"]
    record_audit("check_out", "guest", guest.id, actor_user_id=g.current_user_id,
                 notes=f"duration_minutes={result['duration_minutes']}")

    return jsonify({
        "success": True,
        "message": "Guest checked out",
        "check_out_time": result["timestamp"],
        "duration_minutes": result["duration_minutes"],
        "location": result["location"],
        "volunteer": _volunteer_label(g.current_user_id),
        "guest": _guest_confirmation(guest),
    })


# ── Guest current status lookup ──────────────────────────────────────────────
@checkin_bp.route("/<event_id>/status", methods=["GET"])
@require_role(*_STAFF_ROLES)
def guest_status(event_id):
    if not event_scope_ok(event_id):
        return _json_error("EVENT_FORBIDDEN", "You can only view guests for your own event.", 403)
    guest_id = request.args.get("guest_id")
    if not guest_id:
        return _json_error("MISSING_GUEST", "guest_id query param is required", 400)
    guest = db.session.get(Guest, guest_id)
    if guest is None or guest.is_deleted or guest.event_id != event_id:
        return _json_error("GUEST_NOT_FOUND", "Guest not found for this event", 404)
    return jsonify({"success": True, "guest": _guest_confirmation(guest)})
