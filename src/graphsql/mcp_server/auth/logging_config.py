"""Logging configuration for the auth module.

This module provides centralized logging configuration using loguru,
with support for different log levels, file output, and structured logging.

Example:
    >>> from graphsql.mcp_server.auth.logging_config import configure_logging
    >>> configure_logging(level="DEBUG", log_file="auth.log")
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from loguru import logger


def configure_logging(
    level: str = "INFO",
    log_file: str | Path | None = None,
    json_format: bool = False,
    rotation: str = "10 MB",
    retention: str = "7 days",
    compression: str = "gz",
    colorize: bool = True,
    diagnose: bool = True,
    backtrace: bool = True,
) -> None:
    """Configure loguru logging for the auth module.

    This function sets up loguru with appropriate handlers for console
    and optional file output. It removes existing handlers first to
    ensure clean configuration.

    Args:
        level: Minimum log level (TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to log file. If None, only console output is used.
        json_format: If True, output logs in JSON format (useful for log aggregation).
        rotation: When to rotate log files (e.g., "10 MB", "1 day", "12:00").
        retention: How long to keep rotated logs (e.g., "7 days", "10 files").
        compression: Compression format for rotated logs ("gz", "bz2", "xz", "zip").
        colorize: Whether to colorize console output.
        diagnose: Whether to include variable values in exception traces.
        backtrace: Whether to include full backtrace in exception traces.

    Example:
        >>> # Simple console logging at DEBUG level
        >>> configure_logging(level="DEBUG")

        >>> # Production config with file output and JSON format
        >>> configure_logging(
        ...     level="INFO",
        ...     log_file="/var/log/graphsql/auth.log",
        ...     json_format=True,
        ... )
    """
    # Remove all existing handlers
    logger.remove()

    # Console format
    if json_format:
        console_format = "{message}"
        serialize = True
    else:
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        serialize = False

    # Add console handler
    logger.add(
        sys.stderr,
        format=console_format,
        level=level,
        colorize=colorize and not json_format,
        serialize=serialize,
        diagnose=diagnose,
        backtrace=backtrace,
    )

    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        if json_format:
            file_format = "{message}"
        else:
            file_format = (
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                "{level: <8} | "
                "{name}:{function}:{line} | "
                "{message}"
            )

        logger.add(
            str(log_path),
            format=file_format,
            level=level,
            rotation=rotation,
            retention=retention,
            compression=compression,
            serialize=json_format,
            diagnose=diagnose,
            backtrace=backtrace,
            enqueue=True,  # Thread-safe writing
        )

        logger.info(
            "File logging configured",
            log_file=str(log_path),
            rotation=rotation,
            retention=retention,
            compression=compression,
        )

    logger.info(
        "Logging configured",
        level=level,
        json_format=json_format,
        file_output=log_file is not None,
    )


def add_context(
    **kwargs: Any,
) -> Any:
    """Add context to all subsequent log messages.

    This is useful for adding request-scoped context like user IDs,
    request IDs, or correlation IDs.

    Args:
        **kwargs: Context key-value pairs to add.

    Returns:
        Context manager that removes the context on exit.

    Example:
        >>> with add_context(user_id="user123", request_id="req-abc"):
        ...     logger.info("Processing request")  # Includes user_id and request_id
    """
    return logger.contextualize(**kwargs)


def log_exception(
    message: str = "An exception occurred",
    **kwargs: Any,
) -> None:
    """Log an exception with full traceback and context.

    This should be called within an exception handler to capture
    the current exception with its full traceback.

    Args:
        message: Log message describing the error context.
        **kwargs: Additional context to include in the log.

    Example:
        >>> try:
        ...     do_something_risky()
        ... except Exception:
        ...     log_exception("Failed to complete operation", operation="risky")
    """
    logger.opt(exception=True).error(message, **kwargs)


def log_timing(
    operation: str,
    duration_ms: float,
    **kwargs: Any,
) -> None:
    """Log operation timing for performance monitoring.

    Args:
        operation: Name of the operation being timed.
        duration_ms: Duration in milliseconds.
        **kwargs: Additional context to include.

    Example:
        >>> start = time.time()
        >>> result = do_operation()
        >>> log_timing("database_query", (time.time() - start) * 1000, table="users")
    """
    if duration_ms < 100:
        logger.debug(
            "Operation timing",
            operation=operation,
            duration_ms=round(duration_ms, 2),
            **kwargs,
        )
    elif duration_ms < 1000:
        logger.info(
            "Operation timing",
            operation=operation,
            duration_ms=round(duration_ms, 2),
            **kwargs,
        )
    else:
        logger.warning(
            "Slow operation detected",
            operation=operation,
            duration_ms=round(duration_ms, 2),
            **kwargs,
        )


# Export commonly used logger
__all__ = [
    "configure_logging",
    "add_context",
    "log_exception",
    "log_timing",
    "logger",
]
