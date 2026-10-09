"""Structured logging with structlog, PII masking, and trace correlation."""

import logging
import sys
from typing import Any, cast

import structlog
from structlog.types import EventDict, WrappedLogger


def mask_pii_processor(
    _logger: WrappedLogger, _method_name: str, event_dict: EventDict
) -> EventDict:
    """Mask sensitive fields (PII, credentials, raw PANs) before logging."""
    sensitive_keys = {
        "pan",
        "card_number",
        "cvv",
        "password",
        "secret",
        "api_key",
        "token",
        "authorization",
    }
    for key, value in list(event_dict.items()):
        if any(sens in key.lower() for sens in sensitive_keys):
            event_dict[key] = "[REDACTED]"
        elif isinstance(value, dict):
            # Shallow recursive masking
            for subkey in list(value.keys()):
                if any(sens in subkey.lower() for sens in sensitive_keys):
                    value[subkey] = "[REDACTED]"
    return event_dict


def configure_logging(log_level: str = "INFO", json_format: bool = True) -> None:
    """Configure structlog and standard library logging handlers."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)

    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        mask_pii_processor,
    ]

    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "aegis") -> structlog.stdlib.BoundLogger:
    """Obtain a structured logger instance."""
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))
