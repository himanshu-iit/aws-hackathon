"""Application factory for the Event Tracker Flask backend."""
import os

from flask import Flask
from flask_cors import CORS

from app.extensions import db, ma
from app.logging_config import configure_logging
from app.middleware import register_middleware
from config import get_config


def create_app(config_name: str | None = None) -> Flask:
    """Build and configure a Flask application instance."""
    app = Flask(__name__)

    # Load config (instantiated so SQLALCHEMY_ENGINE_OPTIONS property resolves)
    config_obj = get_config(config_name)()
    app.config.from_object(config_obj)
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = config_obj.SQLALCHEMY_ENGINE_OPTIONS

    # Logging first so later init steps are captured
    configure_logging(app)

    # Extensions
    db.init_app(app)
    ma.init_app(app)

    # CORS limited to configured origins, API routes only
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    )

    # Middleware (request id, logging, security headers, error handlers)
    register_middleware(app)

    # Models must be imported before create_all so metadata is populated
    with app.app_context():
        from app import models  # noqa: F401

        # Auto-create tables for local SQLite dev always. For MySQL/RDS, create
        # tables on startup only when AUTO_CREATE_TABLES is enabled (no Alembic
        # migration pipeline yet — that is a later phase). create_all is safe:
        # it only creates missing tables and never drops or alters existing ones.
        uri = app.config["SQLALCHEMY_DATABASE_URI"]
        auto_create = os.environ.get("AUTO_CREATE_TABLES", "false").lower() == "true"
        reset_schema = os.environ.get("RESET_SCHEMA", "false").lower() == "true"
        if uri.startswith("sqlite") or auto_create:
            try:
                if reset_schema and not uri.startswith("sqlite"):
                    # One-time destructive reset to apply schema changes on a
                    # demo DB with no migration pipeline. Drops ALL data.
                    db.drop_all()
                    app.logger.warning("RESET_SCHEMA: dropped all tables")
                db.create_all()
                app.logger.info("Database tables ensured (create_all)")
            except Exception:  # noqa: BLE001
                app.logger.exception("create_all/reset failed")

    # Blueprints
    from app.blueprints import register_blueprints

    register_blueprints(app)

    app.logger.info("Event Tracker backend initialized", extra={"env": config_name})
    return app


def _seed_demo_event(app) -> None:
    """Ensure a default demo event exists so guests can be registered before
    the event-management endpoints (a later phase) are available.

    Guests have a foreign key to events; without a parent event, registration
    fails on databases that enforce FKs (MySQL). Idempotent.
    """
    from app.models.guest import Event

    demo_id = os.environ.get("DEMO_EVENT_ID", "demo-event")
    if db.session.get(Event, demo_id) is not None:
        return
    event = Event(id=demo_id, name="Demo Event", description="Default event for testing")
    db.session.add(event)
    db.session.commit()
    app.logger.info("Seeded demo event", extra={"event_id": demo_id})
