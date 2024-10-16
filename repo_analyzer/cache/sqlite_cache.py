# repo_analyzer/cache/sqlite_cache.py

import sqlite3
import json
from typing import Optional, Tuple, Dict, Any
import logging
from colorama import Fore, Style
from pathlib import Path
import threading

def initialize_db(db_path: str) -> sqlite3.Connection:
    """
    Initialisiert die SQLite-Datenbank und erstellt die erforderliche Tabelle, falls sie nicht existiert.
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cache (
            file_path TEXT PRIMARY KEY,
            file_hash TEXT,
            file_info TEXT
        )
    ''')
    conn.commit()
    return conn

def get_cached_entry(conn: sqlite3.Connection, file_path: str) -> Optional[Tuple[str, str]]:
    """
    Ruft den gespeicherten Hash und file_info für eine Datei aus dem Cache ab.
    """
    cursor = conn.cursor()
    cursor.execute('SELECT file_hash, file_info FROM cache WHERE file_path = ?', (file_path,))
    result = cursor.fetchone()
    return result if result else None

def set_cached_entry(conn: sqlite3.Connection, file_path: str, file_hash: str, file_info: Dict[str, Any]) -> None:
    """
    Aktualisiert oder fügt den Hash und file_info einer Datei im Cache hinzu.
    """
    file_info_json = json.dumps(file_info)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO cache (file_path, file_hash, file_info)
        VALUES (?, ?, ?)
        ON CONFLICT(file_path) DO UPDATE SET
            file_hash=excluded.file_hash,
            file_info=excluded.file_info
    ''', (file_path, file_hash, file_info_json))
    conn.commit()

def clean_cache(conn: sqlite3.Connection, root_dir: Path, lock: threading.Lock) -> None:
    """
    Bereinigt den Cache, indem Einträge entfernt werden, die nicht mehr existieren.
    """
    cursor = conn.cursor()
    cursor.execute('SELECT file_path FROM cache')
    cached_files = set(row[0] for row in cursor.fetchall())
    existing_files = set(str(p.resolve()) for p in root_dir.rglob('*') if p.is_file())
    files_to_remove = cached_files - existing_files
    if files_to_remove:
        with lock:
            cursor.executemany('DELETE FROM cache WHERE file_path = ?', [(fp,) for fp in files_to_remove])
            conn.commit()
        logging.info(f"{Fore.GREEN}Cache bereinigt. {len(files_to_remove)} Einträge entfernt.{Style.RESET_ALL}")