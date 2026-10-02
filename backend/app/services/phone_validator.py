"""Phone number validation and normalization.

Format (per Requirement 3): a 2-digit country code plus exactly 10 national
digits. The canonical stored form is ``+CC-XXXXXXXXXX``.

Property 2 (Normalization Idempotence): normalize(normalize(x)) == normalize(x)
for every valid input. This is guaranteed because normalize() strips all
non-digits, re-splits into country code + national number, and re-applies the
same canonical format — so a second pass sees an already-canonical value and
produces an identical result.
"""
import re


class PhoneValidationError(ValueError):
    """Raised when a phone number fails validation."""


# Canonical form: +CC-XXXXXXXXXX  (2-digit CC, 10-digit national number)
_CANONICAL_RE = re.compile(r"^\+(\d{2})-(\d{10})$")


class PhoneValidator:
    COUNTRY_CODE_DIGITS = 2
    NATIONAL_DIGITS = 10

    @classmethod
    def _digits_only(cls, raw: str) -> str:
        return re.sub(r"\D", "", raw or "")

    @classmethod
    def validate(cls, raw: str) -> tuple[bool, str | None]:
        """Return (is_valid, error_message)."""
        if not raw or not raw.strip():
            return False, "Phone number is required"

        digits = cls._digits_only(raw)
        total = cls.COUNTRY_CODE_DIGITS + cls.NATIONAL_DIGITS

        if len(digits) != total:
            return (
                False,
                (
                    f"Phone number must have a {cls.COUNTRY_CODE_DIGITS}-digit country "
                    f"code and {cls.NATIONAL_DIGITS} digits "
                    f"(expected {total} digits, got {len(digits)}). "
                    "Example: +91-9876543210"
                ),
            )
        return True, None

    @classmethod
    def normalize(cls, raw: str) -> str:
        """Return the canonical ``+CC-XXXXXXXXXX`` form.

        Raises PhoneValidationError on invalid input. Idempotent: feeding the
        output back in yields the same value.
        """
        is_valid, error = cls.validate(raw)
        if not is_valid:
            raise PhoneValidationError(error)

        digits = cls._digits_only(raw)
        cc = digits[: cls.COUNTRY_CODE_DIGITS]
        national = digits[cls.COUNTRY_CODE_DIGITS :]
        return f"+{cc}-{national}"

    @classmethod
    def is_canonical(cls, value: str) -> bool:
        return bool(_CANONICAL_RE.match(value or ""))

    @classmethod
    def extract_country_code(cls, raw: str) -> str:
        return cls._digits_only(raw)[: cls.COUNTRY_CODE_DIGITS]

    @classmethod
    def extract_national_number(cls, raw: str) -> str:
        return cls._digits_only(raw)[cls.COUNTRY_CODE_DIGITS :]


def normalize_phone(raw: str) -> str:
    """Module-level convenience wrapper used by models and endpoints."""
    return PhoneValidator.normalize(raw)
