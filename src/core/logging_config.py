"""Logging configuration for the application."""

from __future__ import annotations

import logging
import sys

from loguru import logger
from pythonjsonlogger import jsonlogger


class LokiJsonFormatter(jsonlogger.JsonFormatter):
    """JSON formatter limited to the required fields."""

    def add_fields(
        self, log_record: dict, record: logging.LogRecord, message_dict: dict
    ) -> None:  # type: ignore[override]
        super().add_fields(log_record, record, message_dict)
        allowed = {"timestamp", "level", "message", "task_id", "trace_id"}
        for key in list(log_record.keys()):
            if key not in allowed:
                log_record.pop(key)


def setup_logging() -> None:
    """Configure Loguru with JSON output for Loki."""

    logger.remove()

    formatter = LokiJsonFormatter(
        fmt="%(asctime)s %(levelname)s %(message)s %(task_id)s %(trace_id)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logging.basicConfig(handlers=[handler], level=logging.INFO, force=True)
    logger.add(handler, level="INFO", enqueue=False, format="{message}")

    file_handler = logging.FileHandler("loki.log")
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)
    logger.add(file_handler, level="INFO", enqueue=False, format="{message}")
