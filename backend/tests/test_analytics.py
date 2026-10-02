"""Phase 7 & 8 dashboard + analytics endpoint tests."""
import pytest

from app.extensions import db
from app.models.guest import Guest, GuestStatus
from app.models.user import Volunteer, VolunteerStatus
from app.services.session_service import SessionManager

EVENT_ID = "demo-event"


@pytest.fixture()
def staff_token(app):
    with app.app_context():
        vol = Volunteer(name="Vol", phone="+91-9000000070",
                        approval_status=VolunteerStatus.APPROVED.value)
        db.session.add(vol)
        db.session.commit()
        return SessionManager.create_session(vol.id, "volunteer", vol.permissions).token


def _auth(t):
    return {"Authorization": f"Bearer {t}"}


def _seed_guests(app):
    with app.app_context():
        db.session.add_all([
            Guest(event_id=EVENT_ID, name="P1", category="VIP", current_status=GuestStatus.PRESENT.value),
            Guest(event_id=EVENT_ID, name="P2", category="Speaker", current_status=GuestStatus.PRESENT.value),
            Guest(event_id=EVENT_ID, name="D1", category="VIP", current_status=GuestStatus.DEPARTED.value),
            Guest(event_id=EVENT_ID, name="N1", category="General_Attendee", current_status=GuestStatus.NOT_CHECKED_IN.value),
        ])
        db.session.commit()


def test_dashboard_requires_auth(client):
    assert client.get(f"/api/events/{EVENT_ID}/dashboard").status_code == 401


def test_dashboard_metrics(client, staff_token, app):
    _seed_guests(app)
    resp = client.get(f"/api/events/{EVENT_ID}/dashboard", headers=_auth(staff_token))
    assert resp.status_code == 200
    d = resp.get_json()
    assert d["total_registered"] == 4
    assert d["current_present"] == 2
    assert d["departed"] == 1
    assert d["not_checked_in"] == 1
    assert "last_updated" in d


def test_by_category(client, staff_token, app):
    _seed_guests(app)
    resp = client.get(f"/api/events/{EVENT_ID}/analytics/by-category", headers=_auth(staff_token))
    assert resp.status_code == 200
    cats = resp.get_json()["categories"]
    assert cats["VIP"]["count"] == 2
    assert cats["Speaker"]["count"] == 1


def test_capacity_no_limit(client, staff_token, app):
    _seed_guests(app)
    resp = client.get(f"/api/events/{EVENT_ID}/capacity", headers=_auth(staff_token))
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "no_limit"


def test_analytics_summary(client, staff_token, app):
    _seed_guests(app)
    resp = client.get(f"/api/events/{EVENT_ID}/analytics", headers=_auth(staff_token))
    assert resp.status_code == 200
    d = resp.get_json()
    assert d["total_registered"] == 4
    assert "generated_at" in d


def test_category_analytics(client, staff_token, app):
    _seed_guests(app)
    resp = client.get(f"/api/events/{EVENT_ID}/analytics/categories", headers=_auth(staff_token))
    assert resp.status_code == 200
    cats = {c["category"]: c for c in resp.get_json()["categories"]}
    # VIP: 2 guests, one departed -> checkin_rate 50% (1 of 2 present/departed), checkout 50%
    assert cats["VIP"]["count"] == 2


def test_hourly_and_peak_endpoints(client, staff_token, app):
    _seed_guests(app)
    assert client.get(f"/api/events/{EVENT_ID}/analytics/hourly", headers=_auth(staff_token)).status_code == 200
    assert client.get(f"/api/events/{EVENT_ID}/analytics/peak-time", headers=_auth(staff_token)).status_code == 200
    assert client.get(f"/api/events/{EVENT_ID}/analytics/sessions", headers=_auth(staff_token)).status_code == 200
