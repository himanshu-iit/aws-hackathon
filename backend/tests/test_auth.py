"""Phase 4 auth endpoint tests + Property 1 (OTP round trip)."""
import json

from app.extensions import db
from app.models.auth import OTPRequest
from app.models.user import MasterUser, Volunteer, VolunteerStatus


def _latest_otp_code(contact: str) -> str:
    otp = (
        OTPRequest.query.filter_by(phone_or_email=contact, verified=False)
        .order_by(OTPRequest.created_at.desc())
        .first()
    )
    return otp.otp_code


# ── Property 1: OTP Validation Round Trip ────────────────────────────────────
def test_otp_round_trip_master_setup(client, app):
    """Generate OTP for email+phone, verify with correct codes, create master."""
    # Request OTPs
    client.post("/api/auth/otp-request", json={"phone_or_email": "boss@example.com", "purpose": "setup"})
    client.post("/api/auth/otp-request", json={"phone_or_email": "+91-9876543210", "purpose": "setup"})

    with app.app_context():
        email_code = _latest_otp_code("boss@example.com")
        phone_code = _latest_otp_code("+91-9876543210")

    resp = client.post("/api/auth/master-setup", json={
        "email": "boss@example.com",
        "phone": "+91-9876543210",
        "event_id": "10",
        "otp_email": email_code,
        "otp_phone": phone_code,
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["success"] is True
    assert "token" in data
    assert data["user"]["type"] == "master_user"


def test_otp_verify_wrong_code_rejected(client, app):
    client.post("/api/auth/otp-request", json={"phone_or_email": "x@example.com", "purpose": "login"})
    resp = client.post("/api/auth/otp-verify", json={"phone_or_email": "x@example.com", "otp_code": "000000"})
    assert resp.status_code in (401, 429)
    assert resp.get_json()["success"] is False


def test_otp_request_rejects_bad_phone(client):
    resp = client.post("/api/auth/otp-request", json={"phone_or_email": "+91-123"})
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "INVALID_CONTACT"


# ── Master setup: duplicate event id rejected ────────────────────────────────
def test_master_setup_duplicate_event_rejected(client, app):
    from app.models.guest import Event
    with app.app_context():
        db.session.add(Event(id="20", name="Taken"))
        db.session.commit()
    resp = client.post("/api/auth/master-setup", json={
        "email": "new@x.com", "phone": "+91-9999999999", "event_id": "20",
        "otp_email": "1", "otp_phone": "2",
    })
    assert resp.status_code == 409
    assert resp.get_json()["error"]["code"] == "EVENT_EXISTS"


def test_master_setup_rejects_bad_event_id(client):
    resp = client.post("/api/auth/master-setup", json={
        "email": "x@x.com", "phone": "+91-9999999999", "event_id": "ABC",
        "otp_email": "1", "otp_phone": "2",
    })
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "INVALID_EVENT_ID"


# ── Protected routes require auth ────────────────────────────────────────────
def test_validate_requires_token(client):
    resp = client.get("/api/auth/validate")
    assert resp.status_code == 401


def test_volunteer_list_requires_master(client):
    resp = client.get("/api/volunteers")
    assert resp.status_code == 401


# ── Volunteer registration + approval flow ───────────────────────────────────
def test_volunteer_registration_and_approval(client, app):
    from app.models.guest import Event
    with app.app_context():
        db.session.add(Event(id="30", name="VolEvent"))
        db.session.commit()
    # Register volunteer into the existing event
    reg = client.post("/api/volunteers/register", json={
        "name": "Vol One", "phone": "+91-9000000001", "email": "vol1@x.com", "event_id": "30"
    })
    assert reg.status_code == 201
    vol_id = reg.get_json()["volunteer_id"]

    # Create a master (same event) + session to approve
    with app.app_context():
        master = MasterUser(name="M", email="m@x.com", phone="+91-9000000009", event_id="30")
        db.session.add(master)
        db.session.commit()
        from app.services.session_service import SessionManager
        token = SessionManager.create_session(master.id, "master_user", ["volunteer_approval"], event_id="30").token

    approve = client.put(
        f"/api/volunteers/{vol_id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert approve.status_code == 200
    assert approve.get_json()["volunteer"]["status"] == "approved"

    with app.app_context():
        v = db.session.get(Volunteer, vol_id)
        assert v.approval_status == VolunteerStatus.APPROVED.value


def test_duplicate_volunteer_rejected(client, app):
    from app.models.guest import Event
    with app.app_context():
        db.session.add(Event(id="31", name="DupEvent"))
        db.session.commit()
    client.post("/api/volunteers/register", json={"name": "Dup", "phone": "+91-9000000002", "event_id": "31"})
    dup = client.post("/api/volunteers/register", json={"name": "Dup2", "phone": "+91-9000000002", "event_id": "31"})
    assert dup.status_code == 409


def test_volunteer_register_nonexistent_event_rejected(client):
    resp = client.post("/api/volunteers/register", json={"name": "V", "phone": "+91-9000000003", "event_id": "99"})
    assert resp.status_code == 404
    assert resp.get_json()["error"]["code"] == "EVENT_NOT_FOUND"
