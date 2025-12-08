"""
Centralized logging configuration for the LLM Cost Platform.

Usage:
    from .logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("Message")

Log levels:
    DEBUG   - Detailed API calls, token counts, timing
    INFO    - Experiment progress, pipeline results
    WARNING - Rate limits, retries, fallbacks
    ERROR   - Failed API calls, exceptions
"""

import logging
import sys
from typing import Optional

# Default format for all loggers
DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%H:%M:%S"

# Root logger name for the project
ROOT_LOGGER_NAME = "llm_cost"

# Track if logging has been configured
_configured = False


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    date_format: Optional[str] = None,
) -> None:
    """
    Configure logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string (optional)
        date_format: Custom date format (optional)

    This should be called once at application startup (e.g., in CLI main()).
    """
    global _configured

    if _configured:
        return

    log_level = getattr(logging, level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger(ROOT_LOGGER_NAME)
    root_logger.setLevel(log_level)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Set format
    formatter = logging.Formatter(
        fmt=format_string or DEFAULT_FORMAT,
        datefmt=date_format or DEFAULT_DATE_FORMAT,
    )
    handler.setFormatter(formatter)

    # Add handler if not already present
    if not root_logger.handlers:
        root_logger.addHandler(handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance under the llm_cost namespace

    Example:
        logger = get_logger(__name__)
        logger.info("Starting experiment")
    """
    # Ensure logging is configured with defaults
    if not _configured:
        setup_logging()

    # Create child logger under root namespace
    if name.startswith("src."):
        name = name[4:]  # Remove 'src.' prefix for cleaner names

    return logging.getLogger(f"{ROOT_LOGGER_NAME}.{name}")


def set_level(level: str) -> None:
    """
    Change the log level at runtime.

    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger = logging.getLogger(ROOT_LOGGER_NAME)
    root_logger.setLevel(log_level)
    for handler in root_logger.handlers:
        handler.setLevel(log_level)
