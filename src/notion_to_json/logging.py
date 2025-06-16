"""Logging configuration for notion-to-json."""

import logging
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

# Global console instance
console = Console(stderr=True)


def setup_logging(
    verbose: bool = False,
    quiet: bool = False,
    log_file: Path | None = None,
) -> None:
    """Configure logging for the application.

    Args:
        verbose: Enable verbose logging (DEBUG level)
        quiet: Minimize output (ERROR level only)
        log_file: Optional file to write logs to
    """
    # Determine log level
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler with Rich formatting
    if not quiet:
        console_handler = RichHandler(
            console=console,
            show_time=verbose,
            show_path=verbose,
            markup=True,
            rich_tracebacks=True,
            tracebacks_show_locals=verbose,
        )
        console_handler.setLevel(level)
        console_formatter = logging.Formatter("%(message)s")
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Configure specific loggers
    # Silence httpx unless verbose
    if not verbose:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
