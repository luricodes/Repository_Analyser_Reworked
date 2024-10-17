# repo_analyzer/cache/sqlite_cache.py

import json
import logging
import sqlite3
import sys
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from colorama import Fore, Style, init as colorama_init

# Initialize colorama
colorama_init(autoreset=True)

# Determine if the output is a TTY to decide on color usage
USE_COLOR = sys.stdout.isatty()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Thread-local storage for database connections
_thread_local = threading.local()

def get_db_connection(db_path: str) -> sqlite3.Connection:
    """
    Retrieves a thread-local SQLite connection. Creates one if it doesn't exist.
    
    Args:
        db_path (str): Path to the SQLite database file.
    
    Returns:
        sqlite3.Connection: SQLite connection object.
    """
    if not hasattr(_thread_local, 'connection'):
        try:
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
            _thread_local.connection = conn
        except sqlite3.Error as e:
            logging.error(f"Error initializing database connection: {e}")
            raise
    return _thread_local.connection

def close_db_connection():
    """
    Closes the thread-local SQLite connection if it exists.
    """
    conn = getattr(_thread_local, 'connection', None)
    if conn:
        try:
            conn.close()
            del _thread_local.connection
        except sqlite3.Error as e:
            logging.error(f"Error closing database connection: {e}")

def get_cached_entry(conn: sqlite3.Connection, file_path: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves the cached entry for a given file path.
    
    Args:
        conn (sqlite3.Connection): SQLite connection object.
        file_path (str): The path to the file.
    
    Returns:
        Optional[Dict[str, Any]]: Dictionary containing cached data or None if not found.
    """
    absolute_file_path = str(Path(file_path).resolve())
    try:
        cursor = conn.execute(
            "SELECT file_hash, hash_algorithm, file_info, size, mtime FROM cache WHERE file_path = ?",
            (absolute_file_path,),
        )
        result = cursor.fetchone()
        if result:
            file_hash, hash_algorithm, file_info_json, size, mtime = result
            try:
                file_info = json.loads(file_info_json)
            except json.JSONDecodeError as e:
                logging.error(f"Error parsing file_info for {absolute_file_path}: {e}")
                file_info = {}
            return {
                "file_hash": file_hash,
                "hash_algorithm": hash_algorithm,
                "file_info": file_info,
                "size": size,
                "mtime": mtime
            }
    except sqlite3.Error as e:
        logging.error(f"Error retrieving cached entry for {absolute_file_path}: {e}")
    return None

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
    Sets or updates the cached entry for a given file path.
    
    Args:
        conn (sqlite3.Connection): SQLite connection object.
        file_path (str): The path to the file.
        file_hash (Optional[str]): Hash of the file.
        hash_algorithm (Optional[str]): Hash algorithm used.
        file_info (Dict[str, Any]): Information about the file.
        size (int): Size of the file in bytes.
        mtime (float): Last modification time of the file.
    """
    absolute_file_path = str(Path(file_path).resolve())
    file_info_json = json.dumps(file_info)
    try:
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
                (absolute_file_path, file_hash, hash_algorithm, file_info_json, size, mtime),
            )
    except sqlite3.Error as e:
        logging.error(f"Error setting cached entry for {absolute_file_path}: {e}")

def clean_cache(
    db_path: str, root_dir: Path
) -> None:
    """
    Cleans the cache by removing entries for files that no longer exist.
    
    Args:
        db_path (str): Path to the SQLite database file.
        root_dir (Path): Root directory to scan for existing files.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute("SELECT file_path FROM cache")
        cached_files = {row[0] for row in cursor.fetchall()}
    except sqlite3.Error as e:
        logging.error(f"Error fetching cached file paths: {e}")
        return

    try:
        existing_files = {str(p.resolve()) for p in root_dir.rglob("*") if p.is_file()}
    except Exception as e:
        logging.error(f"Error scanning root directory {root_dir}: {e}")
        return

    files_to_remove = cached_files - existing_files

    if files_to_remove:
        try:
            with conn:
                conn.executemany(
                    "DELETE FROM cache WHERE file_path = ?",
                    ((fp,) for fp in files_to_remove),
                )
            if USE_COLOR:
                message = f"{Fore.GREEN}Cache cleaned. {len(files_to_remove)} entries removed.{Style.RESET_ALL}"
            else:
                message = f"Cache cleaned. {len(files_to_remove)} entries removed."
            logging.info(message)
        except sqlite3.Error as e:
            logging.error(f"Error cleaning cache: {e}")

def initialize_db(db_path: str) -> None:
    """
    Initializes the database by ensuring the cache table exists.
    
    Args:
        db_path (str): Path to the SQLite database file.
    """
    get_db_connection(db_path)

def close_all_connections():
    """
    Closes all thread-local database connections.
    """
    close_db_connection()
