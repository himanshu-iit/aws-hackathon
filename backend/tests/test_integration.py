"""Task 105 — full end-to-end workflow integration tests."""
from app.extensions import db
from app.models.guest import Event


def test_full_master_to_checkout_flow(client, app):
    """Master setup (creates event) → register guest → check-in → check-out."""
    app.config["AUTH_BYPASS_OTP"] = True
    ev = "50"

    # 1. Master setup creates event 50
    setup = client.post("/api/auth/master-setup", json={
        "email": "flow-master@evt.io", "phone": "+91-9700000001", "name": "Flow Master", "event_id": ev,
    })
    assert setup.status_code == 201
    token = setup.get_json()["token"]
    h = {"Authorization": f"Bearer {token}"}

    # 2. Validate session carries the event
    v = client.get("/api/auth/validate", headers=h)
    assert v.status_code == 200
    assert v.get_json()["event_id"] == ev

    # 3. Register guest (event taken from session)
    reg = client.post("/api/guests", headers=h, json={
        "name": "Flow Guest", "phone": "+91-9700000050", "category": "VIP",
    })
    assert reg.status_code == 201
    guest_id = reg.get_json()["guest"]["guest_id"]

    # 4. Check in
    ci = client.post(f"/api/events/{ev}/check-in", headers=h, json={"guest_id": guest_id})
    assert ci.status_code == 201
    assert ci.get_json()["guest"]["current_status"] == "present"

    # 5. Dashboard reflects the present guest
    dash = client.get(f"/api/events/{ev}/dashboard", headers=h).get_json()
    assert dash["current_present"] >= 1

    # 6. Check out
    co = client.post(f"/api/events/{ev}/check-out", headers=h, json={"guest_id": guest_id})
    assert co.status_code == 200
    assert co.get_json()["guest"]["current_status"] == "departed"
    assert co.get_json()["duration_minutes"] is not None


def test_volunteer_register_login_checkin_flow(client, app):
    """Master creates event → volunteer joins → login → check in a guest."""
    app.config["AUTH_BYPASS_OTP"] = True
    ev = "51"
    client.post("/api/auth/master-setup", json={
        "email": "vflow-master@evt.io", "phone": "+91-9700000009", "event_id": ev,
    })

    # Volunteer registers into the existing event (auto-approved in bypass)
    reg = client.post("/api/volunteers/register", json={
        "name": "Flow Vol", "phone": "+91-9700000002", "event_id": ev,
    })
    assert reg.status_code == 201
    assert reg.get_json()["status"] == "approved"

    # Volunteer logs in
    login = client.post("/api/auth/login", json={"phone_or_email": "+91-9700000002"})
    assert login.status_code == 200
    assert login.get_json()["event_id"] == ev
    vh = {"Authorization": f"Bearer {login.get_json()['token']}"}

    # Volunteer registers + checks in a guest
    guest_id = client.post("/api/guests", headers=vh, json={"name": "Vol Guest"}).get_json()["guest"]["guest_id"]
    ci = client.post(f"/api/events/{ev}/check-in", headers=vh, json={"guest_id": guest_id})
    assert ci.status_code == 201


def test_analytics_after_activity(client, app):
    """Register + check in a few guests, verify analytics reflects it."""
    app.config["AUTH_BYPASS_OTP"] = True
    ev = "52"
    token = client.post("/api/auth/master-setup", json={
        "email": "an-master@evt.io", "phone": "+91-9700000003", "event_id": ev,
    }).get_json()["token"]
    h = {"Authorization": f"Bearer {token}"}

    for i in range(3):
        gid = client.post("/api/guests", headers=h, json={
            "name": f"A{i}", "category": "Speaker",
        }).get_json()["guest"]["guest_id"]
        client.post(f"/api/events/{ev}/check-in", headers=h, json={"guest_id": gid})

    report = client.get(f"/api/events/{ev}/analytics", headers=h).get_json()
    assert report["total_checked_in"] >= 3
    assert report["peak_attendance"] >= 1

    cats = client.get(f"/api/events/{ev}/analytics/categories", headers=h).get_json()
    assert any(c["category"] == "Speaker" for c in cats["categories"])
