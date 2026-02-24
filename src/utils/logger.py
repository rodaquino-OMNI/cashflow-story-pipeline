"""Structured logging setup using structlog."""

import logging
import logging.config

import structlog


def setup_logging(
    level: int = logging.INFO,
    log_file: str | None = None,
    structured: bool = True
) -> None:
    """
    Setup structured logging with structlog.

    Configures:
    - Console output with colors
    - Optional file logging
    - Structured JSON logging
    - Performance tracking
    - Request tracing

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for log output
        structured: Use structured JSON logging (default True)

    Example:
        setup_logging(level=logging.DEBUG, log_file="app.log")
        logger = logging.getLogger(__name__)
        logger.info("Processing", extra={"stage": 1, "records": 100})

    TODO: Configure logging.basicConfig
    TODO: Setup structlog processors (JSON, pretty-print)
    TODO: Configure console and file handlers
    TODO: Setup performance tracking
    TODO: Configure request correlation IDs
    """

    # Basic logging configuration
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "structured": {
                "()": structlog.processors.JSONRenderer,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "structured" if structured else "standard",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": level,
            "handlers": ["console"],
        },
    }

    # Add file handler if specified
    if log_file:
        logging_config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "level": level,
            "formatter": "structured" if structured else "standard",
            "filename": log_file,
        }
        logging_config["root"]["handlers"].append("file")

    # Apply configuration
    logging.config.dictConfig(logging_config)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if structured else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    """Return a structlog bound logger for the given module name."""
    return structlog.get_logger(name)
