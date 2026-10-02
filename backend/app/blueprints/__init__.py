"""Flask blueprints for the Event Tracker API.

Phase 2 establishes the blueprint structure and the health endpoint. Feature
endpoints (auth, guests, check-in, analytics, queries) are implemented in later
phases; their blueprints are registered here as stubs so routing is wired up.
"""
from app.blueprints.health import health_bp
from app.blueprints.auth import auth_bp
from app.blueprints.volunteers import volunteers_bp
from app.blueprints.guests import guests_bp
from app.blueprints.checkin import checkin_bp
from app.blueprints.events import events_bp
from app.blueprints.analytics import analytics_bp
from app.blueprints.queries import queries_bp

ALL_BLUEPRINTS = [
    health_bp,
    auth_bp,
    volunteers_bp,
    guests_bp,
    checkin_bp,
    events_bp,
    analytics_bp,
    queries_bp,
]


def register_blueprints(app) -> None:
    for bp in ALL_BLUEPRINTS:
        app.register_blueprint(bp)
