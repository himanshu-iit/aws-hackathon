"""Authentication endpoints (Phase 4).

Implements OTP-based auth, first-launch Master user setup, login, session
validation, and logout.
"""
import logging

from flask import Blueprint, current_app, g, jsonify, request

from app.extensions import db
from app.auth_utils import require_auth
from app.models.auth import OTPRequestType
from app.models.guest import Event
from app.models.user import MasterUser, User, Volunteer, VolunteerStatus
from app.services.audit_service import record_audit
from app.services.event_validator import validate_event_id
from app.services.notification_service import EmailService, SMSService
from app.services.otp_service import OTPService, RateLimitExceeded
from app.services.phone_validator import PhoneValidator
from app.services.session_service import SessionManager

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# ── Helpers ──────────────────────────────────────────────────────────────────
def _json_error(code: str, message: str, status: int):
    return jsonify({"success": False, "error": {"code": code, "message": message}}), status


def _is_email(value: str) -> bool:
    return "@" in value and "." in value.split("@")[-1]


def _normalize_contact(raw: str) -> tuple[str | None, str | None, str | None]:
    """Return (normalized_contact, channel, error). channel is 'email' or 'sms'."""
    if not raw or not raw.strip():
        return None, None, "phone_or_email is required"
    raw = raw.strip()
    if _is_email(raw):
        return raw.lower(), "email", None
    ok, err = PhoneValidator.validate(raw)
    if not ok:
        return None, None, err
    return PhoneValidator.normalize(raw), "sms", None


def _deliver_otp(contact: str, channel: str, code: str) -> bool:
    if channel == "email":
        return EmailService.send_otp_email(contact, code)
    return SMSService.send_otp_sms(contact, code)


# ── Task 34: OTP request ─────────────────────────────────────────────────────
@auth_bp.route("/otp-request", methods=["POST"])
def otp_request():
    body = request.get_json(silent=True) or {}
    raw_contact = body.get("phone_or_email", "")
    purpose = body.get("purpose", "login")

    contact, channel, err = _normalize_contact(raw_contact)
    if err:
        return _json_error("INVALID_CONTACT", err, 400)

    type_map = {
        "login": OTPRequestType.MASTER_LOGIN.value,
        "setup": OTPRequestType.MASTER_SETUP.value,
        "verification": OTPRequestType.VOLUNTEER_REGISTRATION.value,
    }
    request_type = type_map.get(purpose, OTPRequestType.MASTER_LOGIN.value)

    try:
        otp = OTPService.generate(contact, request_type)
    except RateLimitExceeded as exc:
        record_audit("otp_request_rate_limited", "otp", contact, status="failure", notes=str(exc))
        return _json_error("RATE_LIMITED", str(exc), 429)

    delivered = _deliver_otp(contact, channel, otp.otp_code)
    record_audit("otp_requested", "otp", contact, status="success" if delivered else "failure",
                 notes=f"purpose={purpose} channel={channel}")

    if not delivered:
        return _json_error("DELIVERY_FAILED", "Could not deliver OTP. Try again.", 502)

    return jsonify({
        "success": True,
        "message": "OTP sent",
        "channel": channel,
        "expires_in": current_app.config["OTP_TTL_MINUTES"] * 60,
    })


# ── Task 35: OTP verify ──────────────────────────────────────────────────────
@auth_bp.route("/otp-verify", methods=["POST"])
def otp_verify():
    body = request.get_json(silent=True) or {}
    raw_contact = body.get("phone_or_email", "")
    code = str(body.get("otp_code", "")).strip()

    contact, _channel, err = _normalize_contact(raw_contact)
    if err:
        return _json_error("INVALID_CONTACT", err, 400)
    if not code:
        return _json_error("MISSING_OTP", "otp_code is required", 400)

    result = OTPService.verify(contact, code)
    if not result.success:
        status = 429 if result.locked else 401
        record_audit("otp_verify_failed", "otp", contact, status="failure", notes=result.message)
        return _json_error("OTP_INVALID", result.message, status)

    # OTP valid — find the user and issue a session (if they exist).
    user = _find_user_by_contact(contact)
    if user is None:
        record_audit("otp_verified_no_user", "otp", contact, status="success")
        return jsonify({
            "success": True,
            "verified": True,
            "message": "OTP verified. No account linked yet — complete setup or registration.",
        })

    if isinstance(user, Volunteer) and not user.is_approved:
        return _json_error("PENDING_APPROVAL", "Your volunteer account is pending approval.", 403)

    session = _issue_session(user)
    record_audit("login_success", "user", user.id, actor_user_id=user.id)
    return jsonify({
        "success": True,
        "verified": True,
        "token": session.token,
        "user_type": session.user_type,
        "permissions": session.permissions_json,
    })


