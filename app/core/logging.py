import contextvars
import json
import logging
import sys
import uuid
from datetime import UTC, datetime, timezone
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variable for correlating logs across a single request lifecycle
request_id_ctx_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)

SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "mfa_secret",
    "secret",
    "authorization",
    "cookie",
}


def get_request_id() -> str:
    """Returns the current request ID from contextvars, or empty string."""
    return request_id_ctx_var.get()


def _sanitize_data(data: Any) -> Any:
    """Recursively redacts sensitive values from log extras."""
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if any(sens in k.lower() for sens in SENSITIVE_KEYS):
                sanitized[k] = "***REDACTED***"
            else:
                sanitized[k] = _sanitize_data(v)
        return sanitized
    elif isinstance(data, list):
        return [_sanitize_data(item) for item in data]
    return data


class JSONFormatter(logging.Formatter):
    """
    Structured JSON log formatter that includes ISO-8601 UTC timestamp,
    severity level, logger name, message, bound request_id, and any extra context.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
        }

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        # Append extra parameters passed to logging calls
        standard_attrs = {
            "args",
            "asctime",
            "created",
            "exc_info",
            "exc_text",
            "filename",
            "funcName",
            "id",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "message",
            "msg",
            "name",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "thread",
            "threadName",
        }

        for key, val in record.__dict__.items():
            if key not in standard_attrs and not key.startswith("_"):
                if any(sens in key.lower() for sens in SENSITIVE_KEYS):
                    log_payload[key] = "***REDACTED***"
                else:
                    log_payload[key] = _sanitize_data(val)

        return json.dumps(log_payload, default=str)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts or generates an X-Request-ID, binds it to
    the log context variable for distributed correlation, and appends
    it to response headers.
    """

    async def dispatch(self, request: Request, call_next):
        req_id = (
            request.headers.get("x-request-id")
            or request.headers.get("X-Request-ID")
            or str(uuid.uuid4())
        )
        token = request_id_ctx_var.set(req_id)
        try:
            response: Response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            request_id_ctx_var.reset(token)


def setup_logging(level: int = logging.INFO) -> None:
    """Configures root logger to use JSON formatting on stdout."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]
