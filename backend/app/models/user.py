"""User hierarchy models: MasterUser and Volunteer (single-table inheritance)."""
import enum

from app.extensions import db
from app.models.base import BaseModel, utcnow


class VolunteerStatus(str, enum.Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(BaseModel):
    """Base user with polymorphic discriminator.

    MasterUser and Volunteer share this table; `type` distinguishes them.
    """

    __tablename__ = "users"

    type = db.Column(db.String(20), nullable=False, index=True)

    # Shared contact fields (nullable at base level; subclasses enforce)
    name = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=True, index=True)
    phone = db.Column(db.String(20), nullable=True, index=True)
    last_login = db.Column(db.DateTime, nullable=True)

    # Event scope: the 2-digit event this user belongs to.
    event_id = db.Column(db.String(2), nullable=True, index=True)

    # Volunteer-specific
    approval_status = db.Column(
        db.String(20), nullable=True, index=True
    )
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "user",
    }

    def record_login(self) -> None:
        self.last_login = utcnow()


class MasterUser(User):
    """System administrator created during first-time setup."""

    __mapper_args__ = {"polymorphic_identity": "master_user"}

    @property
    def permissions(self) -> list[str]:
        return [
            "system_configuration",
            "volunteer_approval",
            "guest_registration",
            "checkin_checkout",
            "query_execution",
            "report_generation",
            "data_export",
        ]


class Volunteer(User):
    """Staff member who assists guests. Requires MasterUser approval."""

    __mapper_args__ = {"polymorphic_identity": "volunteer"}

    @property
    def is_approved(self) -> bool:
        return self.approval_status == VolunteerStatus.APPROVED.value

    @property
    def permissions(self) -> list[str]:
        if not self.is_approved:
            return []
        return [
            "guest_registration",
            "checkin_checkout",
            "basic_queries",
            "view_attendance",
        ]
