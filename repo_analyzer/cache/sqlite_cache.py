# repo_analyzer/cache/sqlite_cache.py

import atexit
import json
import logging
import queue
import sqlite3
import sys
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, Optional, Set

from colorama import Fore, Style, init as colorama_init

colorama_init(autoreset=True)

USE_COLOR = sys.stdout.isatty()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

DEFAULT_CONNECTION_POOL_SIZE = 3


class ConnectionPool:
    """Verwaltung eines Pools von SQLite-Verbindungen."""

    _instance_lock = threading.Lock()
    _instance: Optional['ConnectionPool'] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super(ConnectionPool, cls).__new__(cls)
        return cls._instance

    def __init__(self, db_path: str, pool_size: Optional[int] = None) -> None:
        if hasattr(self, '_initialized') and self._initialized:
            return
        self.pool_size = pool_size if pool_size is not None else DEFAULT_CONNECTION_POOL_SIZE
        if not isinstance(self.pool_size, int) or self.pool_size <= 0:
            logging.error("pool_size muss eine positive ganze Zahl sein.")
            sys.exit(1)
        self.pool = queue.Queue(maxsize=self.pool_size)
        self.pool_lock = threading.Lock()
        self._initialize_pool(db_path)
        self._initialized = True

    def _initialize_pool(self, db_path: str) -> None:
        with self.pool_lock:
            for _ in range(self.pool_size):
                try:
                    conn = sqlite3.connect(
                        db_path,
                        check_same_thread=False
                    )
                    conn.execute("PRAGMA foreign_keys = ON;")
                    conn.execute("PRAGMA journal_mode = WAL;")
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
                    conn.execute(
                        """
                        CREATE INDEX IF NOT EXISTS idx_hash_algorithm
                        ON cache(hash_algorithm);
                        """
                    )
                    self.pool.put(conn)
                except sqlite3.Error as e:
                    logging.error(
                        f"Fehler beim Initialisieren der Datenbankverbindung: {e}"
                    )
                    sys.exit(1)
            logging.info(
                f"Datenbankverbindungspool mit {self.pool_size} "
                "Verbindungen initialisiert."
            )

    @contextmanager
    def get_connection_context(self) -> Generator[sqlite3.Connection, None, None]:
        try:
            conn = self.pool.get(timeout=10)
            if not self._validate_connection(conn):
                logging.warning("Verbindung ist ungültig. Neue Verbindung wird erstellt.")
                conn = self._create_new_connection(conn)
            yield conn
        except queue.Empty:
            logging.error("Keine verfügbaren Datenbankverbindungen im Pool. Timeout erreicht.")
            raise
        finally:
            if conn:
                self.pool.put(conn)

    def _validate_connection(self, conn: sqlite3.Connection) -> bool:
        try:
            conn.execute("SELECT 1;")
            return True
        except sqlite3.Error:
            return False

    def _create_new_connection(self, old_conn: sqlite3.Connection) -> sqlite3.Connection:
        try:
            old_conn.close()
            new_conn = sqlite3.connect(
                old_conn.database,
                check_same_thread=False
            )
            new_conn.execute("PRAGMA foreign_keys = ON;")
            new_conn.execute("PRAGMA journal_mode = WAL;")
            return new_conn
        except sqlite3.Error as e:
            logging.error(f"Fehler beim Erstellen einer neuen Datenbankverbindung: {e}")
            sys.exit(1)

    def close_all_connections(self, exclude_conn: Optional[sqlite3.Connection] = None) -> None:
        closed_connections = 0
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                if conn != exclude_conn:
                    conn.close()
                    closed_connections += 1
                else:
                    self.pool.put(conn)
            except queue.Empty:
                break
            except sqlite3.Error as e:
                logging.error(
                    f"Fehler beim Schließen der Datenbankverbindung: {e}"
                )
        logging.info(
            f"Alle {closed_connections} Datenbankverbindungen im Pool wurden geschlossen."
        )


# Instanz des Verbindungspools
_connection_pool_instance: Optional[ConnectionPool] = None
_pool_lock = threading.Lock()


def initialize_connection_pool(
    db_path: str,
    pool_size: Optional[int] = None
) -> None:
    global _connection_pool_instance
    if _connection_pool_instance is None:
        with _pool_lock:
            if _connection_pool_instance is None:
                _connection_pool_instance = ConnectionPool(db_path, pool_size)
    else:
        logging.info("Verbindungspool ist bereits initialisiert.")


@contextmanager
def get_connection_context() -> Generator[sqlite3.Connection, None, None]:
    if _connection_pool_instance is None:
        logging.error(
            "Verbindungspool ist nicht initialisiert. "
            "Bitte rufe initialize_connection_pool auf."
        )
        raise RuntimeError("Verbindungspool nicht initialisiert.")
    with _connection_pool_instance.get_connection_context() as conn:
        yield conn


