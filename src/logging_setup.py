"""
Logging setup module for the FastAPI + Langfuse application.

This module configures structured logging in JSON format, which is easier to
parse in observability backends like ELK, Datadog, or Google Cloud Logging.

Features:
- Logs are written to stdout (12-factor compliant).
- Messages are formatted as JSON objects with level, logger name, and message.
- Optionally includes a `request_id` field if provided via `extra` in logging calls.
"""

import json
import logging
import sys


class JsonFormatter(logging.Formatter):
    """Custom logging formatter that outputs logs as JSON objects.

    Example output:
        {"level": "INFO", "name": "app", "msg": "Request completed", "request_id": "1234"}

    Attributes:
        None
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format a logging record as a JSON string.

        Args:
            record: The log record provided by the logging framework.

        Returns:
            str: A JSON-formatted string with standard fields and optional request_id.
        """
        base = {
            "level": record.levelname,
            "name": record.name,
            "msg": record.getMessage(),
        }
        # Attach request_id if present in extra context
        if hasattr(record, "request_id"):
            base["request_id"] = record.request_id
        return json.dumps(base)


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger to output JSON-formatted logs to stdout.

    This replaces any existing handlers with a single StreamHandler.

    Args:
        level: Logging level as a string ("DEBUG", "INFO", "WARNING", "ERROR").
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
