"""Check-in / check-out engine (Phase 6).

Handles the volunteer-assisted check-in and check-out transactions with
pessimistic row locking for concurrency safety, duration calculation, and
session-attendance tracking.

Concurrency (Requirement 21): on MySQL/InnoDB the guest row is locked with
SELECT ... FOR UPDATE inside the transaction, so simultaneous operations on the
same guest serialize and cannot produce duplicate or lost updates. SQLite has
no row locks; it serializes writes at the file level, which is sufficient for
local/dev correctness.
"""
import logging
from datetime import timezone

from app.extensions import db
from app.models.attendance import (
    CheckInEvent,
    CheckOutEvent,
    IdentificationMethod,
    SessionAttendance,
)
from app.models.base import utcnow
from app.models.guest import Guest, GuestStatus, LocationIdentifier
from app.models.guest import EventSession

logger = logging.getLogger(__name__)


class CheckInError(Exception):
    """Carries an error code + HTTP status for the blueprint to surface."""

    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def _aware(dt):
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _lock_guest(guest_id: str) -> Guest | None:
    """Fetch the guest row with a write lock when the backend supports it."""
    query = Guest.query.filter(Guest.id == guest_id, Guest.deleted_at.is_(None))
    if db.engine.dialect.name == "mysql":
        query = query.with_for_update()
    return query.first()


def _validate_location(event_id: str, location_id: str | None) -> None:
    """Location is optional; if given it must exist for the event."""
    if not location_id:
        return
    loc = (
        LocationIdentifier.query_active()
        .filter(LocationIdentifier.id == location_id, LocationIdentifier.event_id == event_id)
        .first()
    )
    if loc is None:
        raise CheckInError("LOCATION_NOT_FOUND", f"Location '{location_id}' not found for event", 400)


def _validate_session(event_id: str, session_id: str | None) -> None:
    if not session_id:
        return
    sess = db.session.get(EventSession, session_id)
    if sess is None or sess.event_id != event_id:
        raise CheckInError("SESSION_NOT_FOUND", f"Session '{session_id}' not found for event", 400)


def check_in(
    *,
    event_id: str,
    guest_id: str,
    volunteer_id: str,
    location_id: str | None = None,
    session_id: str | None = None,
    identification_method: str | None = None,
    confirm_recheck: bool = False,
) -> dict:
    """Perform a check-in. Returns a result dict (may include a warning)."""
    guest = _lock_guest(guest_id)
    if guest is None:
        raise CheckInError("GUEST_NOT_FOUND", "Guest not found", 404)
    if guest.event_id != event_id:
        raise CheckInError("GUEST_WRONG_EVENT", "Guest does not belong to this event", 400)

    _validate_location(event_id, location_id)
    _validate_session(event_id, session_id)

    warning = None
    # Duplicate detection (Requirement 9.11 / 22.1)
    if guest.current_status == GuestStatus.PRESENT.value:
        if not confirm_recheck:
            # Surface a warning WITHOUT recording; caller must confirm.
            last = (
                CheckInEvent.query.filter_by(guest_id=guest.id)
                .order_by(CheckInEvent.timestamp.desc())
                .first()
            )
            at = _aware(last.timestamp).strftime("%H:%M") if last else "unknown time"
            loc = last.location if last else "unknown location"
            raise CheckInError(
                "ALREADY_CHECKED_IN",
                f"Guest already checked in at {at} at {loc}. Resend with confirm_recheck=true to check in again.",
                409,
            )
        warning = "Guest was already checked in; re-check-in recorded."

    method = identification_method or IdentificationMethod.NONE.value

    event = CheckInEvent(
        guest_id=guest.id,
        event_id=event_id,
        session_id=session_id,
        timestamp=utcnow(),
        location=location_id,
        volunteer_id=volunteer_id,
        identification_method=method,
    )
    db.session.add(event)

    guest.current_status = GuestStatus.PRESENT.value
    guest.current_location = location_id

    if session_id:
        _upsert_session_attendance_checkin(session_id, guest.id, event_id, location_id, event.timestamp)

    db.session.commit()

    return {
        "checkin_id": event.id,
        "timestamp": _aware(event.timestamp).isoformat(),
        "location": location_id,
        "warning": warning,
        "guest": guest,
    }


def check_out(
    *,
    event_id: str,
    guest_id: str,
    volunteer_id: str,
    location_id: str | None = None,
    session_id: str | None = None,
) -> dict:
    """Perform a check-out. Requires an active check-in."""
    guest = _lock_guest(guest_id)
    if guest is None:
        raise CheckInError("GUEST_NOT_FOUND", "Guest not found", 404)
    if guest.event_id != event_id:
        raise CheckInError("GUEST_WRONG_EVENT", "Guest does not belong to this event", 400)

    # Must have an active check-in (Requirement 10.11 / 22.3)
    if guest.current_status != GuestStatus.PRESENT.value:
        raise CheckInError(
            "NOT_CHECKED_IN", "Guest is not currently checked in; cannot check out", 409
        )

    _validate_location(event_id, location_id)
    _validate_session(event_id, session_id)

    last_checkin = (
        CheckInEvent.query.filter_by(guest_id=guest.id, event_id=event_id)
        .order_by(CheckInEvent.timestamp.desc())
        .first()
    )
    now = utcnow()
    duration_minutes = None
    if last_checkin is not None:
        delta = now - _aware(last_checkin.timestamp)
        duration_minutes = int(delta.total_seconds() // 60)

    event = CheckOutEvent(
        guest_id=guest.id,
        event_id=event_id,
        session_id=session_id,
        timestamp=now,
        location=location_id,
        volunteer_id=volunteer_id,
        duration_minutes=duration_minutes,
    )
    db.session.add(event)

    guest.current_status = GuestStatus.DEPARTED.value
    guest.current_location = None

    if session_id:
        _close_session_attendance(session_id, guest.id, now)

    db.session.commit()

    return {
        "checkout_id": event.id,
        "timestamp": _aware(event.timestamp).isoformat(),
        "duration_minutes": duration_minutes,
        "location": location_id,
        "guest": guest,
    }


def _upsert_session_attendance_checkin(session_id, guest_id, event_id, location_id, ts):
    record = (
        SessionAttendance.query.filter_by(session_id=session_id, guest_id=guest_id).first()
    )
    if record is None:
        record = SessionAttendance(
            session_id=session_id, guest_id=guest_id, event_id=event_id,
            check_in_time=ts, location=location_id,
        )
        db.session.add(record)
    else:
        record.check_in_time = ts
        record.check_out_time = None
        record.duration_minutes = None


def _close_session_attendance(session_id, guest_id, ts):
    record = (
        SessionAttendance.query.filter_by(session_id=session_id, guest_id=guest_id).first()
    )
    if record is not None and record.check_in_time is not None:
        record.check_out_time = ts
        delta = ts - _aware(record.check_in_time)
        record.duration_minutes = int(delta.total_seconds() // 60)
