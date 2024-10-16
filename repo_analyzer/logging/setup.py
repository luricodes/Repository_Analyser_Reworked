# repo_analyzer/logging/setup.py

import logging
import sys
from typing import Optional

from colorama import Fore, Style, init as colorama_init
from logging.handlers import RotatingFileHandler


class ColorFormatter(logging.Formatter):
    """Custom formatter to add colors to console logs based on log level.

    Fügt den Konsolenlogs Farben hinzu, die dem Log-Level entsprechen.
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
        message = f"{color}{record.getMessage()}{Style.RESET_ALL}"
        record.message = message
        return super().format(record)


def setup_logging(verbose: bool, log_file: Optional[str] = None) -> None:
    """
    Konfiguriert das Logging-Modul mit separaten Handlern für Konsole und Datei.

    :param verbose: Wenn True, wird der Log-Level auf DEBUG gesetzt, sonst auf INFO.
    :param log_file: Optionaler Pfad zur Log-Datei.
    """
    # Initialize colorama for colored console output
    colorama_init(autoreset=True)

    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    log_level = logging.DEBUG if verbose else logging.INFO
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Entfernt alle bestehenden Handler, um doppelte Logs zu vermeiden
    if logger.hasHandlers():
        logger.handlers.clear()

    # Format für Konsolen-Logs mit Farben
    console_formatter = ColorFormatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    if log_file:
        # Format für Datei-Logs ohne Farben
        file_formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

        # Rotating File Handler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)  # Datei-Handler speichert alle Logs
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