def close_all_connections(exclude_conn: Optional[sqlite3.Connection] = None) -> None:
    if _connection_pool_instance is not None:
        _connection_pool_instance.close_all_connections(exclude_conn)
    else:
        logging.warning(
            "Verbindungspool wurde nicht initialisiert. "
            "Keine Verbindungen zu schließen."
        )


def get_cached_entry(
    conn: sqlite3.Connection,
    file_path: str
) -> Optional[Dict[str, Any]]:
    absolute_file_path = str(Path(file_path).resolve())
    try:
        cursor = conn.execute(
            """
            SELECT file_hash, hash_algorithm, file_info, size, mtime
            FROM cache WHERE file_path = ?
            """,
            (absolute_file_path,),
        )
        result = cursor.fetchone()
        if result:
            file_hash, hash_algorithm, file_info_json, size, mtime = result
            try:
                file_info = json.loads(file_info_json)
                logging.debug(
                    f"Cache-Treffer für Datei: {absolute_file_path} mit Hash: {file_hash}"
                )
            except json.JSONDecodeError as e:
                logging.error(
                    f"Fehler beim Parsen von file_info für {absolute_file_path}: {e}"
                )
                conn.execute(
                    "DELETE FROM cache WHERE file_path = ?",
                    (absolute_file_path,),
                )
                conn.commit()
                return None
            return {
                "file_hash": file_hash,
                "hash_algorithm": hash_algorithm,
                "file_info": file_info,
                "size": size,
                "mtime": mtime
            }
    except sqlite3.Error as e:
        logging.error(
            f"Fehler beim Abrufen des zwischengespeicherten Eintrags für {absolute_file_path}: {e}"
        )
    return None


def set_cached_entry(
    conn: sqlite3.Connection,
    file_path: str,
    file_hash: Optional[str],
    hash_algorithm: Optional[str],
    file_info: Dict[str, Any],
    size: int,
    mtime: float
) -> None:
    absolute_file_path = str(Path(file_path).resolve())
    file_info_json = json.dumps(file_info)
    try:
        conn.execute(
            """
            INSERT INTO cache (
                file_path, file_hash, hash_algorithm, file_info, size, mtime
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(file_path) DO UPDATE SET
                file_hash = excluded.file_hash,
                hash_algorithm = excluded.hash_algorithm,
                file_info = excluded.file_info,
                size = excluded.size,
                mtime = excluded.mtime
            """,
            (
                absolute_file_path, file_hash, hash_algorithm,
                file_info_json, size, mtime
            ),
        )
        conn.commit()
    except sqlite3.Error as e:
        logging.error(
            f"Fehler beim Setzen des zwischengespeicherten Eintrags für {absolute_file_path}: {e}"
        )


def clean_cache(root_dir: Path) -> None:
    if _connection_pool_instance is None:
        logging.error(
            "Verbindungspool ist nicht initialisiert. Bitte rufe initialize_connection_pool auf."
        )
        raise RuntimeError("Verbindungspool nicht initialisiert.")

    included_files: Set[str] = set()
    try:
        for p in root_dir.rglob("*"):
            if p.is_file():
                included_files.add(str(p.resolve()))
    except Exception as e:
        logging.error(f"Fehler beim Scannen des Wurzelverzeichnisses {root_dir}: {e}")
        return

    with get_connection_context() as conn:
        try:
            cursor = conn.execute("SELECT file_path FROM cache")
            cached_files = {row[0] for row in cursor.fetchall()}
        except sqlite3.Error as e:
            logging.error(
                f"Fehler beim Abrufen der zwischengespeicherten Dateipfade: {e}"
            )
            return

    files_to_remove = cached_files - included_files

    if files_to_remove:
        try:
            with get_connection_context() as conn:
                conn.executemany(
                    "DELETE FROM cache WHERE file_path = ?",
                    ((fp,) for fp in files_to_remove),
                )
                conn.commit()

                # Optional: VACUUM nur durchführen, wenn eine bestimmte Anzahl von Einträgen entfernt wurde
                if len(files_to_remove) >= 10:  # Beispielschwelle
                    try:
                        conn.execute("VACUUM;")
                        logging.info("VACUUM ausgeführt, Datenbankgröße reduziert.")
                    except sqlite3.Error as e:
                        logging.error(f"Fehler beim Ausführen von VACUUM: {e}")

            if USE_COLOR:
                message = (
                    f"{Fore.GREEN}Cache bereinigt. "
                    f"{len(files_to_remove)} Einträge entfernt.{Style.RESET_ALL}"
                )
            else:
                message = (
                    f"Cache bereinigt. {len(files_to_remove)} Einträge entfernt."
                )
            logging.info(message)
        except sqlite3.Error as e:
            logging.error(f"Fehler beim Bereinigen des Caches: {e}")
    else:
        logging.info(
            "Keine Cache-Bereinigung erforderlich. Alle Einträge sind aktuell."
        )


# Automatisches Schließen aller Verbindungen beim Programmende
def _shutdown():
    if _connection_pool_instance:
        _connection_pool_instance.close_all_connections()

atexit.register(_shutdown)
