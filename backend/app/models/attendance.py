"""Check-in / check-out events and per-session attendance records."""
import enum

from app.extensions import db
from app.models.base import BaseModel, utcnow


class IdentificationMethod(str, enum.Enum):
    NAME_SEARCH = "name_search"
    TICKET = "ticket"
    BADGE = "badge"
    NONE = "none"  # identification is optional per spec clarification


class CheckInEvent(BaseModel):
    """Record of a guest arrival, created by a Volunteer."""

    __tablename__ = "check_in_events"

    guest_id = db.Column(db.String(36), db.ForeignKey("guests.id"), nullable=False, index=True)
    event_id = db.Column(db.String(36), db.ForeignKey("events.id"), nullable=False, index=True)
    session_id = db.Column(db.String(36), db.ForeignKey("event_sessions.id"), nullable=True)
    timestamp = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)
    location = db.Column(db.String(100), nullable=True)
    volunteer_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    identification_method = db.Column(
        db.String(20), nullable=True, default=IdentificationMethod.NONE.value
    )
    notes = db.Column(db.String(500), nullable=True)

    __table_args__ = (
        db.Index("ix_checkin_guest_event_time", "guest_id", "event_id", "timestamp"),
    )


class CheckOutEvent(BaseModel):
    """Record of a guest departure, created by a Volunteer."""

    __tablename__ = "check_out_events"

    guest_id = db.Column(db.String(36), db.ForeignKey("guests.id"), nullable=False, index=True)
    event_id = db.Column(db.String(36), db.ForeignKey("events.id"), nullable=False, index=True)
    session_id = db.Column(db.String(36), db.ForeignKey("event_sessions.id"), nullable=True)
    timestamp = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)
    location = db.Column(db.String(100), nullable=True)
    volunteer_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    duration_minutes = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.String(500), nullable=True)

    __table_args__ = (
        db.Index("ix_checkout_guest_event_time", "guest_id", "event_id", "timestamp"),
    )


class SessionAttendance(BaseModel):
    """A guest's participation record for a specific session."""

    __tablename__ = "session_attendance"

    session_id = db.Column(
        db.String(36), db.ForeignKey("event_sessions.id"), nullable=False, index=True
    )
    guest_id = db.Column(db.String(36), db.ForeignKey("guests.id"), nullable=False, index=True)
    event_id = db.Column(db.String(36), db.ForeignKey("events.id"), nullable=False, index=True)
    check_in_time = db.Column(db.DateTime, nullable=True)
    check_out_time = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)
    location = db.Column(db.String(100), nullable=True)

    __table_args__ = (
        db.UniqueConstraint("session_id", "guest_id", name="uq_session_guest"),
        db.Index("ix_attendance_session_guest", "session_id", "guest_id", "event_id"),
    )
