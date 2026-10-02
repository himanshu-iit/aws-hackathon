"""Analytics and dashboard aggregation (Phases 7 & 8).

All queries run directly against RDS (no caching layer, per design). Functions
return plain dicts/lists ready for JSON serialization.
"""
from collections import defaultdict
from datetime import timezone

from sqlalchemy import func

from app.extensions import db
from app.models.attendance import CheckInEvent, CheckOutEvent, SessionAttendance
from app.models.guest import Event, EventSession, Guest, GuestCategory, GuestStatus, LocationIdentifier
from app.models.base import utcnow


def _aware(dt):
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# ── Dashboard metrics (Task 63) ──────────────────────────────────────────────
def dashboard_metrics(event_id: str) -> dict:
    base = Guest.query_active().filter(Guest.event_id == event_id)
    total = base.count()
    present = base.filter(Guest.current_status == GuestStatus.PRESENT.value).count()
    departed = base.filter(Guest.current_status == GuestStatus.DEPARTED.value).count()
    not_checked_in = base.filter(Guest.current_status == GuestStatus.NOT_CHECKED_IN.value).count()

    return {
        "event_id": event_id,
        "total_registered": total,
        "current_present": present,
        "departed": departed,
        "not_checked_in": not_checked_in,
        "peak_attendance": _peak_attendance(event_id)["peak_count"],
        "last_updated": utcnow().isoformat(),
    }


# ── Category breakdown (Task 64) ─────────────────────────────────────────────
def by_category(event_id: str) -> dict:
    rows = (
        db.session.query(Guest.category, func.count(Guest.id))
        .filter(Guest.event_id == event_id, Guest.deleted_at.is_(None))
        .group_by(Guest.category)
        .all()
    )
    total = sum(count for _, count in rows) or 1
    breakdown = {
        cat.value: {"count": 0, "percentage": 0.0} for cat in GuestCategory
    }
    for category, count in rows:
        breakdown[category] = {
            "count": count,
            "percentage": round(count * 100.0 / total, 1),
        }
    return {"event_id": event_id, "categories": breakdown}


# ── Location breakdown (Task 65) ─────────────────────────────────────────────
def by_location(event_id: str) -> dict:
    rows = (
        db.session.query(Guest.current_location, func.count(Guest.id))
        .filter(
            Guest.event_id == event_id,
            Guest.deleted_at.is_(None),
            Guest.current_status == GuestStatus.PRESENT.value,
            Guest.current_location.isnot(None),
        )
        .group_by(Guest.current_location)
        .all()
    )
    locations = {loc.id: loc for loc in LocationIdentifier.query_active().filter_by(event_id=event_id).all()}
    result = {}
    for location_id, count in rows:
        loc = locations.get(location_id)
        capacity = loc.capacity if loc else None
        result[location_id] = {
            "count": count,
            "capacity": capacity,
            "percentage": round(count * 100.0 / capacity, 1) if capacity else None,
        }
    return {"event_id": event_id, "locations": result}


# ── Capacity status (Task 67) ────────────────────────────────────────────────
def capacity_status(event_id: str) -> dict:
    event = db.session.get(Event, event_id)
    present = (
        Guest.query_active()
        .filter(Guest.event_id == event_id, Guest.current_status == GuestStatus.PRESENT.value)
        .count()
    )
    capacity = event.capacity if event else None
    pct = round(present * 100.0 / capacity, 1) if capacity else None
    if capacity is None:
        status = "no_limit"
    elif present >= capacity:
        status = "critical"
    elif present >= 0.8 * capacity:
        status = "warning"
    else:
        status = "normal"
    return {
        "event_id": event_id,
        "current_present": present,
        "capacity": capacity,
        "percentage": pct,
        "status": status,
    }


# ── Detailed attendance list (Task 66) ───────────────────────────────────────
def attendance_list(event_id: str, filters: dict, limit: int, offset: int) -> dict:
    q = Guest.query_active().filter(Guest.event_id == event_id)
    for field in ("current_status", "category", "current_location"):
        if filters.get(field):
            q = q.filter(getattr(Guest, field) == filters[field])
    total = q.count()
    rows = q.order_by(Guest.name.asc()).limit(limit).offset(offset).all()

    def latest_checkin(gid):
        ev = CheckInEvent.query.filter_by(guest_id=gid).order_by(CheckInEvent.timestamp.desc()).first()
        return _aware(ev.timestamp).isoformat() if ev else None

    return {
        "event_id": event_id,
        "total": total,
        "limit": limit,
        "offset": offset,
        "guests": [
            {
                "guest_id": g.id,
                "name": g.name,
                "category": g.category,
                "current_status": g.current_status,
                "current_location": g.current_location,
                "last_check_in": latest_checkin(g.id),
            }
            for g in rows
        ],
    }


