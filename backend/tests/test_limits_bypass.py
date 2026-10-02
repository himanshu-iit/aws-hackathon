"""Tests for OTP-bypass mode and capacity limits."""
import pytest

from app.extensions import db
from app.models.guest import Guest
from app.models.user import MasterUser, Volunteer, VolunteerStatus
from app.services.session_service import SessionManager, ConcurrentSessionLimitExceeded


# ── OTP bypass mode ──────────────────────────────────────────────────────────
def test_master_setup_bypass_no_otp(client, app):
    app.config["AUTH_BYPASS_OTP"] = True
    resp = client.post("/api/auth/master-setup", json={
        "email": "boss@demo.io", "phone": "+91-9811112222", "name": "Boss", "event_id": "40",
    })
    assert resp.status_code == 201
    assert resp.get_json()["token"]
    assert resp.get_json()["user"]["event_id"] == "40"


def test_login_bypass_issues_token(client, app):
    app.config["AUTH_BYPASS_OTP"] = True
    client.post("/api/auth/master-setup", json={"email": "l@demo.io", "phone": "+91-9811113333", "event_id": "41"})
    resp = client.post("/api/auth/login", json={"phone_or_email": "l@demo.io"})
    assert resp.status_code == 200
    assert resp.get_json()["token"]
    assert resp.get_json()["event_id"] == "41"


def test_volunteer_auto_approved_in_bypass(client, app):
    app.config["AUTH_BYPASS_OTP"] = True
    client.post("/api/auth/master-setup", json={"email": "vm@demo.io", "phone": "+91-9811119999", "event_id": "42"})
    resp = client.post("/api/volunteers/register", json={"name": "V", "phone": "+91-9811114444", "event_id": "42"})
    assert resp.status_code == 201
    assert resp.get_json()["status"] == "approved"


def test_login_bypass_unknown_user_404(client, app):
    app.config["AUTH_BYPASS_OTP"] = True
    resp = client.post("/api/auth/login", json={"phone_or_email": "nobody@demo.io"})
    assert resp.status_code == 404


# ── 200 total user cap ───────────────────────────────────────────────────────
def test_user_cap_blocks_registration(client, app):
    from app.models.guest import Event
    app.config["AUTH_BYPASS_OTP"] = True
    app.config["MAX_TOTAL_USERS"] = 2
    with app.app_context():
        db.session.add(Event(id="43", name="CapEvent"))
        db.session.add(MasterUser(name="M", email="m@c.io", phone="+91-9000000011", event_id="43"))
        db.session.add(Guest(event_id="43", name="G1"))
        db.session.commit()
    # Third registration should be blocked
    resp = client.post("/api/volunteers/register", json={"name": "V", "phone": "+91-9000000012", "event_id": "43"})
    assert resp.status_code == 403
    assert resp.get_json()["error"]["code"] == "USER_LIMIT_REACHED"


# ── 20 concurrent session cap ────────────────────────────────────────────────
def test_concurrent_session_cap(app):
    app.config["MAX_CONCURRENT_SESSIONS"] = 3
    with app.app_context():
        u = MasterUser(name="M", email="s@c.io", phone="+91-9000000013")
        db.session.add(u)
        db.session.commit()
        # Create up to the cap
        for _ in range(3):
            SessionManager.create_session(u.id, "master_user", [])
        # Next one exceeds the cap
        with pytest.raises(ConcurrentSessionLimitExceeded):
            SessionManager.create_session(u.id, "master_user", [])
