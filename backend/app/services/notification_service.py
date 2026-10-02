"""Email and SMS delivery with retry and dev console fallback.

When API keys are not configured (local dev), messages are logged to the
console instead of being sent — so OTP flows are testable without external
accounts. In production, SendGrid (email) and Twilio (SMS) are used.
"""
import logging
import time

import requests
from flask import current_app

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_BACKOFF_BASE_SECONDS = 0.5


def _retry(fn, *args, **kwargs):
    """Call fn with exponential-backoff retries. Returns True on success."""
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            fn(*args, **kwargs)
            return True
        except Exception as exc:  # noqa: BLE001 - log and retry
            wait = _BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
            logger.warning(
                "Delivery attempt %d/%d failed: %s", attempt, _MAX_RETRIES, exc
            )
            if attempt < _MAX_RETRIES:
                time.sleep(wait)
    return False


class EmailService:
    @staticmethod
    def _send_via_sendgrid(to_email: str, subject: str, body: str) -> None:
        cfg = current_app.config
        resp = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {cfg['SENDGRID_API_KEY']}",
                "Content-Type": "application/json",
            },
            json={
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": cfg["SENDGRID_FROM_EMAIL"]},
                "subject": subject,
                "content": [{"type": "text/plain", "value": body}],
            },
            timeout=10,
        )
        resp.raise_for_status()

    @classmethod
    def send_otp_email(cls, to_email: str, code: str) -> bool:
        subject = "Your Event Tracker verification code"
        body = f"Your verification code is {code}. It expires in 5 minutes."
        return cls.send_notification_email(to_email, subject, body)

    @classmethod
    def send_notification_email(cls, to_email: str, subject: str, body: str) -> bool:
        if not current_app.config.get("SENDGRID_API_KEY"):
            logger.info("[DEV EMAIL] to=%s subject=%s body=%s", to_email, subject, body)
            return True
        return _retry(cls._send_via_sendgrid, to_email, subject, body)


class SMSService:
    @staticmethod
    def _send_via_twilio(to_number: str, body: str) -> None:
        cfg = current_app.config
        sid = cfg["TWILIO_ACCOUNT_SID"]
        resp = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
            auth=(sid, cfg["TWILIO_API_KEY"]),
            data={"To": to_number, "From": cfg["TWILIO_FROM_NUMBER"], "Body": body},
            timeout=10,
        )
        resp.raise_for_status()

    @classmethod
    def send_otp_sms(cls, to_number: str, code: str) -> bool:
        return cls.send_notification_sms(
            to_number, f"Your Event Tracker code is {code} (valid 5 min)."
        )

    @classmethod
    def send_notification_sms(cls, to_number: str, body: str) -> bool:
        if not current_app.config.get("TWILIO_API_KEY"):
            logger.info("[DEV SMS] to=%s body=%s", to_number, body)
            return True
        return _retry(cls._send_via_twilio, to_number, body)
