"""Guest management endpoints (Phase 5).

Registration, retrieval, search, update, and soft-delete. All write operations
require an authenticated Master or approved Volunteer and are recorded in the
audit trail. (Batch registration intentionally omitted per project decision.)
"""
import logging

from flask import Blueprint, g, jsonify, request

from app.extensions import db
from app.auth_utils import require_role
from app.models.guest import Guest, GuestStatus
from app.services.audit_service import record_audit
from app.services.guest_validator import validate_guest

logger = logging.getLogger(__name__)

guests_bp = Blueprint("guests", __name__, url_prefix="/api/guests")

# Guest-management roles: master users and approved volunteers.
_GUEST_ROLES = ("master_user", "volunteer")


def _json_error(code, message, status, details=None):
    err = {"code": code, "message": message}
    if details is not None:
        err["details"] = details
    return jsonify({"success": False, "error": err}), status


def _serialize(guest: Guest) -> dict:
    return {
        "guest_id": guest.id,
        "event_id": guest.event_id,
        "name": guest.name,
        "email": guest.email,
        "phone": guest.phone,
        "company": guest.company,
        "job_title": guest.job_title,
        "profession": guest.profession,
        "emergency_contact_name": guest.emergency_contact_name,
        "emergency_contact_phone": guest.emergency_contact_phone,
        "ticket_number": guest.ticket_number,
        "badge_number": guest.badge_number,
        "category": guest.category,
        "dietary_restrictions": guest.dietary_restrictions,
        "accessibility_needs": guest.accessibility_needs,
        "current_status": guest.current_status,
        "current_location": guest.current_location,
        "registered_by": guest.registered_by,
        "registered_at": guest.created_at.isoformat() if guest.created_at else None,
    }


def _apply_normalized(guest: Guest, normalized: dict) -> None:
    for field, value in normalized.items():
        setattr(guest, field, value)


def _duplicate_exists(event_id: str, phone: str | None) -> bool:
    if not phone:
        return False
    return (
        Guest.query_active()
        .filter(Guest.event_id == event_id, Guest.phone == phone)
        .first()
        is not None
    )


def _get_active_guest(guest_id: str) -> Guest | None:
    guest = db.session.get(Guest, guest_id)
    if guest is None or guest.is_deleted:
        return None
    # Enforce event scope: a user can only touch guests in their own event.
    if g.current_event_id and guest.event_id != g.current_event_id:
        return None
    return guest


# ── Task 45: Single guest registration ───────────────────────────────────────
@guests_bp.route("", methods=["POST"])
@require_role(*_GUEST_ROLES)
def register_guest():
    data = dict(request.get_json(silent=True) or {})
    # Guests always belong to the logged-in user's event — override any client value.
    if g.current_event_id:
        data["event_id"] = g.current_event_id
    result = validate_guest(data, require_event=True)
    if not result.is_valid:
        return _json_error("VALIDATION_ERROR", "Guest data is invalid", 400, result.errors)

    event_id = result.normalized["event_id"]

    # Enforce total-user cap (master + volunteers + guests)
    from app.services.limits import enforce_user_cap
    cap_error = enforce_user_cap()
    if cap_error:
        return cap_error

    # The guest must belong to an existing event (FK integrity).
    from app.models.guest import Event
    if db.session.get(Event, event_id) is None:
        return _json_error("EVENT_NOT_FOUND", f"Event '{event_id}' does not exist", 404)

    phone = result.normalized.get("phone")
    if _duplicate_exists(event_id, phone):
        return _json_error(
            "DUPLICATE_GUEST",
            "A guest with this phone already exists for this event",
            409,
        )

    guest = Guest(
        current_status=GuestStatus.NOT_CHECKED_IN.value,
        registered_by=g.current_user_id,
    )
    _apply_normalized(guest, result.normalized)
    db.session.add(guest)
    db.session.commit()

    record_audit("guest_registered", "guest", guest.id, actor_user_id=g.current_user_id)
    return jsonify({"success": True, "guest": _serialize(guest)}), 201


