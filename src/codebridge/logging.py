"""CodeBridge logging configuration with secret redaction."""

from __future__ import annotations

import logging
import re

# Patterns to redact from log output
_REDACT_PATTERNS = [
    re.compile(r"(nvidia[_-]?api[_-]?key\s*[=:]\s*)([^\s,\"']+)", re.IGNORECASE),
    re.compile(r"(codebridge[_-]?local[_-]?token\s*[=:]\s*)([^\s,\"']+)", re.IGNORECASE),
    re.compile(r"(authorization\s*:\s*bearer\s+)([^\s,\"']+)", re.IGNORECASE),
    re.compile(r"(authorization\s*:\s*token\s+)([^\s,\"']+)", re.IGNORECASE),
    re.compile(r"(\"authorization\"\s*:\s*\")([^\"]+)(\")", re.IGNORECASE),
    re.compile(r"(nvapi-)([A-Za-z0-9_-]{8,})", re.IGNORECASE),
]

_REDACTED = "[REDACTED]"


def redact(text: str) -> str:
    """Remove secrets from a string."""
    for pattern in _REDACT_PATTERNS:
        if pattern.groups == 3:  # type: ignore[attr-defined]
            text = pattern.sub(r"\g<1>" + _REDACTED + r"\g<3>", text)
        else:
            text = pattern.sub(r"\g<1>" + _REDACTED, text)
    return text


class RedactingFilter(logging.Filter):
    """Logging filter that redacts secrets from log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(str(record.msg))
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: redact(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, (tuple, list)):
                record.args = tuple(redact(str(a)) for a in record.args)
        return True


def configure_logging(level: str = "INFO") -> None:
    """Configure root logger with redacting filter and clean format."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.addFilter(RedactingFilter())

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(log_level)
    # Avoid duplicate handlers if called multiple times
    root.handlers.clear()
    root.addHandler(handler)

    # Silence noisy third-party loggers
    for noisy in ("httpx", "httpcore", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
