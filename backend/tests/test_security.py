"""Task 108 — security tests (RBAC, sessions, injection, unauthorized access)."""
from datetime import timedelta

from app.extensions import db
from app.models.base import utcnow
from app.models.guest import Event, Guest
from app.models.user import MasterUser, Volunteer, VolunteerStatus
from app.services.session_service import SessionManager


def _master(app):
    with app.app_context():
        m = MasterUser(name="M", email="sec-m@x.io", phone="+91-9500000001")
        db.session.add(m)
        db.session.commit()
        return m.id, SessionManager.create_session(m.id, "master_user", m.permissions).token


def _volunteer(app):
    with app.app_context():
        v = Volunteer(name="V", phone="+91-9500000002", approval_status=VolunteerStatus.APPROVED.value)
        db.session.add(v)
        db.session.commit()
        return v.id, SessionManager.create_session(v.id, "volunteer", v.permissions).token


# ── Unauthorized access ──────────────────────────────────────────────────────
def test_no_token_rejected(client):
    assert client.get("/api/auth/validate").status_code == 401
    assert client.get("/api/guests").status_code == 401
    assert client.get("/api/events/demo-event/dashboard").status_code == 401


def test_garbage_token_rejected(client):
    h = {"Authorization": "Bearer not-a-real-token"}
    assert client.get("/api/auth/validate", headers=h).status_code == 401


# ── RBAC: volunteer cannot do master-only actions ────────────────────────────
def test_volunteer_cannot_list_volunteers(client, app):
    _vid, vtoken = _volunteer(app)
    resp = client.get("/api/volunteers", headers={"Authorization": f"Bearer {vtoken}"})
    assert resp.status_code == 403


def test_volunteer_cannot_delete_guest(client, app):
    _mid, mtoken = _master(app)
    _vid, vtoken = _volunteer(app)
    with app.app_context():
        if db.session.get(Event, "demo-event") is None:
            db.session.add(Event(id="demo-event", name="Demo"))
            db.session.commit()
        g = Guest(event_id="demo-event", name="Victim")
        db.session.add(g)
        db.session.commit()
        gid = g.id
    resp = client.delete(f"/api/guests/{gid}", headers={"Authorization": f"Bearer {vtoken}"})
    assert resp.status_code == 403


# ── Session expiry + revocation ──────────────────────────────────────────────
def test_expired_session_rejected(client, app):
    with app.app_context():
        m = MasterUser(name="E", email="exp@x.io", phone="+91-9500000003")
        db.session.add(m)
        db.session.commit()
        s = SessionManager.create_session(m.id, "master_user", [])
        s.expires_at = utcnow() - timedelta(hours=1)  # force-expire
        db.session.commit()
        token = s.token
    assert client.get("/api/auth/validate", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_revoked_session_rejected(client, app):
    _mid, token = _master(app)
    h = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/auth/validate", headers=h).status_code == 200
    client.post("/api/auth/logout", headers=h)  # revoke
    assert client.get("/api/auth/validate", headers=h).status_code == 401


# ── SQL injection safety (ORM parameterizes) ─────────────────────────────────
def test_sql_injection_in_search_is_safe(client, app):
    _mid, token = _master(app)
    h = {"Authorization": f"Bearer {token}"}
    with app.app_context():
        if db.session.get(Event, "demo-event") is None:
            db.session.add(Event(id="demo-event", name="Demo"))
            db.session.commit()
    # Malicious input must not error or drop tables — just returns no matches.
    resp = client.get("/api/guests/search?name=' OR '1'='1'; DROP TABLE guests;--&event_id=demo-event", headers=h)
    assert resp.status_code == 200
    # Table still intact: a normal query still works
    assert client.get("/api/guests", headers=h).status_code == 200
