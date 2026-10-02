"""Guest, Event, EventSession, and Location models."""
import enum

from app.extensions import db
from app.models.base import BaseModel


class GuestCategory(str, enum.Enum):
    GENERAL_ATTENDEE = "General_Attendee"
    VIP = "VIP"
    SPEAKER = "Speaker"
    STAFF = "Staff"
    VOLUNTEER = "Volunteer"
    PRESS = "Press"
    SPONSOR = "Sponsor"


class GuestStatus(str, enum.Enum):
    NOT_CHECKED_IN = "not_checked_in"
    PRESENT = "present"
    DEPARTED = "departed"


class LocationType(str, enum.Enum):
    ENTRANCE = "entrance"
    SESSION_ROOM = "session_room"
    EXIT = "exit"
    OTHER = "other"


class Event(BaseModel):
    """An event that guests register for and attend."""

    __tablename__ = "events"

    name = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    capacity = db.Column(db.Integer, nullable=True)
    created_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    settings = db.Column(db.JSON, nullable=True)


class LocationIdentifier(BaseModel):
    """A named physical location within an event venue."""

    __tablename__ = "locations"

    event_id = db.Column(db.String(36), db.ForeignKey("events.id"), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    capacity = db.Column(db.Integer, nullable=True)
    location_type = db.Column(db.String(20), nullable=False, default=LocationType.OTHER.value)


class EventSession(BaseModel):
    """A scheduled track/segment within an event."""

    __tablename__ = "event_sessions"

    event_id = db.Column(db.String(36), db.ForeignKey("events.id"), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    scheduled_start = db.Column(db.DateTime, nullable=True)
    scheduled_end = db.Column(db.DateTime, nullable=True)
    location_id = db.Column(db.String(36), db.ForeignKey("locations.id"), nullable=True)
    created_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)


class Guest(BaseModel):
    """An attendee registered by a Master user or Volunteer."""

    __tablename__ = "guests"

    event_id = db.Column(db.String(36), db.ForeignKey("events.id"), nullable=False, index=True)

    # Personal details
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True, index=True)

    # Professional details
    company = db.Column(db.String(255), nullable=True)
    job_title = db.Column(db.String(255), nullable=True)
    profession = db.Column(db.String(255), nullable=True)

    # Emergency contact
    emergency_contact_name = db.Column(db.String(255), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)

    # Event-specific
    ticket_number = db.Column(db.String(100), nullable=True, index=True)
    badge_number = db.Column(db.String(100), nullable=True, index=True)
    category = db.Column(
        db.String(32), nullable=False, default=GuestCategory.GENERAL_ATTENDEE.value, index=True
    )

    # Special requirements
    dietary_restrictions = db.Column(db.String(500), nullable=True)
    accessibility_needs = db.Column(db.String(500), nullable=True)

    # Live attendance state
    current_status = db.Column(
        db.String(20), nullable=False, default=GuestStatus.NOT_CHECKED_IN.value, index=True
    )
    current_location = db.Column(db.String(100), nullable=True)

    registered_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    guest_metadata = db.Column(db.JSON, nullable=True)
