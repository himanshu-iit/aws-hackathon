"""Dashboard + analytics endpoints (Phases 7 & 8).

All reads are role-gated to master users and approved volunteers and run
directly against RDS (no caching layer).
"""
from flask import Blueprint, jsonify, request

from app.auth_utils import require_role, event_scope_ok
from app.services import analytics_service as svc

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/events")

_STAFF_ROLES = ("master_user", "volunteer")


def _scope_guard(event_id):
    """Return a 403 response if the event is not the user's own, else None."""
    if not event_scope_ok(event_id):
        return jsonify({
            "success": False,
            "error": {"code": "EVENT_FORBIDDEN", "message": "You can only access your own event."},
        }), 403
    return None


# ── Phase 7: Dashboard ───────────────────────────────────────────────────────
@analytics_bp.route("/<event_id>/dashboard", methods=["GET"])
@require_role(*_STAFF_ROLES)
def dashboard(event_id):
    guard = _scope_guard(event_id)
    if guard:
        return guard
    return jsonify({"success": True, **svc.dashboard_metrics(event_id)})


@analytics_bp.route("/<event_id>/attendance", methods=["GET"])
@require_role(*_STAFF_ROLES)
def attendance(event_id):
    guard = _scope_guard(event_id)
    if guard:
        return guard
    filters = {
        "current_status": request.args.get("current_status"),
        "category": request.args.get("category"),
        "current_location": request.args.get("location"),
    }
    limit = min(int(request.args.get("limit", 100)), 500)
    offset = int(request.args.get("offset", 0))
    return jsonify({"success": True, **svc.attendance_list(event_id, filters, limit, offset)})


@analytics_bp.route("/<event_id>/analytics/by-category", methods=["GET"])
@require_role(*_STAFF_ROLES)
def dashboard_by_category(event_id):
    guard = _scope_guard(event_id)
    if guard:
        return guard
    return jsonify({"success": True, **svc.by_category(event_id)})


@analytics_bp.route("/<event_id>/analytics/by-location", methods=["GET"])
@require_role(*_STAFF_ROLES)
def dashboard_by_location(event_id):
    guard = _scope_guard(event_id)
    if guard:
        return guard
    return jsonify({"success": True, **svc.by_location(event_id)})


@analytics_bp.route("/<event_id>/capacity", methods=["GET"])
@require_role(*_STAFF_ROLES)
def capacity(event_id):
    guard = _scope_guard(event_id)
    if guard:
        return guard
    return jsonify({"success": True, **svc.capacity_status(event_id)})


# ── Phase 8: Analytics & Reporting ───────────────────────────────────────────
@analytics_bp.route("/<event_id>/analytics", methods=["GET"])
@require_role(*_STAFF_ROLES)
def analytics_report(event_id):
    guard = _scope_guard(event_id)
    if guard:
        return guard
    return jsonify({"success": True, **svc.analytics_summary(event_id)})


@analytics_bp.route("/<event_id>/analytics/hourly", methods=["GET"])
@require_role(*_STAFF_ROLES)
def analytics_hourly(event_id):
    guard = _scope_guard(event_id)
    if guard:
        return guard
    return jsonify({"success": True, **svc.hourly_breakdown(event_id)})


@analytics_bp.route("/<event_id>/analytics/sessions", methods=["GET"])
@require_role(*_STAFF_ROLES)
def analytics_sessions(event_id):
    guard = _scope_guard(event_id)
    if guard:
        return guard
    return jsonify({"success": True, **svc.session_analytics(event_id)})


@analytics_bp.route("/<event_id>/analytics/categories", methods=["GET"])
@require_role(*_STAFF_ROLES)
def analytics_categories(event_id):
    guard = _scope_guard(event_id)
    if guard:
        return guard
    return jsonify({"success": True, **svc.category_analytics(event_id)})


@analytics_bp.route("/<event_id>/analytics/peak-time", methods=["GET"])
@require_role(*_STAFF_ROLES)
def analytics_peak(event_id):
    guard = _scope_guard(event_id)
    if guard:
        return guard
    return jsonify({"success": True, **svc.peak_attendance(event_id)})
