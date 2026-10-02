"""Audit logging helper — append-only records of consequential actions."""
import logging

from flask import request

from app.extensions import db
from app.models.auth import AuditLog

logger = logging.getLogger(__name__)


def record_audit(
    action_type: str,
    resource_type: str,
    resource_id: str | None = None,
    actor_user_id: str | None = None,
    status: str = "success",
    before_value: dict | None = None,
    after_value: dict | None = None,
    notes: str | None = None,
) -> None:
    """Insert an immutable audit record. Never raises — logs on failure."""
    try:
        entry = AuditLog(
            actor_user_id=actor_user_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            before_value=before_value,
            after_value=after_value,
            notes=notes,
            ip_address=_client_ip(),
        )
        db.session.add(entry)
        db.session.commit()
    except Exception:  # noqa: BLE001
        db.session.rollback()
        logger.exception("Failed to write audit log for %s/%s", action_type, resource_type)


def _client_ip() -> str | None:
    if not request:
        return None
    # Respect X-Forwarded-For from ALB/CloudFront, fall back to remote_addr
    fwd = request.headers.get("X-Forwarded-For")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.remote_addr
