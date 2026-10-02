"""Phase 5 guest management endpoint tests."""
import pytest

from app.extensions import db
from app.models.guest import Guest, GuestStatus
from app.models.user import MasterUser, Volunteer, VolunteerStatus
from app.services.session_service import SessionManager

EVENT_ID = "demo-event"


@pytest.fixture()
def master_token(app):
    with app.app_context():
        master = MasterUser(name="M", email="m@x.com", phone="+91-9000000000")
        db.session.add(master)
        db.session.commit()
        return SessionManager.create_session(master.id, "master_user", master.permissions).token


@pytest.fixture()
def volunteer_token(app):
    with app.app_context():
        vol = Volunteer(
            name="V", phone="+91-9000000001",
            approval_status=VolunteerStatus.APPROVED.value,
        )
        db.session.add(vol)
        db.session.commit()
        return SessionManager.create_session(vol.id, "volunteer", vol.permissions).token


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ── Auth gating ──────────────────────────────────────────────────────────────
def test_register_requires_auth(client):
    resp = client.post("/api/guests", json={"name": "X", "event_id": EVENT_ID})
    assert resp.status_code == 401


# ── Task 45: registration ────────────────────────────────────────────────────
def test_register_guest_success(client, master_token):
    resp = client.post("/api/guests", headers=_auth(master_token), json={
        "name": "Grace Hopper",
        "email": "grace@navy.mil",
        "phone": "+91-2025550143",
        "company": "US Navy",
        "profession": "Computer Scientist",
        "category": "Speaker",
        "event_id": EVENT_ID,
    })
    assert resp.status_code == 201
    guest = resp.get_json()["guest"]
    assert guest["name"] == "Grace Hopper"
    assert guest["phone"] == "+91-2025550143"
    assert guest["category"] == "Speaker"
    assert guest["current_status"] == GuestStatus.NOT_CHECKED_IN.value


def test_register_missing_name_fails(client, master_token):
    resp = client.post("/api/guests", headers=_auth(master_token), json={"event_id": EVENT_ID})
    assert resp.status_code == 400
    assert "name" in resp.get_json()["error"]["details"]


def test_register_invalid_phone_fails(client, master_token):
    resp = client.post("/api/guests", headers=_auth(master_token), json={
        "name": "Bad Phone", "phone": "+1-123", "event_id": EVENT_ID,
    })
    assert resp.status_code == 400
    assert "phone" in resp.get_json()["error"]["details"]


def test_register_invalid_category_fails(client, master_token):
    resp = client.post("/api/guests", headers=_auth(master_token), json={
        "name": "Bad Cat", "category": "Alien", "event_id": EVENT_ID,
    })
    assert resp.status_code == 400
    assert "category" in resp.get_json()["error"]["details"]


def test_duplicate_phone_same_event_rejected(client, master_token):
    payload = {"name": "Dup", "phone": "+91-9988776655", "event_id": EVENT_ID}
    assert client.post("/api/guests", headers=_auth(master_token), json=payload).status_code == 201
    dup = client.post("/api/guests", headers=_auth(master_token), json=payload)
    assert dup.status_code == 409


def test_volunteer_can_register(client, volunteer_token):
    resp = client.post("/api/guests", headers=_auth(volunteer_token), json={
        "name": "By Volunteer", "event_id": EVENT_ID,
    })
    assert resp.status_code == 201


# ── Task 47: search ──────────────────────────────────────────────────────────
def test_search_by_name_substring(client, master_token):
    for n in ["Alice Smith", "Bob Jones", "Alicia Keys"]:
        client.post("/api/guests", headers=_auth(master_token), json={"name": n, "event_id": EVENT_ID})
    resp = client.get(f"/api/guests/search?name=ali&event_id={EVENT_ID}", headers=_auth(master_token))
    assert resp.status_code == 200
    names = [g["name"] for g in resp.get_json()["guests"]]
    assert "Alice Smith" in names and "Alicia Keys" in names
    assert "Bob Jones" not in names


# ── Task 49: update ──────────────────────────────────────────────────────────
def test_update_guest_fields(client, master_token):
    created = client.post("/api/guests", headers=_auth(master_token), json={
        "name": "Original", "phone": "+91-9111111111", "event_id": EVENT_ID,
    }).get_json()["guest"]
    gid = created["guest_id"]

    resp = client.put(f"/api/guests/{gid}", headers=_auth(master_token), json={
        "name": "Updated Name", "company": "NewCo",
    })
    assert resp.status_code == 200
    assert resp.get_json()["guest"]["name"] == "Updated Name"
    assert resp.get_json()["guest"]["company"] == "NewCo"


def test_update_phone_immutable(client, master_token):
    created = client.post("/api/guests", headers=_auth(master_token), json={
        "name": "Phone Lock", "phone": "+91-9222222222", "event_id": EVENT_ID,
    }).get_json()["guest"]
    gid = created["guest_id"]

    resp = client.put(f"/api/guests/{gid}", headers=_auth(master_token), json={
        "phone": "+91-9333333333",
    })
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "PHONE_IMMUTABLE"


# ── Task 50: delete (master only) ────────────────────────────────────────────
def test_delete_guest_master_only(client, master_token, volunteer_token):
    created = client.post("/api/guests", headers=_auth(master_token), json={
        "name": "To Delete", "event_id": EVENT_ID,
    }).get_json()["guest"]
    gid = created["guest_id"]

    # Volunteer cannot delete
    assert client.delete(f"/api/guests/{gid}", headers=_auth(volunteer_token)).status_code == 403

    # Master can delete (soft)
    assert client.delete(f"/api/guests/{gid}", headers=_auth(master_token)).status_code == 200

    # Now gone from active queries
    assert client.get(f"/api/guests/{gid}", headers=_auth(master_token)).status_code == 404


# ── Property 4: Guest data persistence round-trip via API ────────────────────
def test_guest_persists_and_reads_back(client, master_token, app):
    created = client.post("/api/guests", headers=_auth(master_token), json={
        "name": "Persist Me", "email": "persist@x.com", "phone": "+44-7700900123",
        "profession": "Engineer", "category": "VIP", "event_id": EVENT_ID,
    }).get_json()["guest"]
    gid = created["guest_id"]

    fetched = client.get(f"/api/guests/{gid}", headers=_auth(master_token)).get_json()["guest"]
    assert fetched["name"] == "Persist Me"
    assert fetched["email"] == "persist@x.com"
    assert fetched["phone"] == "+44-7700900123"
    assert fetched["profession"] == "Engineer"
    assert fetched["category"] == "VIP"
