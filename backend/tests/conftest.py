"""Shared pytest fixtures."""
import pytest
from sqlalchemy import event as sa_event

from app.factory import create_app
from app.extensions import db as _db


@pytest.fixture()
def app():
    app = create_app("testing")
    with app.app_context():
        # Enforce foreign keys in SQLite so tests catch FK violations the way
        # MySQL (production) does.
        engine = _db.engine

        @sa_event.listens_for(engine, "connect")
        def _fk_pragma(dbapi_conn, _rec):  # noqa: ANN001
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

        _db.create_all()
        _seed_event()
        yield app
        _db.session.remove()
        _db.drop_all()


def _seed_event():
    """Seed the demo event the guest tests reference."""
    from app.models.guest import Event

    if _db.session.get(Event, "demo-event") is None:
        _db.session.add(Event(id="demo-event", name="Demo Event"))
        _db.session.commit()


@pytest.fixture()
def client(app):
    return app.test_client()
