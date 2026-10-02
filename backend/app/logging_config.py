"""Structured JSON logging with optional CloudWatch shipping.

In ECS, stdout is automatically captured by the awslogs driver and forwarded to
the configured CloudWatch log group, so JSON-to-stdout is sufficient. When
ENABLE_CLOUDWATCH is true and running outside ECS, a boto3-based handler can be
attached as a fallback.
"""
import logging
import sys

from pythonjsonlogger import jsonlogger


def configure_logging(app) -> None:
    level = getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    # Clear any default handlers to avoid duplicate log lines
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)

    # Quiet noisy libraries
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)

    app.logger.info(
        "Logging configured",
        extra={"log_group": app.config.get("CLOUDWATCH_LOG_GROUP"), "level": level},
    )
