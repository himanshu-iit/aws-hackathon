"""Base model with common fields and soft-delete support."""
import uuid
from datetime import datetime, timezone

from app.extensions import db


def utcnow() -> datetime:
    """Timezone-aware UTC now (avoids deprecated datetime.utcnow)."""
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


class BaseModel(db.Model):
    """Abstract base: UUID id, timestamps, and soft-delete.

    All concrete models inherit these columns. Soft-deleted rows keep a
    `deleted_at` timestamp instead of being physically removed, and the
    `query_active` helper filters them out.
    """

    __abstract__ = True

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark this row as deleted without removing it."""
        self.deleted_at = utcnow()

    @classmethod
    def query_active(cls):
        """Query excluding soft-deleted rows."""
        return cls.query.filter(cls.deleted_at.is_(None))

    def to_dict(self) -> dict:
        """Serialize column values to a plain dict (ISO timestamps)."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
