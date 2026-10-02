"""SQLAlchemy ORM models for the Event Tracker.

Importing this package registers all models with SQLAlchemy's metadata so that
`db.create_all()` and migrations can see them.
"""
from app.models.base import BaseModel, utcnow  # noqa: F401
from app.models.user import User, MasterUser, Volunteer, VolunteerStatus  # noqa: F401
from app.models.auth import OTPRequest, SessionToken, AuditLog, OTPRequestType  # noqa: F401
from app.models.guest import (  # noqa: F401
    Guest,
    GuestCategory,
    GuestStatus,
    Event,
    EventSession,
    LocationIdentifier,
    LocationType,
)
from app.models.attendance import (  # noqa: F401
    CheckInEvent,
    CheckOutEvent,
    SessionAttendance,
    IdentificationMethod,
)

__all__ = [
    "BaseModel",
    "utcnow",
    "User",
    "MasterUser",
    "Volunteer",
    "VolunteerStatus",
    "OTPRequest",
    "SessionToken",
    "AuditLog",
    "OTPRequestType",
    "Guest",
    "GuestCategory",
    "GuestStatus",
    "Event",
    "EventSession",
    "LocationIdentifier",
    "LocationType",
    "CheckInEvent",
    "CheckOutEvent",
    "SessionAttendance",
    "IdentificationMethod",
]
