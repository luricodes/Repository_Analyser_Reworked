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
    hash_algorithm: Optional[str] = "md5",  # Neuer Parameter
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Verarbeitet eine einzelne Datei und gibt deren Informationen zurück.

    Args:
        file_path (Path): Pfad zur Datei.
        max_file_size (int): Maximale Dateigröße in Bytes.
        include_binary (bool): Gibt an, ob binäre Dateien eingeschlossen werden sollen.
        image_extensions (Set[str]): Set von Bilddateiendungen.
        conn (sqlite3.Connection): SQLite-Verbindung.
        lock (threading.Lock): Lock für den Zugriff auf den Cache.
        encoding (str, optional): Encoding für Textdateien.
        hash_algorithm (Optional[str], optional): Hash-Algorithmus oder None.

    Returns:
        Tuple[str, Optional[Dict[str, Any]]]: Dateiname und Datei-Info oder None.
    """
    filename = file_path.name

    # Prüfe den Cache nur, wenn Hashing aktiviert ist
    if hash_algorithm is not None:
        file_hash = compute_file_hash(file_path, algorithm=hash_algorithm)
        cached_entry = None
        if file_hash is not None:
            with lock:
                cached_entry = get_cached_entry(conn, str(file_path.resolve()))
        
        if (file_hash is not None and cached_entry 
            and cached_entry[0] == file_hash 
            and cached_entry[1] == hash_algorithm):
            logging.debug(
                f"{Fore.BLUE}Cache-Treffer für Datei: {file_path}{Style.RESET_ALL}"
            )
            # Lade file_info aus cached_entry
            try:
                cached_file_info = json.loads(cached_entry[2])
                return filename, cached_file_info
            except json.JSONDecodeError as e:
                logging.warning(
                    f"{Fore.YELLOW}Fehler beim Dekodieren der gecachten Dateiinfo für "
                    f"{file_path}: {e}{Style.RESET_ALL}"
                )
                # Weiter zur erneuten Verarbeitung der Datei

    file_extension = file_path.suffix.lower()

    # Prüfe, ob die Datei eine Bilddatei ist
    is_image = file_extension in image_extensions

    # Prüfe, ob die Datei binär ist
    binary = is_binary(file_path)

    # Wenn die Datei binär oder ein Bild ist und include_binary nicht gesetzt ist, überspringen
    if (binary or is_image) and not include_binary:
        logging.debug(
            f"{Fore.YELLOW}Ausschließen von {'binär' if binary else 'Bild'} "
            f"Datei: {file_path}{Style.RESET_ALL}"
        )
        return filename, None  # Rückgabe von None signalisiert, dass die Datei übersprungen wird

    file_info: Dict[str, Any] = {}

    try:
        if binary:
            with open(file_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('utf-8')
            file_info = {
                "type": "binary",
                "content": content
            }
            logging.debug(
                f"{Fore.GREEN}Eingeschlossene binäre Datei: {file_path}{Style.RESET_ALL}"
            )
        else:
            stat = file_path.stat()
            if stat.st_size > max_file_size:
                content = "<Datei zu groß zum Lesen>"
                logging.info(
                    f"{Fore.YELLOW}Datei zu groß: {file_path} "
                    f"({stat.st_size} Bytes){Style.RESET_ALL}"
                )
            else:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                logging.debug(
                    f"{Fore.GREEN}Eingelesene Textdatei: {file_path}{Style.RESET_ALL}"
                )
            file_info = {
                "type": "text",
                "content": content
            }
    except UnicodeDecodeError as e:
        logging.warning(
            f"{Fore.YELLOW}UnicodeDecodeError bei Datei {file_path}: "
            f"{e}{Style.RESET_ALL}"
        )
        file_info = {
            "type": "unknown",
            "content": f"<UnicodeDecodeError: {str(e)}>"
        }
    except (PermissionError, IsADirectoryError) as e:
        file_info = {
            "type": "unknown",
            "content": f"<Konnte den Inhalt nicht lesen: {str(e)}>"
        }
        logging.warning(
            f"{Fore.YELLOW}Konnte den Inhalt nicht lesen: {file_path} - "
            f"{e}{Style.RESET_ALL}"
        )
    except Exception as e:
        file_info = {
            "type": "error",
            "content": f"<Fehler: {str(e)}>"
        }
        logging.error(
            f"{Fore.RED}Fehler beim Verarbeiten der Datei {file_path}: "
            f"{e}{Style.RESET_ALL}"
        )

    # Füge Metadaten hinzu
    try:
        stat = file_path.stat()
        file_info.update({
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "permissions": oct(stat.st_mode)
        })
    except Exception as e:
        logging.warning(
            f"{Fore.YELLOW}Konnte Metadaten nicht abrufen für: {file_path} - "
            f"{e}{Style.RESET_ALL}"
        )

    # Aktualisiere den Cache nur, wenn Hashing aktiviert ist
    if hash_algorithm is not None and file_hash is not None:
        with lock:
            set_cached_entry(conn, str(file_path.resolve()), file_hash, hash_algorithm, file_info)

    return filename, file_info
