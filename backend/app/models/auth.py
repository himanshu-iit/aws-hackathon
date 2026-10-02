"""Authentication models: OTP requests, session tokens, and the audit log."""
import enum

from app.extensions import db
from app.models.base import BaseModel, utcnow


class OTPRequestType(str, enum.Enum):
    MASTER_SETUP = "master_setup"
    MASTER_LOGIN = "master_login"
    VOLUNTEER_REGISTRATION = "volunteer_registration"
    VOLUNTEER_LOGIN = "volunteer_login"


class OTPRequest(BaseModel):
    """A one-time password challenge sent to an email or phone."""

    __tablename__ = "otp_requests"

    phone_or_email = db.Column(db.String(255), nullable=False, index=True)
    otp_code = db.Column(db.String(6), nullable=False)
    request_type = db.Column(db.String(32), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    attempt_count = db.Column(db.Integer, default=0, nullable=False)
    verified = db.Column(db.Boolean, default=False, nullable=False)
    verified_at = db.Column(db.DateTime, nullable=True)
    locked_until = db.Column(db.DateTime, nullable=True)

    def is_expired(self) -> bool:
        return utcnow() > _aware(self.expires_at)

    def is_locked(self) -> bool:
        return self.locked_until is not None and utcnow() < _aware(self.locked_until)


class SessionToken(BaseModel):
    """An authenticated session, bound to a user with optional IP/UA binding."""

    __tablename__ = "session_tokens"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    token = db.Column(db.String(64), nullable=False, unique=True, index=True)
    user_type = db.Column(db.String(20), nullable=False)
    event_id = db.Column(db.String(2), nullable=True, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    permissions_json = db.Column(db.JSON, nullable=True)
    is_valid = db.Column(db.Boolean, default=True, nullable=False)

    def is_expired(self) -> bool:
        return utcnow() > _aware(self.expires_at)

    def is_active(self) -> bool:
        return self.is_valid and not self.is_expired()


class AuditLog(BaseModel):
    """Immutable, append-only record of consequential actions.

    Rows are only ever inserted — never updated or deleted — to preserve an
    accurate accountability trail (Requirement 20).
    """

    __tablename__ = "audit_logs"

    actor_user_id = db.Column(db.String(36), nullable=True, index=True)
    action_type = db.Column(db.String(100), nullable=False, index=True)
    resource_type = db.Column(db.String(100), nullable=False)
    resource_id = db.Column(db.String(36), nullable=True)
    before_value = db.Column(db.JSON, nullable=True)
    after_value = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="success")
    notes = db.Column(db.String(500), nullable=True)
    # Dedicated timestamp index for fast time-range audit queries
    event_time = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)


def _aware(dt):
    """Treat naive datetimes (from SQLite) as UTC for safe comparison."""
    from datetime import timezone

    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
