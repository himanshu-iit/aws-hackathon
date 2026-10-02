"""Session token management: create, validate, revoke."""
import secrets

from flask import current_app

from app.extensions import db
from app.models.auth import SessionToken
from app.models.base import utcnow


class SessionManager:
    @staticmethod
    def _generate_token() -> str:
        """URL-safe cryptographically-random token."""
        return secrets.token_urlsafe(48)[:64]

    @classmethod
    def create_session(
        cls,
        user_id: str,
        user_type: str,
        permissions: list[str] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> SessionToken:
        """Create and persist a new session token."""
        token = SessionToken(
            user_id=user_id,
            token=cls._generate_token(),
            user_type=user_type,
            expires_at=utcnow() + current_app.config["SESSION_TTL"],
            ip_address=ip_address,
            user_agent=user_agent,
            permissions_json=permissions or [],
            is_valid=True,
        )
        db.session.add(token)
        db.session.commit()
        return token

    @classmethod
    def validate_session(
        cls,
        token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> SessionToken | None:
        """Return the active SessionToken for a token string, or None.

        When ip_address / user_agent are provided they must match the values
        recorded at creation time (binding), rejecting stolen tokens.
        """
        session = SessionToken.query.filter_by(token=token).first()
        if session is None or not session.is_active():
            return None
        if ip_address is not None and session.ip_address and session.ip_address != ip_address:
            return None
        if user_agent is not None and session.user_agent and session.user_agent != user_agent:
            return None
        return session

    @classmethod
    def revoke_session(cls, token: str) -> bool:
        """Invalidate a session (logout). Returns True if a session was revoked."""
        session = SessionToken.query.filter_by(token=token).first()
        if session is None:
            return False
        session.is_valid = False
        db.session.commit()
        return True

    @classmethod
    def get_active_sessions(cls, user_id: str) -> list[SessionToken]:
        sessions = SessionToken.query.filter_by(user_id=user_id, is_valid=True).all()
        return [s for s in sessions if not s.is_expired()]

    @classmethod
    def cleanup_expired(cls) -> int:
        """Mark all expired tokens invalid. Returns count cleaned."""
        count = 0
        for s in SessionToken.query.filter_by(is_valid=True).all():
            if s.is_expired():
                s.is_valid = False
                count += 1
        if count:
            db.session.commit()
        return count
