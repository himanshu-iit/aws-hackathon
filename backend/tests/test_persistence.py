"""Property 13: Data Persistence (Requirements 24.1-24.3).

Verifies that a persisted entity can be retrieved with identical field values
within the same database — the in-process analogue of surviving a restart.
"""
from app.extensions import db
from app.models.guest import Guest, GuestCategory, GuestStatus


def test_guest_round_trip(app):
    with app.app_context():
        guest = Guest(
            event_id="evt-1",
            name="Ada Lovelace",
            email="ada@example.com",
            phone="+44-7700900000",
            company="Analytical Engines",
            profession="Mathematician",
            category=GuestCategory.SPEAKER.value,
        )
        db.session.add(guest)
        db.session.commit()
        guest_id = guest.id

        # Clear identity map so we fetch fresh from the DB
        db.session.expunge_all()

        fetched = db.session.get(Guest, guest_id)
        assert fetched is not None
        assert fetched.name == "Ada Lovelace"
        assert fetched.email == "ada@example.com"
        assert fetched.phone == "+44-7700900000"
        assert fetched.category == GuestCategory.SPEAKER.value
        assert fetched.current_status == GuestStatus.NOT_CHECKED_IN.value


def test_soft_delete_excluded_from_active_query(app):
    with app.app_context():
        g = Guest(event_id="evt-1", name="Temp Guest")
        db.session.add(g)
        db.session.commit()
        g.soft_delete()
        db.session.commit()

        assert Guest.query_active().filter_by(id=g.id).first() is None
        assert db.session.get(Guest, g.id) is not None  # still physically present
