"""Volunteer management endpoints (Phase 4, tasks 40-43).

Self-registration (with phone OTP verification), plus Master-only approve,
reject, and pending-list operations.
"""
import logging

from flask import Blueprint, current_app, g, jsonify, request

from app.extensions import db
from app.auth_utils import require_role
from app.models.base import utcnow
from app.models.user import Volunteer, User, VolunteerStatus
from app.models.guest import Event
from app.services.audit_service import record_audit
from app.services.otp_service import OTPService, RateLimitExceeded
from app.models.auth import OTPRequestType
from app.services.notification_service import SMSService
from app.services.phone_validator import PhoneValidator
from app.services.limits import enforce_user_cap
from app.services.event_validator import validate_event_id

logger = logging.getLogger(__name__)

volunteers_bp = Blueprint("volunteers", __name__, url_prefix="/api/volunteers")


def _json_error(code, message, status):
    return jsonify({"success": False, "error": {"code": code, "message": message}}), status


# ── Task 40: Volunteer self-registration ─────────────────────────────────────
@volunteers_bp.route("/register", methods=["POST"])
def register():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    raw_phone = (body.get("phone") or "").strip()
    email = (body.get("email") or "").strip().lower() or None
    event_id = (body.get("event_id") or "").strip()

    if not name:
        return _json_error("MISSING_NAME", "name is required", 400)
    ok, err = PhoneValidator.validate(raw_phone)
    if not ok:
        return _json_error("INVALID_PHONE", err, 400)
    phone = PhoneValidator.normalize(raw_phone)

    # Volunteer must join an EXISTING event (created by a master).
    ok, err = validate_event_id(event_id)
    if not ok:
        return _json_error("INVALID_EVENT_ID", err, 400)
    if db.session.get(Event, event_id) is None:
        return _json_error("EVENT_NOT_FOUND", f"Event '{event_id}' does not exist. Ask your master for the event ID.", 404)

    # Enforce total-user cap (master + volunteers + guests)
    cap_error = enforce_user_cap()
    if cap_error:
        return cap_error

    # Reject duplicates
    existing = User.query_active().filter(
        (User.phone == phone) | ((User.email == email) & (email is not None))
    ).first()
    if existing is not None:
        return _json_error("ALREADY_EXISTS", "An account with this phone or email already exists.", 409)

    bypass = current_app.config.get("AUTH_BYPASS_OTP", False)
    status = VolunteerStatus.APPROVED.value if bypass else VolunteerStatus.PENDING_APPROVAL.value

    volunteer = Volunteer(name=name, phone=phone, email=email, approval_status=status, event_id=event_id)
    db.session.add(volunteer)
    db.session.commit()

    if not bypass:
        # Normal mode: send phone-verification OTP and await approval.
        try:
            otp = OTPService.generate(phone, OTPRequestType.VOLUNTEER_REGISTRATION.value)
            SMSService.send_otp_sms(phone, otp.otp_code)
        except RateLimitExceeded as exc:
            return _json_error("RATE_LIMITED", str(exc), 429)
        message = "Registration received. Verify your phone, then await master approval."
    else:
        message = "Registration complete. You are approved and can log in."

    record_audit("volunteer_registered", "volunteer", volunteer.id, actor_user_id=volunteer.id,
                 notes="auto_approved" if bypass else None)
    return jsonify({
        "success": True,
        "message": message,
        "volunteer_id": volunteer.id,
        "status": volunteer.approval_status,
        "event_id": volunteer.event_id,
    }), 201


# ── Task 43: Pending volunteers list (Master only, scoped to their event) ────
@volunteers_bp.route("", methods=["GET"])
@require_role("master_user")
def list_volunteers():
    status = request.args.get("status")
    query = Volunteer.query_active()
    # Scope to the master's own event.
    if g.current_event_id:
        query = query.filter(Volunteer.event_id == g.current_event_id)
    if status:
        query = query.filter(Volunteer.approval_status == status)
    volunteers = query.order_by(Volunteer.created_at.desc()).all()
    return jsonify({
        "success": True,
        "total": len(volunteers),
        "volunteers": [
            {
                "volunteer_id": v.id,
                "name": v.name,
                "email": v.email,
                "phone": v.phone,
                "status": v.approval_status,
                "registered_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in volunteers
        ],
    })


# ── Task 41: Approve volunteer (Master only) ─────────────────────────────────
@volunteers_bp.route("/<volunteer_id>/approve", methods=["PUT"])
@require_role("master_user")
def approve(volunteer_id):
    volunteer = _get_volunteer(volunteer_id)
    if volunteer is None:
        return _json_error("NOT_FOUND", "Volunteer not found", 404)

    before = volunteer.approval_status
    volunteer.approval_status = VolunteerStatus.APPROVED.value
    volunteer.approved_at = utcnow()
    volunteer.approved_by = g.current_user_id
    db.session.commit()

    SMSService.send_notification_sms(
        volunteer.phone, "Your Event Tracker volunteer account has been approved. You can now log in."
    )
    record_audit("volunteer_approved", "volunteer", volunteer.id,
                 actor_user_id=g.current_user_id,
                 before_value={"status": before}, after_value={"status": volunteer.approval_status})
    return jsonify({
        "success": True,
        "volunteer": {"volunteer_id": volunteer.id, "status": volunteer.approval_status},
    })


# ── Task 42: Reject volunteer (Master only) ──────────────────────────────────
@volunteers_bp.route("/<volunteer_id>/reject", methods=["DELETE"])
@require_role("master_user")
def reject(volunteer_id):
    volunteer = _get_volunteer(volunteer_id)
    if volunteer is None:
        return _json_error("NOT_FOUND", "Volunteer not found", 404)

    before = volunteer.approval_status
    volunteer.approval_status = VolunteerStatus.REJECTED.value
    db.session.commit()

    SMSService.send_notification_sms(
        volunteer.phone, "Your Event Tracker volunteer registration was not approved."
    )
    record_audit("volunteer_rejected", "volunteer", volunteer.id,
                 actor_user_id=g.current_user_id,
                 before_value={"status": before}, after_value={"status": volunteer.approval_status})
    return jsonify({"success": True, "message": "Volunteer rejected"})


def _get_volunteer(volunteer_id: str) -> Volunteer | None:
    v = db.session.get(Volunteer, volunteer_id)
    if v is None or v.is_deleted or v.type != "volunteer":
        return None
    return v
