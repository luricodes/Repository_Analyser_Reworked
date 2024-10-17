# repo_analyzer/utils/mime_type.py

import magic
import threading
from colorama import Fore, Style
import logging
from pathlib import Path
from .helpers import is_binary_alternative

thread_local_data = threading.local()

def get_magic_instance():
    if not hasattr(thread_local_data, 'mime'):
        try:
            thread_local_data.mime = magic.Magic(mime=True)
        except Exception as e:
            logging.error(f"{Fore.RED}Fehler beim Initialisieren von magic: {e}{Style.RESET_ALL}")
            thread_local_data.mime = None
    return thread_local_data.mime

def is_binary(file_path: Path) -> bool:
    """
    Prüft, ob eine Datei binär ist, basierend auf dem MIME-Typ.
    Falls die MIME-Erkennung fehlschlägt, verwendet sie eine alternative Methode.
    """
    try:
        mime = get_magic_instance()
        if mime is None:
            return is_binary_alternative(file_path)
        
        # Lese nur die ersten 8192 Bytes der Datei
        with open(file_path, 'rb') as f:
            file_content = f.read(8192)
        
        mime_type = mime.from_buffer(file_content)
        logging.debug(f"Datei: {file_path} - MIME-Typ: {mime_type}")
        return not mime_type.startswith('text/')
    except Exception as e:
        logging.warning(f"{Fore.YELLOW}Fehler bei der Erkennung des MIME-Typs für {file_path}: {e}{Style.RESET_ALL}")
        # Alternative Methode zur Binärprüfung
        return is_binary_alternative(file_path)
