"""Guest data validation (Requirements 7, 8).

Validates required fields, email/phone formats, and guest category, returning
per-field errors so the API can report exactly what is wrong.
"""
import re

from app.models.guest import GuestCategory
from app.services.phone_validator import PhoneValidator

# Simplified RFC 5322 email check
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

VALID_CATEGORIES = {c.value for c in GuestCategory}


class GuestValidationResult:
    def __init__(self, errors: dict[str, str], normalized: dict):
        self.errors = errors
        self.normalized = normalized

    @property
    def is_valid(self) -> bool:
        return not self.errors


def validate_guest(data: dict, require_event: bool = True) -> GuestValidationResult:
    """Validate a guest payload. Returns per-field errors + normalized values."""
    errors: dict[str, str] = {}
    normalized: dict = {}

    # Required: name
    name = (data.get("name") or "").strip()
    if not name:
        errors["name"] = "Name is required"
    else:
        normalized["name"] = name

    # Required: event_id
    if require_event:
        event_id = (data.get("event_id") or "").strip()
        if not event_id:
            errors["event_id"] = "event_id is required"
        else:
            normalized["event_id"] = event_id

    # Optional phone — if present, must be valid; normalized to canonical form
    raw_phone = (data.get("phone") or "").strip()
    if raw_phone:
        ok, err = PhoneValidator.validate(raw_phone)
        if not ok:
            errors["phone"] = err
        else:
            normalized["phone"] = PhoneValidator.normalize(raw_phone)

    # Optional email — if present, must look valid
    email = (data.get("email") or "").strip()
    if email:
        if not _EMAIL_RE.match(email):
            errors["email"] = "Invalid email format"
        else:
            normalized["email"] = email.lower()

    # Optional emergency contact phone
    raw_ec_phone = (data.get("emergency_contact_phone") or "").strip()
    if raw_ec_phone:
        ok, err = PhoneValidator.validate(raw_ec_phone)
        if not ok:
            errors["emergency_contact_phone"] = err
        else:
            normalized["emergency_contact_phone"] = PhoneValidator.normalize(raw_ec_phone)

    # Category — defaults to General_Attendee; if given must be valid
    category = (data.get("category") or GuestCategory.GENERAL_ATTENDEE.value).strip()
    if category not in VALID_CATEGORIES:
        errors["category"] = (
            f"Invalid category. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
        )
    else:
        normalized["category"] = category

    # Pass-through optional free-text fields
    for field in (
        "company",
        "job_title",
        "profession",
        "emergency_contact_name",
        "ticket_number",
        "badge_number",
        "dietary_restrictions",
        "accessibility_needs",
    ):
        value = data.get(field)
        if value is not None and str(value).strip():
            normalized[field] = str(value).strip()

    return GuestValidationResult(errors, normalized)
