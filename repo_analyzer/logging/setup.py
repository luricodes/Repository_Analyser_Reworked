# repo_analyzer/logging/setup.py

import logging
import sys
import os
from typing import Optional

from colorama import Fore, Style
from logging.handlers import RotatingFileHandler


class ColorFormatter(logging.Formatter):
    """Custom formatter to add colors to console logs based on log level.
    """

    LEVEL_COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA,
    }

    def __init__(self, fmt: str, datefmt: Optional[str] = None) -> None:
        super().__init__(fmt, datefmt)

    def format(self, record: logging.LogRecord) -> str:
        color = self.LEVEL_COLORS.get(record.levelno, Fore.WHITE)
        colored_message = f"{color}{record.getMessage()}{Style.RESET_ALL}"
        original_message = record.getMessage()
        record.message = colored_message
        try:
            formatted = super().format(record)
        finally:
            record.message = original_message  # Restore original message
        return formatted


def setup_logging(
    verbose: bool,
    log_file: Optional[str] = None,
    file_level: int = logging.DEBUG,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    """
    Configures the logging module with separate handlers for console and file.

    :param verbose: If True, the log level is set to DEBUG, otherwise to INFO.
    :param log_file: Optional path to the log file.
    :param file_level: Log level for the file handler. Standard: DEBUG.
    :param max_bytes: Maximum file size in bytes for the rotating file handler. Standard: 5 MB.
    :param backup_count: Number of backup files for the rotating file handler. Standard: 5.
    """
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    log_level = logging.DEBUG if verbose else logging.INFO
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Removes all existing handlers to avoid duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    # Format for console logs with colours
    console_formatter = ColorFormatter(fmt=log_format, datefmt=date_format)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    if log_file:
        try:
            # Ensure that the log directory exists
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            # Format for file logs without colours
            file_formatter = logging.Formatter(fmt=log_format, datefmt=date_format)

            # Rotating File Handler
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(file_level)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except (IOError, OSError) as e:
            logger.error(f"Failed to set up file handler: {e}")
