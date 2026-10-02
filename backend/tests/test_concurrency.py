"""Task 106 / Property 5 — check-in concurrency safety.

Note: the suite uses in-memory SQLite which serializes writes, so this verifies
logical correctness (exactly N distinct check-in records, no duplicates, final
state consistent) rather than true parallel contention. Real row-level locking
(SELECT FOR UPDATE) is exercised on MySQL/RDS in production.
"""
from app.extensions import db
from app.models.attendance import CheckInEvent
from app.models.guest import Event, Guest, GuestStatus
from app.models.user import Volunteer, VolunteerStatus
from app.services.checkin_service import check_in


def _setup(app, n):
    with app.app_context():
        if db.session.get(Event, "demo-event") is None:
            db.session.add(Event(id="demo-event", name="Demo"))
        vol = Volunteer(name="V", phone="+91-9600000000", approval_status=VolunteerStatus.APPROVED.value)
        db.session.add(vol)
        db.session.commit()
        vol_id = vol.id
        gids = []
        for i in range(n):
            g = Guest(event_id="demo-event", name=f"G{i}", current_status=GuestStatus.NOT_CHECKED_IN.value)
            db.session.add(g)
            db.session.flush()
            gids.append(g.id)
        db.session.commit()
        return vol_id, gids


def test_n_checkins_create_n_records(app):
    """For N distinct guests checked in, exactly N check-in records exist."""
    n = 50
    with app.app_context():
        vol_id, gids = _setup(app, n)
        for gid in gids:
            check_in(event_id="demo-event", guest_id=gid, volunteer_id=vol_id)

        count = CheckInEvent.query.filter_by(event_id="demo-event").count()
        assert count == n
        # Every guest is now present
        present = Guest.query.filter_by(event_id="demo-event", current_status="present").count()
        assert present == n


def test_duplicate_checkin_no_second_record_without_confirm(app):
    """A duplicate check-in without confirm raises and creates no 2nd record."""
    from app.services.checkin_service import CheckInError

    with app.app_context():
        vol_id, gids = _setup(app, 1)
        gid = gids[0]
        check_in(event_id="demo-event", guest_id=gid, volunteer_id=vol_id)
        try:
            check_in(event_id="demo-event", guest_id=gid, volunteer_id=vol_id)
            assert False, "expected CheckInError"
        except CheckInError as e:
            assert e.code == "ALREADY_CHECKED_IN"
        assert CheckInEvent.query.filter_by(guest_id=gid).count() == 1
