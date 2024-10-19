# repo_analyzer/logging/setup.py

import logging
import sys
import os
from typing import Optional

from colorama import Fore, Style
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
    Konfiguriert das Logging-Modul mit separaten Handlern für Konsole und Datei.

    :param verbose: Wenn True, wird der Log-Level auf DEBUG gesetzt, sonst auf INFO.
    :param log_file: Optionaler Pfad zur Log-Datei.
    :param file_level: Log-Level für den Datei-Handler. Standard: DEBUG.
    :param max_bytes: Maximale Dateigröße in Bytes für den rotierenden Datei-Handler. Standard: 5 MB.
    :param backup_count: Anzahl der Backup-Dateien für den rotierenden Datei-Handler. Standard: 5.
    """
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    log_level = logging.DEBUG if verbose else logging.INFO
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Entfernt alle bestehenden Handler, um doppelte Logs zu vermeiden
    if logger.hasHandlers():
        logger.handlers.clear()

    # Format für Konsolen-Logs mit Farben
    console_formatter = ColorFormatter(fmt=log_format, datefmt=date_format)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    if log_file:
        try:
            # Sicherstellen, dass das Log-Verzeichnis existiert
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            # Format für Datei-Logs ohne Farben
            file_formatter = logging.Formatter(fmt=log_format, datefmt=date_format)

            # Rotating File Handler
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(file_level)  # Datei-Handler speichert alle Logs ab file_level
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except (IOError, OSError) as e:
            logger.error(f"Failed to set up file handler: {e}")
