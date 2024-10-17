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

def process_file(
    file_path: Path,
    max_file_size: int,
    include_binary: bool,
    image_extensions: Set[str],
    conn: sqlite3.Connection,
    lock: threading.Lock,
    encoding: str = 'utf-8',
    hash_algorithm: Optional[str] = "md5",
) -> Tuple[str, Optional[Dict[str, Any]]]:
    filename = file_path.name

    try:
        stat = file_path.stat()
        current_size = stat.st_size
        current_mtime = stat.st_mtime
    except Exception as e:
        logging.warning(
            f"{Fore.YELLOW}Konnte Metadaten nicht abrufen: {file_path} - {e}{Style.RESET_ALL}"
        )
        return filename, None

    # **Überprüfung der Dateigröße**
    if current_size > max_file_size:
        logging.info(
            f"{Fore.YELLOW}Datei zu groß und wird ausgeschlossen: {file_path} ({current_size} Bytes){Style.RESET_ALL}"
        )
        return filename, None  # Datei wird ausgeschlossen

    file_hash = None
    cached_info = None

    if hash_algorithm is not None:
        with lock:
            cached_entry = get_cached_entry(conn, str(file_path.resolve()))
        
        if cached_entry:
            cached_hash, cached_algorithm, cached_info_json, cached_size, cached_mtime = cached_entry
            if (cached_size == current_size and
                cached_mtime == current_mtime and
                cached_algorithm == hash_algorithm):
                try:
                    cached_info = json.loads(cached_info_json)
                    logging.debug(
                        f"{Fore.BLUE}Cache-Treffer für Datei: {file_path}{Style.RESET_ALL}"
                    )
                    return filename, cached_info
                except json.JSONDecodeError as e:
                    logging.warning(
                        f"{Fore.YELLOW}Fehler beim Dekodieren der gecachten Dateiinfo für {file_path}: {e}{Style.RESET_ALL}"
                    )
            else:
                logging.debug(
                    f"{Fore.GREEN}Datei geändert seit letztem Cache-Eintrag: {file_path}{Style.RESET_ALL}"
                )
        else:
            logging.debug(
                f"{Fore.GREEN}Kein Cache-Eintrag für Datei: {file_path}{Style.RESET_ALL}"
            )

        # Nur wenn kein gültiger Cache-Treffer vorliegt, den Hash berechnen
        file_hash = compute_file_hash(file_path, algorithm=hash_algorithm)

    file_extension = file_path.suffix.lower()

    # Prüfe, ob die Datei eine Bilddatei ist
    is_image = file_extension in image_extensions

    try:
        # Prüfe, ob die Datei binär ist
        binary = is_binary(file_path)

        # Wenn die Datei binär oder ein Bild ist und include_binary nicht gesetzt ist, überspringen
        if (binary or is_image) and not include_binary:
            logging.debug(
                f"{Fore.YELLOW}Ausschließen von {'binär' if binary else 'Bild'} Datei: {file_path}{Style.RESET_ALL}"
            )
            return filename, None  # Datei wird ausgeschlossen

        file_info: Dict[str, Any] = {}

        if binary:
            # Verarbeitung binärer Dateien
            with open(file_path, 'rb') as f:
                content = base64.b64encode(f.read(max_file_size)).decode('utf-8')
            file_info = {
                "type": "binary",
                "content": content
            }
            logging.debug(
                f"{Fore.GREEN}Eingeschlossene binäre Datei: {file_path}{Style.RESET_ALL}"
            )
        else:
            # Verarbeitung von Textdateien
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read(max_file_size)
            logging.debug(
                f"{Fore.GREEN}Eingelesene Textdatei: {file_path}{Style.RESET_ALL}"
            )
            file_info = {
                "type": "text",
                "content": content
            }
    except UnicodeDecodeError as e:
        logging.warning(
            f"{Fore.YELLOW}UnicodeDecodeError bei Datei {file_path}: {e}{Style.RESET_ALL}"
        )
        return filename, None
    except (PermissionError, IsADirectoryError) as e:
        logging.warning(
            f"{Fore.YELLOW}Konnte den Inhalt nicht lesen: {file_path} - {e}{Style.RESET_ALL}"
        )
        return filename, None
    except Exception as e:
        logging.error(
            f"{Fore.RED}Fehler beim Verarbeiten der Datei {file_path}: {e}{Style.RESET_ALL}"
        )
        return filename, None

    # Füge Metadaten hinzu
    try:
        file_info.update({
            "size": current_size,
            "created": stat.st_birthtime,
            "modified": current_mtime,
            "permissions": oct(stat.st_mode)
        })
    except Exception as e:
        logging.warning(
            f"{Fore.YELLOW}Konnte Metadaten nicht abrufen für: {file_path} - {e}{Style.RESET_ALL}"
        )

    # Aktualisiere den Cache nur, wenn Hashing aktiviert ist und Hash berechnet wurde
    if hash_algorithm is not None and file_hash is not None:
        with lock:
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
