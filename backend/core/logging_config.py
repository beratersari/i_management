"""
Central logging configuration.
Creates file and console handlers with support for TRACE/INFO/WARNING/ERROR levels.
"""
from __future__ import annotations

import functools
import logging
import os
import time
from typing import Callable, Optional, TypeVar

from backend.core.config import settings

F = TypeVar("F", bound=Callable[..., any])

TRACE_LEVEL = 5
logging.addLevelName(TRACE_LEVEL, "TRACE")


def trace(self: logging.Logger, message: str, *args, **kwargs) -> None:
    """Emit a TRACE-level message on the logger instance."""
    if self.isEnabledFor(TRACE_LEVEL):
        self._log(TRACE_LEVEL, message, args, **kwargs)


logging.Logger.trace = trace  # type: ignore[attr-defined]


class LogLevelFilter(logging.Filter):
    """Filter log records to an allowed set of levels."""

    def __init__(self, allowed_levels: set[int]) -> None:
        """Initialize the filter with the accepted level numbers."""
        super().__init__()
        self._allowed_levels = allowed_levels

    def filter(self, record: logging.LogRecord) -> bool:
        """Return True when the record level is allowed."""
        return record.levelno in self._allowed_levels


def _parse_allowed_levels() -> set[int]:
    """Parse the configured log levels into numeric values."""
    default_levels = {TRACE_LEVEL, logging.INFO, logging.WARNING, logging.ERROR}
    raw = settings.LOG_LEVELS
    if not raw:
        return default_levels

    levels: set[int] = set()
    for level_name in raw.split(","):
        normalized = level_name.strip().upper()
        if normalized == "TRACE":
            levels.add(TRACE_LEVEL)
        elif normalized == "ERROR":
            levels.add(logging.ERROR)
        elif normalized == "WARNING":
            levels.add(logging.WARNING)
        elif normalized == "INFO":
            levels.add(logging.INFO)
    return levels or default_levels


def _resolve_level(level_name: Optional[str]) -> int:
    """Resolve the configured log level string to its numeric value."""
    if not level_name:
        return logging.INFO
    normalized = level_name.strip().upper()
    if normalized == "TRACE":
        return TRACE_LEVEL
    return getattr(logging, normalized, logging.INFO)


def configure_logging() -> None:
    """Configure root logger with console + file handlers."""
    log_dir = os.path.dirname(settings.LOG_FILE_PATH)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    root_logger = logging.getLogger()
    root_logger.setLevel(_resolve_level(settings.LOG_LEVEL))
    root_logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    allowed_levels = _parse_allowed_levels()
    level_filter = LogLevelFilter(allowed_levels)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(level_filter)

    file_handler = logging.FileHandler(settings.LOG_FILE_PATH)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(level_filter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def log_db_timing(func: F) -> F:
    """
    Decorator to log the execution time of database operations.
    Logs the function name, arguments (excluding 'self' and 'conn'),
    and the duration in milliseconds.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get logger from the class instance (first arg is 'self')
        logger = logging.getLogger(func.__module__)
        
        # Build args string (skip 'self' and 'conn' for cleaner logs)
        arg_parts = []
        if len(args) > 1:
            # Skip 'self' (args[0]) and 'conn' if present (args[1] is often conn)
            display_args = args[2:] if len(args) > 2 else args[1:]
            for arg in display_args:
                arg_parts.append(str(arg))
        for key, value in kwargs.items():
            arg_parts.append(f"{key}={value}")
        args_str = ", ".join(arg_parts) if arg_parts else ""
        
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                "DB_OP | %s.%s | duration=%.3fms | args=(%s)",
                func.__qualname__,
                func.__name__,
                elapsed_ms,
                args_str
            )
            return result
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "DB_OP | %s.%s | duration=%.3fms | args=(%s) | error=%s",
                func.__qualname__,
                func.__name__,
                elapsed_ms,
                args_str,
                str(e)
            )
            raise
    return wrapper  # type: ignore[return-value]