# ── Report / analytics summary (Task 71) ─────────────────────────────────────
def analytics_summary(event_id: str) -> dict:
    checked_in = (
        db.session.query(func.count(func.distinct(CheckInEvent.guest_id)))
        .filter(CheckInEvent.event_id == event_id).scalar() or 0
    )
    checked_out = (
        db.session.query(func.count(func.distinct(CheckOutEvent.guest_id)))
        .filter(CheckOutEvent.event_id == event_id).scalar() or 0
    )
    total = Guest.query_active().filter(Guest.event_id == event_id).count()
    peak = _peak_attendance(event_id)
    return {
        "event_id": event_id,
        "total_registered": total,
        "total_checked_in": checked_in,
        "total_checked_out": checked_out,
        "peak_attendance": peak["peak_count"],
        "peak_time": peak["peak_time"],
        "generated_at": utcnow().isoformat(),
    }


# ── Hourly breakdown (Task 72) ───────────────────────────────────────────────
def hourly_breakdown(event_id: str) -> dict:
    checkins = CheckInEvent.query.filter_by(event_id=event_id).all()
    checkouts = CheckOutEvent.query.filter_by(event_id=event_id).all()
    buckets: dict[str, dict] = defaultdict(lambda: {"checkins": 0, "checkouts": 0})
    for e in checkins:
        hour = _aware(e.timestamp).strftime("%Y-%m-%dT%H:00")
        buckets[hour]["checkins"] += 1
    for e in checkouts:
        hour = _aware(e.timestamp).strftime("%Y-%m-%dT%H:00")
        buckets[hour]["checkouts"] += 1

    rows = []
    running = 0
    for hour in sorted(buckets):
        running += buckets[hour]["checkins"] - buckets[hour]["checkouts"]
        rows.append({
            "hour": hour,
            "checkins": buckets[hour]["checkins"],
            "checkouts": buckets[hour]["checkouts"],
            "current": running,
        })
    return {"event_id": event_id, "hourly_breakdown": rows}


# ── Session analytics (Task 73) ──────────────────────────────────────────────
def session_analytics(event_id: str) -> dict:
    sessions = EventSession.query_active().filter_by(event_id=event_id).all()
    out = []
    for s in sessions:
        records = SessionAttendance.query.filter_by(session_id=s.id).all()
        durations = [r.duration_minutes for r in records if r.duration_minutes is not None]
        avg = round(sum(durations) / len(durations), 1) if durations else 0
        out.append({
            "session_id": s.id,
            "name": s.name,
            "total_attendees": len(records),
            "avg_duration": avg,
            "checkins": sum(1 for r in records if r.check_in_time),
            "checkouts": sum(1 for r in records if r.check_out_time),
        })
    out.sort(key=lambda x: x["total_attendees"], reverse=True)
    return {"event_id": event_id, "sessions": out}


# ── Category analytics w/ rates (Task 74) ────────────────────────────────────
def category_analytics(event_id: str) -> dict:
    out = []
    for cat in GuestCategory:
        guests = Guest.query_active().filter_by(event_id=event_id, category=cat.value).all()
        count = len(guests)
        if count == 0:
            continue
        checked_in = sum(1 for g in guests if g.current_status in (GuestStatus.PRESENT.value, GuestStatus.DEPARTED.value))
        checked_out = sum(1 for g in guests if g.current_status == GuestStatus.DEPARTED.value)
        out.append({
            "category": cat.value,
            "count": count,
            "checkin_rate": round(checked_in * 100.0 / count, 1),
            "checkout_rate": round(checked_out * 100.0 / count, 1),
        })
    return {"event_id": event_id, "categories": out}


# ── Peak attendance (Task 75) ────────────────────────────────────────────────
def _peak_attendance(event_id: str) -> dict:
    """Replay check-in/out events chronologically to find max concurrent."""
    events = []
    for e in CheckInEvent.query.filter_by(event_id=event_id).all():
        events.append((_aware(e.timestamp), 1))
    for e in CheckOutEvent.query.filter_by(event_id=event_id).all():
        events.append((_aware(e.timestamp), -1))
    events.sort(key=lambda x: x[0])

    running = 0
    peak = 0
    peak_time = None
    for ts, delta in events:
        running += delta
        if running > peak:
            peak = running
            peak_time = ts
    return {"peak_count": peak, "peak_time": peak_time.isoformat() if peak_time else None}


def peak_attendance(event_id: str) -> dict:
    result = _peak_attendance(event_id)
    return {"event_id": event_id, "peak_count": result["peak_count"], "peak_time": result["peak_time"]}
