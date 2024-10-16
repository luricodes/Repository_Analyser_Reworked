# repo_analyzer/processing/file_processor.py

import base64
import json
import logging
import sqlite3
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List
from colorama import Fore, Style
from ..cache.sqlite_cache import get_cached_entry, set_cached_entry
from ..processing.hashing import compute_file_hash
from ..utils.mime_type import get_magic_instance, is_binary
from ..utils.helpers import is_binary_alternative
import threading

def process_file(
    file_path: Path,
    max_file_size: int,
    include_binary: bool,
    image_extensions: set,
    conn: sqlite3.Connection,
    lock: threading.Lock,
    encoding: str = 'utf-8'
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Verarbeitet eine einzelne Datei und gibt deren Informationen zurück.
    """
    filename = file_path.name

    # Prüfe den Cache
    file_hash = compute_file_hash(file_path)
    cached_entry = None
    if file_hash is not None:
        with lock:
            cached_entry = get_cached_entry(conn, str(file_path.resolve()))
    if file_hash is not None and cached_entry and cached_entry[0] == file_hash:
        logging.debug(f"{Fore.BLUE}Cache-Treffer für Datei: {file_path}{Style.RESET_ALL}")
        # Load file_info from cached_entry
        try:
            cached_file_info = json.loads(cached_entry[1])
            return filename, cached_file_info
        except json.JSONDecodeError as e:
            logging.warning(f"{Fore.YELLOW}Fehler beim Dekodieren der gecachten Dateiinfo für {file_path}: {e}{Style.RESET_ALL}")
            # Proceed to re-process the file

    file_extension = file_path.suffix.lower()

    # Prüfe, ob die Datei eine Bilddatei ist
    is_image = file_extension in image_extensions

    # Prüfe, ob die Datei binär ist
    binary = is_binary(file_path)

    # Wenn die Datei binär oder ein Bild ist und include_binary nicht gesetzt ist, überspringen
    if (binary or is_image) and not include_binary:
        logging.debug(f"{Fore.YELLOW}Ausschließen von {'binär' if binary else 'Bild'} Datei: {file_path}{Style.RESET_ALL}")
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
            logging.debug(f"{Fore.GREEN}Eingeschlossene binäre Datei: {file_path}{Style.RESET_ALL}")
        else:
            stat = file_path.stat()
            if stat.st_size > max_file_size:
                content = "<Datei zu groß zum Lesen>"
                logging.info(f"{Fore.YELLOW}Datei zu groß: {file_path} ({stat.st_size} Bytes){Style.RESET_ALL}")
            else:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                logging.debug(f"{Fore.GREEN}Eingelesene Textdatei: {file_path}{Style.RESET_ALL}")
            file_info = {
                "type": "text",
                "content": content
            }
    except UnicodeDecodeError as e:
        logging.warning(f"{Fore.YELLOW}UnicodeDecodeError bei Datei {file_path}: {e}{Style.RESET_ALL}")
        file_info = {
            "type": "unknown",
            "content": f"<UnicodeDecodeError: {str(e)}>"
        }
    except (PermissionError, IsADirectoryError) as e:
        file_info = {
            "type": "unknown",
            "content": f"<Konnte den Inhalt nicht lesen: {str(e)}>"
        }
        logging.warning(f"{Fore.YELLOW}Konnte den Inhalt nicht lesen: {file_path} - {e}{Style.RESET_ALL}")
    except Exception as e:
        file_info = {
            "type": "error",
            "content": f"<Fehler: {str(e)}>"
        }
        logging.error(f"{Fore.RED}Fehler beim Verarbeiten der Datei {file_path}: {e}{Style.RESET_ALL}")

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
        logging.warning(f"{Fore.YELLOW}Konnte Metadaten nicht abrufen für: {file_path} - {e}{Style.RESET_ALL}")

    # Aktualisiere den Cache
    if file_hash is not None:
        with lock:
            set_cached_entry(conn, str(file_path.resolve()), file_hash, file_info)

    return filename, file_info