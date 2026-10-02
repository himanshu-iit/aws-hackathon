"""OTP generation and verification.

Backs Property 1 (OTP Validation Round Trip): a freshly generated OTP verified
with the correct code succeeds exactly once; an incorrect code is rejected and,
after the retry limit, the challenge is locked out.

Rules (Requirements 1, 2):
- 6-digit numeric code
- 5-minute TTL (configurable)
- 3 incorrect attempts -> 15-minute lockout (configurable)
- max 5 OTP requests per hour per phone/email (configurable)
"""
import secrets
from datetime import timedelta

from flask import current_app

from app.extensions import db
from app.models.auth import OTPRequest
from app.models.base import utcnow


class OTPError(Exception):
    """Base class for OTP-related errors."""


class RateLimitExceeded(OTPError):
    pass


class OTPResult:
    """Outcome of a verification attempt."""

    def __init__(self, success: bool, message: str, locked: bool = False):
        self.success = success
        self.message = message
        self.locked = locked


class OTPService:
    @staticmethod
    def _generate_code(length: int) -> str:
        """Cryptographically-random numeric code, zero-padded."""
        upper = 10 ** length
        return str(secrets.randbelow(upper)).zfill(length)

    @classmethod
    def _recent_request_count(cls, phone_or_email: str) -> int:
        window_start = utcnow() - timedelta(hours=1)
        return (
            OTPRequest.query.filter(
                OTPRequest.phone_or_email == phone_or_email,
                OTPRequest.created_at >= window_start,
            ).count()
        )

    @classmethod
    def generate(cls, phone_or_email: str, request_type: str) -> OTPRequest:
        """Create and persist a new OTP challenge.

        Raises RateLimitExceeded if the per-hour cap is hit. Returns the
        OTPRequest (the caller is responsible for delivering the code via
        email/SMS).
        """
        cfg = current_app.config
        limit = cfg["OTP_RATE_LIMIT_PER_HOUR"]
        if cls._recent_request_count(phone_or_email) >= limit:
            raise RateLimitExceeded(
                f"Too many OTP requests. Limit is {limit} per hour."
            )

        code = cls._generate_code(cfg["OTP_LENGTH"])
        otp = OTPRequest(
            phone_or_email=phone_or_email,
            otp_code=code,
            request_type=request_type,
            expires_at=utcnow() + timedelta(minutes=cfg["OTP_TTL_MINUTES"]),
            attempt_count=0,
            verified=False,
        )
        db.session.add(otp)
        db.session.commit()
        return otp

    @classmethod
    def verify(cls, phone_or_email: str, code: str) -> OTPResult:
        """Verify a submitted code against the latest active challenge."""
        cfg = current_app.config
        otp = (
            OTPRequest.query.filter_by(phone_or_email=phone_or_email, verified=False)
            .order_by(OTPRequest.created_at.desc())
            .first()
        )

        if otp is None:
            return OTPResult(False, "No pending OTP found. Request a new code.")

        if otp.is_locked():
            return OTPResult(
                False,
                "Too many failed attempts. Try again later.",
                locked=True,
            )

        if otp.is_expired():
            return OTPResult(False, "OTP has expired. Request a new code.")

        if code == otp.otp_code:
            otp.verified = True
            otp.verified_at = utcnow()
            db.session.commit()
            return OTPResult(True, "OTP verified successfully.")

        # Incorrect code — increment and possibly lock
        otp.attempt_count += 1
        remaining = cfg["OTP_RETRY_LIMIT"] - otp.attempt_count
        if otp.attempt_count >= cfg["OTP_RETRY_LIMIT"]:
            otp.locked_until = utcnow() + timedelta(minutes=cfg["OTP_LOCKOUT_MINUTES"])
            db.session.commit()
            return OTPResult(
                False,
                f"Incorrect code. Locked for {cfg['OTP_LOCKOUT_MINUTES']} minutes.",
                locked=True,
            )
        db.session.commit()
        return OTPResult(False, f"Incorrect code. {remaining} attempt(s) remaining.")
