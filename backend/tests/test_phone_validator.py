"""Property 2: Phone Number Normalization Idempotence (Requirements 3.1-3.5)."""
import pytest
from hypothesis import given, strategies as st

from app.services.phone_validator import PhoneValidator, PhoneValidationError

# Valid inputs: 2-digit country code + 10-digit national number, in various
# surface formats (with +, dashes, spaces, parentheses).
valid_cc = st.from_regex(r"[1-9][0-9]", fullmatch=True)
valid_national = st.from_regex(r"[0-9]{10}", fullmatch=True)


@given(cc=valid_cc, national=valid_national)
def test_normalization_idempotent(cc, national):
    """normalize(normalize(x)) == normalize(x) for all valid inputs."""
    raw = f"+{cc}-{national}"
    once = PhoneValidator.normalize(raw)
    twice = PhoneValidator.normalize(once)
    assert once == twice
    assert once == f"+{cc}-{national}"


@given(cc=valid_cc, national=valid_national)
def test_normalization_strips_formatting(cc, national):
    """Different surface formats normalize to the same canonical value."""
    canonical = f"+{cc}-{national}"
    variants = [
        f"+{cc}-{national}",
        f"{cc}{national}",
        f"+{cc} {national}",
        f"({cc}) {national}",
    ]
    for v in variants:
        assert PhoneValidator.normalize(v) == canonical


def test_rejects_wrong_digit_count():
    with pytest.raises(PhoneValidationError):
        PhoneValidator.normalize("+91-12345")  # too short


def test_rejects_empty():
    with pytest.raises(PhoneValidationError):
        PhoneValidator.normalize("")
