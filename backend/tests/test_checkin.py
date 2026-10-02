"""Phase 6 check-in/check-out tests (Properties 5, 6, 7)."""
import pytest

from app.extensions import db
from app.models.guest import Guest, GuestStatus
from app.models.user import MasterUser, Volunteer, VolunteerStatus
from app.services.session_service import SessionManager

EVENT_ID = "demo-event"


@pytest.fixture()
def staff_token(app):
    with app.app_context():
        vol = Volunteer(name="Vol", phone="+91-9000000050",
                        approval_status=VolunteerStatus.APPROVED.value)
        db.session.add(vol)
        db.session.commit()
        return SessionManager.create_session(vol.id, "volunteer", vol.permissions).token


@pytest.fixture()
def guest_id(app):
    with app.app_context():
        guest = Guest(event_id=EVENT_ID, name="Checkin Guest", category="VIP",
                      dietary_restrictions="Vegetarian",
                      current_status=GuestStatus.NOT_CHECKED_IN.value)
        db.session.add(guest)
        db.session.commit()
        return guest.id


def _auth(t):
    return {"Authorization": f"Bearer {t}"}


# ── Auth / enforcement ───────────────────────────────────────────────────────
def test_checkin_requires_auth(client, guest_id):
    resp = client.post(f"/api/events/{EVENT_ID}/check-in", json={"guest_id": guest_id})
    assert resp.status_code == 401


# ── Task 54: check-in happy path + confirmation format ───────────────────────
def test_checkin_success(client, staff_token, guest_id):
    resp = client.post(f"/api/events/{EVENT_ID}/check-in",
                       headers=_auth(staff_token), json={"guest_id": guest_id})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["guest"]["current_status"] == "present"
    assert data["guest"]["is_vip_or_speaker"] is True          # VIP highlight
    assert data["guest"]["special_requirements"]["dietary_restrictions"] == "Vegetarian"
    assert "timestamp" in data


# ── Property 6: Check-out requires an active check-in ────────────────────────
def test_checkout_without_checkin_fails(client, staff_token, guest_id):
    resp = client.post(f"/api/events/{EVENT_ID}/check-out",
                       headers=_auth(staff_token), json={"guest_id": guest_id})
    assert resp.status_code == 409
    assert resp.get_json()["error"]["code"] == "NOT_CHECKED_IN"


def test_checkout_after_checkin_succeeds(client, staff_token, guest_id):
    client.post(f"/api/events/{EVENT_ID}/check-in", headers=_auth(staff_token), json={"guest_id": guest_id})
    resp = client.post(f"/api/events/{EVENT_ID}/check-out", headers=_auth(staff_token), json={"guest_id": guest_id})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["guest"]["current_status"] == "departed"
    assert data["duration_minutes"] is not None
    assert data["duration_minutes"] >= 0


# ── Property 7: Duration is non-negative and computed ────────────────────────
def test_duration_calculated(client, staff_token, guest_id):
    client.post(f"/api/events/{EVENT_ID}/check-in", headers=_auth(staff_token), json={"guest_id": guest_id})
    out = client.post(f"/api/events/{EVENT_ID}/check-out", headers=_auth(staff_token), json={"guest_id": guest_id})
    assert isinstance(out.get_json()["duration_minutes"], int)


# ── Task 56: Duplicate check-in detection + re-check-in ──────────────────────
def test_duplicate_checkin_warns_then_allows(client, staff_token, guest_id):
    client.post(f"/api/events/{EVENT_ID}/check-in", headers=_auth(staff_token), json={"guest_id": guest_id})
    # Second check-in without confirm -> 409 ALREADY_CHECKED_IN
    dup = client.post(f"/api/events/{EVENT_ID}/check-in", headers=_auth(staff_token), json={"guest_id": guest_id})
    assert dup.status_code == 409
    assert dup.get_json()["error"]["code"] == "ALREADY_CHECKED_IN"
    # With confirm_recheck -> allowed, includes warning
    ok = client.post(f"/api/events/{EVENT_ID}/check-in", headers=_auth(staff_token),
                     json={"guest_id": guest_id, "confirm_recheck": True})
    assert ok.status_code == 201
    assert "warning" in ok.get_json()


# ── Guest from wrong event rejected ──────────────────────────────────────────
def test_checkin_wrong_event(client, staff_token, guest_id):
    resp = client.post("/api/events/other-event/check-in",
                       headers=_auth(staff_token), json={"guest_id": guest_id})
    assert resp.status_code in (400, 404)


# ── Status endpoint ──────────────────────────────────────────────────────────
def test_status_endpoint(client, staff_token, guest_id):
    resp = client.get(f"/api/events/{EVENT_ID}/status?guest_id={guest_id}", headers=_auth(staff_token))
    assert resp.status_code == 200
    assert resp.get_json()["guest"]["guest_id"] == guest_id
