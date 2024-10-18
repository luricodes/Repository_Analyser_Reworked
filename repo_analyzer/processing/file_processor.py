# repo_analyzer/processing/file_processor.py

import base64
import json
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple

from colorama import Fore, Style

from ..cache.sqlite_cache import get_cached_entry, set_cached_entry
from ..processing.hashing import compute_file_hash
from ..utils.mime_type import is_binary
from repo_analyzer.cache.sqlite_cache import get_connection_context


def process_file(
    file_path: Path,
    max_file_size: int,
    include_binary: bool,
    image_extensions: Set[str],
    encoding: str = 'utf-8',
    hash_algorithm: Optional[str] = "md5",
) -> Tuple[str, Optional[Dict[str, Any]]]:
    filename = file_path.name

    try:
        stat = file_path.stat()
        current_size = stat.st_size
        current_mtime = stat.st_mtime
    except Exception as e:
        logging.warning(f"Konnte Metadaten nicht abrufen: {file_path} - {e}")
        return filename, None

    if current_size > max_file_size:
        logging.info(f"Datei zu groß und wird ausgeschlossen: {file_path} ({current_size} Bytes)")
        return filename, None

    file_hash = None
    file_info = None

    if hash_algorithm is not None:
        with get_connection_context() as conn:
            cached_entry = get_cached_entry(conn, str(file_path.resolve()))

        if cached_entry:
            cached_hash = cached_entry.get("file_hash")
            cached_algorithm = cached_entry.get("hash_algorithm")
            cached_info = cached_entry.get("file_info")
            cached_size = cached_entry.get("size")
            cached_mtime = cached_entry.get("mtime")

            if (cached_size == current_size and
                cached_mtime == current_mtime and
                cached_algorithm == hash_algorithm):
                try:
                    file_info = cached_info
                    logging.debug(f"Cache-Treffer für Datei: {file_path}")
                    return filename, file_info
                except Exception as e:
                    logging.warning(f"Fehler beim Dekodieren der gecachten Dateiinfo für {file_path}: {e}")
            else:
                logging.debug(f"Datei geändert seit letztem Cache-Eintrag: {file_path}")
        else:
            logging.debug(f"Kein Cache-Eintrag für Datei: {file_path}")

    file_hash = compute_file_hash(file_path, algorithm=hash_algorithm)
    file_extension = file_path.suffix.lower()
    is_image = file_extension in image_extensions

    try:
        binary = is_binary(file_path)

        if (binary or is_image) and not include_binary:
            logging.debug(f"Ausschließen von {'binär' if binary else 'Bild'} Datei: {file_path}")
            return filename, None

        file_info = {}
        if binary:
            with open(file_path, 'rb') as f:
                content = base64.b64encode(f.read(max_file_size)).decode('utf-8')
            file_info = {
                "type": "binary",
                "content": content
            }
            logging.debug(f"Eingeschlossene binäre Datei: {file_path}")
        else:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read(max_file_size)
            logging.debug(f"Eingelesene Textdatei: {file_path}")
            file_info = {
                "type": "text",
                "content": content
            }
    except UnicodeDecodeError as e:
        logging.warning(f"UnicodeDecodeError bei Datei {file_path}: {e}")
        return filename, None
    except (PermissionError, IsADirectoryError) as e:
        logging.warning(f"Konnte den Inhalt nicht lesen: {file_path} - {e}")
        return filename, None
    except Exception as e:
        logging.error(f"Fehler beim Verarbeiten der Datei {file_path}: {e}")
        return filename, None

    try:
        file_info.update({
            "size": current_size,
            "created": getattr(stat, 'st_birthtime', None),
            "modified": current_mtime,
            "permissions": oct(stat.st_mode)
        })
    except Exception as e:
        logging.warning(f"Konnte Metadaten nicht abrufen für: {file_path} - {e}")

    if hash_algorithm is not None and file_hash is not None:
        with get_connection_context() as conn:
            set_cached_entry(
                conn,
                str(file_path.resolve()),
                file_hash,
                hash_algorithm,
                file_info,
                current_size,
                current_mtime
            )

    return filename, file_info
