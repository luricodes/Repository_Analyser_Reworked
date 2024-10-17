# repo_analyzer/cache/sqlite_cache.py

import json
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from colorama import Fore, Style

def initialize_db(db_path: str) -> sqlite3.Connection:
    """
    Initialisiert die SQLite-Datenbank und erstellt die
    erforderliche Tabelle, falls sie nicht existiert.
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                file_path TEXT PRIMARY KEY,
                file_hash TEXT,
                hash_algorithm TEXT,
                file_info TEXT,
                size INTEGER,
                mtime REAL
            )
            """
        )
    return conn

def get_cached_entry(
    conn: sqlite3.Connection, file_path: str
) -> Optional[Tuple[Optional[str], Optional[str], str, Optional[int], Optional[float]]]:
    """
    Ruft den gespeicherten Hash, Hash-Algorithmus, file_info, size und mtime für eine Datei aus dem Cache ab.

    Args:
        conn (sqlite3.Connection): Die SQLite-Verbindung.
        file_path (str): Der Pfad zur Datei.

    Returns:
        Optional[Tuple[Optional[str], Optional[str], str, Optional[int], Optional[float]]]: 
            Tuple bestehend aus file_hash, hash_algorithm, file_info_json, size und mtime.
            Oder None, wenn kein Eintrag gefunden wurde.
    """
    with conn:
        cursor = conn.execute(
            "SELECT file_hash, hash_algorithm, file_info, size, mtime FROM cache WHERE file_path = ?",
            (file_path,),
        )
        result = cursor.fetchone()
    return result if result else None

def set_cached_entry(
    conn: sqlite3.Connection,
    file_path: str,
    file_hash: Optional[str],
    hash_algorithm: Optional[str],
    file_info: Dict[str, Any],
    size: int,
    mtime: float,
) -> None:
    """
    Aktualisiert oder fügt den Hash, Hash-Algorithmus, file_info, size und mtime einer Datei im Cache hinzu.

    Args:
        conn (sqlite3.Connection): Die SQLite-Verbindung.
        file_path (str): Der Pfad zur Datei.
        file_hash (Optional[str]): Der Hash der Datei oder None.
        hash_algorithm (Optional[str]): Der Hash-Algorithmus oder None.
        file_info (Dict[str, Any]): Die Informationen zur Datei.
        size (int): Die Größe der Datei in Bytes.
        mtime (float): Die letzte Änderungszeit der Datei.
    """
    file_info_json = json.dumps(file_info)
    with conn:
        conn.execute(
            """
            INSERT INTO cache (file_path, file_hash, hash_algorithm, file_info, size, mtime)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(file_path) DO UPDATE SET
                file_hash = excluded.file_hash,
                hash_algorithm = excluded.hash_algorithm,
                file_info = excluded.file_info,
                size = excluded.size,
                mtime = excluded.mtime
            """,
            (file_path, file_hash, hash_algorithm, file_info_json, size, mtime),
        )

def clean_cache(
    conn: sqlite3.Connection, root_dir: Path, lock: threading.Lock
) -> None:
    """
    Bereinigt den Cache, indem Einträge entfernt werden,
    die nicht mehr existieren.

    Args:
        conn (sqlite3.Connection): Die SQLite-Verbindung.
        root_dir (Path): Das Wurzelverzeichnis.
        lock (threading.Lock): Lock für den Zugriff auf den Cache.
    """
    with conn:
        cursor = conn.execute("SELECT file_path FROM cache")
        cached_files = {row[0] for row in cursor.fetchall()}

    existing_files = {str(p.resolve()) for p in root_dir.rglob("*") if p.is_file()}
    files_to_remove = cached_files - existing_files

    if files_to_remove:
        with lock:
            with conn:
                conn.executemany(
                    "DELETE FROM cache WHERE file_path = ?",
                    ((fp,) for fp in files_to_remove),
                )
            logging.info(
                f"{Fore.GREEN}Cache bereinigt. {len(files_to_remove)} Einträge entfernt.{Style.RESET_ALL}"
            )