# ── Task 36: Master setup (dual OTP, or open when bypass enabled) ─────────────
@auth_bp.route("/master-setup", methods=["POST"])
def master_setup():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    raw_phone = (body.get("phone") or "").strip()
    event_id = (body.get("event_id") or "").strip()

    if not email or not _is_email(email):
        return _json_error("INVALID_EMAIL", "A valid email is required", 400)
    ok, err = PhoneValidator.validate(raw_phone)
    if not ok:
        return _json_error("INVALID_PHONE", err, 400)
    phone = PhoneValidator.normalize(raw_phone)

    # Validate the 2-digit event id the master wants to create.
    ok, err = validate_event_id(event_id)
    if not ok:
        return _json_error("INVALID_EVENT_ID", err, 400)

    bypass = current_app.config.get("AUTH_BYPASS_OTP", False)

    # Bypass mode: if this email/phone is already a master, log them back in.
    if bypass:
        existing = _find_user_by_contact(email) or _find_user_by_contact(phone)
        if isinstance(existing, MasterUser):
            session = _issue_session(existing)
            return jsonify({
                "success": True,
                "token": session.token,
                "user": {"id": existing.id, "email": existing.email, "phone": existing.phone,
                         "type": "master_user", "event_id": existing.event_id},
                "permissions": session.permissions_json,
            }), 200

    # Event ID must be unique — a master creates a brand-new event.
    if db.session.get(Event, event_id) is not None:
        return _json_error("EVENT_EXISTS", f"Event ID '{event_id}' already exists. Choose another.", 409)

    # Enforce total-user cap.
    from app.services.limits import enforce_user_cap
    cap_error = enforce_user_cap()
    if cap_error:
        return cap_error

    # Normal mode: both OTPs must verify.
    if not bypass:
        otp_email = str(body.get("otp_email", "")).strip()
        otp_phone = str(body.get("otp_phone", "")).strip()
        email_result = OTPService.verify(email, otp_email)
        if not email_result.success:
            return _json_error("EMAIL_OTP_INVALID", f"Email OTP: {email_result.message}", 401)
        phone_result = OTPService.verify(phone, otp_phone)
        if not phone_result.success:
            return _json_error("PHONE_OTP_INVALID", f"Phone OTP: {phone_result.message}", 401)

    # Create the event, then the master bound to it.
    event = Event(id=event_id, name=body.get("event_name", f"Event {event_id}"))
    db.session.add(event)
    master = MasterUser(name=body.get("name", "Master User"), email=email, phone=phone, event_id=event_id)
    db.session.add(master)
    db.session.commit()

    session = _issue_session(master)
    record_audit("master_user_created", "user", master.id, actor_user_id=master.id,
                 notes=f"event_id={event_id}" + (" otp_bypassed" if bypass else ""))

    return jsonify({
        "success": True,
        "token": session.token,
        "user": {"id": master.id, "email": master.email, "phone": master.phone,
                 "type": "master_user", "event_id": master.event_id},
        "permissions": session.permissions_json,
    }), 201


# ── Task 37: Login (OTP send, or direct session when bypass enabled) ─────────
@auth_bp.route("/login", methods=["POST"])
def login():
    body = request.get_json(silent=True) or {}
    contact, channel, err = _normalize_contact(body.get("phone_or_email", ""))
    if err:
        return _json_error("INVALID_CONTACT", err, 400)

    user = _find_user_by_contact(contact)
    bypass = current_app.config.get("AUTH_BYPASS_OTP", False)

    if bypass:
        # No OTP: log the user straight in if they exist.
        if user is None:
            return _json_error(
                "NO_ACCOUNT",
                "No account found. Register as master or volunteer first.",
                404,
            )
        if isinstance(user, Volunteer) and not user.is_approved:
            return _json_error("PENDING_APPROVAL", "Your volunteer account is pending approval.", 403)
        session = _issue_session(user)
        record_audit("login_success", "user", user.id, actor_user_id=user.id, notes="otp_bypassed")
        return jsonify({
            "success": True,
            "token": session.token,
            "user_type": session.user_type,
            "permissions": session.permissions_json,
            "event_id": session.event_id,
        })

    # Normal mode: send an OTP (no user enumeration leak).
    if user is not None:
        if isinstance(user, Volunteer) and not user.is_approved:
            return _json_error("PENDING_APPROVAL", "Your volunteer account is pending approval.", 403)
        try:
            otp = OTPService.generate(contact, OTPRequestType.MASTER_LOGIN.value)
            _deliver_otp(contact, channel, otp.otp_code)
        except RateLimitExceeded as exc:
            return _json_error("RATE_LIMITED", str(exc), 429)
    record_audit("login_requested", "user", user.id if user else None, notes=f"channel={channel}")

    return jsonify({
        "success": True,
        "message": "If an account exists, an OTP has been sent.",
        "channel": channel,
    })


# ── Task 38: Session validate ────────────────────────────────────────────────
@auth_bp.route("/validate", methods=["GET"])
@require_auth
def validate():
    session = g.session
    user = db.session.get(User, session.user_id)
    return jsonify({
        "success": True,
        "valid": True,
        "user": {
            "id": user.id if user else session.user_id,
            "type": session.user_type,
            "email": getattr(user, "email", None),
            "phone": getattr(user, "phone", None),
            "event_id": session.event_id,
        },
        "permissions": session.permissions_json,
        "event_id": session.event_id,
    })


# ── Task 39: Logout ──────────────────────────────────────────────────────────
@auth_bp.route("/logout", methods=["POST"])
@require_auth
def logout():
    token = request.headers.get("Authorization", "")[7:].strip()
    SessionManager.revoke_session(token)
    record_audit("logout", "user", g.current_user_id, actor_user_id=g.current_user_id)
    return jsonify({"success": True, "message": "Logged out"})


# ── Internal helpers ─────────────────────────────────────────────────────────
def _find_user_by_contact(contact: str) -> User | None:
    """Match a user by email or phone (active, non-deleted)."""
    return (
        User.query_active()
        .filter((User.email == contact) | (User.phone == contact))
        .first()
    )


def _issue_session(user: User):
    permissions = getattr(user, "permissions", [])
    return SessionManager.create_session(
        user_id=user.id,
        user_type=user.type,
        permissions=permissions,
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent"),
        event_id=getattr(user, "event_id", None),
    )
