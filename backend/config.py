"""Configuration classes for the Event Tracker Flask backend.

Config values are read from environment variables. In AWS, these are injected
from Secrets Manager into the ECS task; locally they come from a .env file.
"""
import os
from datetime import timedelta


class Config:
    """Base configuration shared across all environments."""

    # ── Core ────────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")
    AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

    # ── Database ──────────────────────────────────────────────────────────────
    # Falls back to a local SQLite file when DATABASE_URL is not provided,
    # so the app can run locally without a MySQL server.
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or "sqlite:///event_tracker_dev.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Connection pooling (per design: pool_size=20, max_overflow=40, recycle 3600).
    # Pool options only apply to non-SQLite engines.
    @property
    def SQLALCHEMY_ENGINE_OPTIONS(self):  # noqa: N802
        if self.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
            return {}
        return {
            "pool_size": 20,
            "max_overflow": 40,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        }

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS = [
        o.strip()
        for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
        if o.strip()
    ]

    # ── OTP ───────────────────────────────────────────────────────────────────
    OTP_TTL_MINUTES = int(os.environ.get("OTP_TTL_MINUTES", "5"))
    OTP_RETRY_LIMIT = int(os.environ.get("OTP_RETRY_LIMIT", "3"))
    OTP_LOCKOUT_MINUTES = int(os.environ.get("OTP_LOCKOUT_MINUTES", "15"))
    OTP_RATE_LIMIT_PER_HOUR = int(os.environ.get("OTP_RATE_LIMIT_PER_HOUR", "5"))
    OTP_LENGTH = 6

    # ── Sessions ────────────────────────────────────────────────────────────────
    SESSION_TTL = timedelta(hours=int(os.environ.get("SESSION_TTL_HOURS", "8")))

    # ── Logging ─────────────────────────────────────────────────────────────────
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    CLOUDWATCH_LOG_GROUP = os.environ.get("CLOUDWATCH_LOG_GROUP", "/ecs/event-tracker-app")
    ENABLE_CLOUDWATCH = os.environ.get("ENABLE_CLOUDWATCH", "false").lower() == "true"

    # ── External services ─────────────────────────────────────────────────────
    SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
    SENDGRID_FROM_EMAIL = os.environ.get("SENDGRID_FROM_EMAIL", "noreply@eventtracker.local")
    TWILIO_API_KEY = os.environ.get("TWILIO_API_KEY", "")
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
    TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER", "")

    # ── LLM (Phase 7) ───────────────────────────────────────────────────────────
    LLM_API_KEY = os.environ.get("LLM_API_KEY", "")

    TESTING = False
    DEBUG = False


class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = "DEBUG"


class StagingConfig(Config):
    DEBUG = False


class ProductionConfig(Config):
    DEBUG = False
    ENABLE_CLOUDWATCH = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    # Deterministic settings for tests
    OTP_RATE_LIMIT_PER_HOUR = 1000


_CONFIG_MAP = {
    "development": DevelopmentConfig,
    "staging": StagingConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config(name: str | None = None) -> type[Config]:
    """Return the config class for the given environment name."""
    env = (name or os.environ.get("FLASK_ENV", "development")).lower()
    return _CONFIG_MAP.get(env, DevelopmentConfig)