# ── Task 47: Search ──────────────────────────────────────────────────────────
@guests_bp.route("/search", methods=["GET"])
@require_role(*_GUEST_ROLES)
def search_guests():
    q = Guest.query_active()
    # Always scope to the logged-in user's event.
    if g.current_event_id:
        q = q.filter(Guest.event_id == g.current_event_id)

    name = request.args.get("name")
    if name:
        q = q.filter(Guest.name.ilike(f"%{name}%"))  # case-insensitive substring

    for field in ("phone", "email", "badge_number", "ticket_number"):
        value = request.args.get(field)
        if value:
            q = q.filter(getattr(Guest, field) == value)  # exact match

    limit = min(int(request.args.get("limit", 100)), 500)
    offset = int(request.args.get("offset", 0))
    total = q.count()
    rows = q.order_by(Guest.name.asc()).limit(limit).offset(offset).all()

    return jsonify({
        "success": True,
        "total": total,
        "limit": limit,
        "offset": offset,
        "guests": [_serialize(gst) for gst in rows],
    })


# ── Task 46: List with filters + pagination ──────────────────────────────────
@guests_bp.route("", methods=["GET"])
@require_role(*_GUEST_ROLES)
def list_guests():
    q = Guest.query_active()
    # Always scope to the logged-in user's event.
    if g.current_event_id:
        q = q.filter(Guest.event_id == g.current_event_id)
    for field in ("category", "current_status"):
        value = request.args.get(field)
        if value:
            q = q.filter(getattr(Guest, field) == value)
    name = request.args.get("name")
    if name:
        q = q.filter(Guest.name.ilike(f"%{name}%"))

    limit = min(int(request.args.get("limit", 100)), 500)
    offset = int(request.args.get("offset", 0))
    total = q.count()
    rows = q.order_by(Guest.created_at.desc()).limit(limit).offset(offset).all()

    return jsonify({
        "success": True,
        "total": total,
        "limit": limit,
        "offset": offset,
        "guests": [_serialize(gst) for gst in rows],
    })


# ── Task 46: Get single guest ────────────────────────────────────────────────
@guests_bp.route("/<guest_id>", methods=["GET"])
@require_role(*_GUEST_ROLES)
def get_guest(guest_id):
    guest = _get_active_guest(guest_id)
    if guest is None:
        return _json_error("NOT_FOUND", "Guest not found", 404)
    return jsonify({"success": True, "guest": _serialize(guest)})


# ── Task 49: Update (phone immutable) ────────────────────────────────────────
@guests_bp.route("/<guest_id>", methods=["PUT"])
@require_role(*_GUEST_ROLES)
def update_guest(guest_id):
    guest = _get_active_guest(guest_id)
    if guest is None:
        return _json_error("NOT_FOUND", "Guest not found", 404)

    data = request.get_json(silent=True) or {}
    if data.get("phone") and data["phone"] != guest.phone:
        return _json_error("PHONE_IMMUTABLE", "Phone number cannot be changed", 400)

    updatable = {
        "name", "email", "company", "job_title", "profession",
        "emergency_contact_name", "emergency_contact_phone", "ticket_number",
        "badge_number", "category", "dietary_restrictions", "accessibility_needs",
    }
    subset = {k: v for k, v in data.items() if k in updatable}
    # Validate provided subset; event not required on update, name defaults to current
    res = validate_guest({**subset, "name": data.get("name", guest.name)}, require_event=False)
    if not res.is_valid:
        return _json_error("VALIDATION_ERROR", "Guest data is invalid", 400, res.errors)

    before = _serialize(guest)
    for field in updatable:
        if field in data:
            setattr(guest, field, res.normalized.get(field, data[field]))
    db.session.commit()

    record_audit(
        "guest_updated", "guest", guest.id, actor_user_id=g.current_user_id,
        before_value=before, after_value=_serialize(guest),
    )
    return jsonify({"success": True, "guest": _serialize(guest)})


# ── Task 50: Soft delete (master only) ───────────────────────────────────────
@guests_bp.route("/<guest_id>", methods=["DELETE"])
@require_role("master_user")
def delete_guest(guest_id):
    guest = _get_active_guest(guest_id)
    if guest is None:
        return _json_error("NOT_FOUND", "Guest not found", 404)
    guest.soft_delete()
    db.session.commit()
    record_audit("guest_deleted", "guest", guest.id, actor_user_id=g.current_user_id)
    return jsonify({"success": True, "message": "Guest deleted"})
