"""Structured JSON logging setup. Call configure_logging() at app startup."""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        # propagate any extra kwargs passed to the logger call
        for key, val in record.__dict__.items():
            if key not in {
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
            }:
                payload[key] = val
        return json.dumps(payload, default=str)


def configure_logging(level: str | None = None) -> None:
    """Wire the root logger to emit JSON on stderr."""
    effective = (level or os.getenv("LOG_LEVEL") or "INFO").upper()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(effective)
