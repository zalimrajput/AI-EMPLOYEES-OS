"""Structured logging setup for the whole backend.

Never log secrets: this module exists precisely so we control what ends up on
stdout/stderr.  Request bodies, authorization headers, tokens and database
connection strings are never logged anywhere in the application.
"""
import logging
import sys

_configured = False


def configure_logging(level: str | None = None) -> None:
    """Idempotently configure a single, consistent root logger."""
    global _configured
    if _configured:
        return

    root = logging.getLogger()
    root.setLevel((level or "INFO").upper())

    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
            )
        )
        root.addHandler(handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)