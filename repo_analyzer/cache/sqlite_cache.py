# repo_analyzer/cache/sqlite_cache.py

import json
import logging
import queue
import sqlite3
import sys
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, Optional

from colorama import Fore, Style
from colorama import init as colorama_init

# Initialize colorama
colorama_init(autoreset=True)

# Determine if the output is a TTY to decide on color usage
USE_COLOR = sys.stdout.isatty()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Connection pool settings
DEFAULT_CONNECTION_POOL_SIZE = 10
connection_pool = queue.Queue(maxsize=DEFAULT_CONNECTION_POOL_SIZE)
pool_initialized = False
pool_init_lock = threading.Lock()


def initialize_connection_pool(
    db_path: str,
    pool_size: Optional[int] = None
) -> None:
    """
    Initialisiert den Verbindungspool mit SQLite-Verbindungen.

    Args:
        db_path (str): Pfad zur SQLite-Datenbankdatei.
        pool_size (Optional[int]): Optionale Größe des Verbindungspools.
    """
    global pool_initialized
    if not pool_initialized:
        with pool_init_lock:
            if not pool_initialized:
                actual_pool_size = (
                    pool_size
                    if pool_size is not None
                    else DEFAULT_CONNECTION_POOL_SIZE
                )
                if not isinstance(actual_pool_size, int) or actual_pool_size <= 0:
                    logging.error("pool_size muss eine positive ganze Zahl sein.")
                    sys.exit(1)
                for _ in range(actual_pool_size):
                    try:
                        conn = sqlite3.connect(
                            db_path,
                            check_same_thread=False
                        )
                        # Setzen der PRAGMA-Einstellungen für bessere Leistung und Sicherheit
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
                        # Hinzufügen eines Indexes für hash_algorithm
                        conn.execute(
                            """
                            CREATE INDEX IF NOT EXISTS idx_hash_algorithm
                            ON cache(hash_algorithm);
                            """
                        )
                        connection_pool.put(conn)
                    except sqlite3.Error as e:
                        logging.error(
                            f"Fehler beim Initialisieren der Datenbankverbindung: {e}"
                        )
                        sys.exit(1)
                pool_initialized = True
                logging.info(
                    f"Datenbankverbindungspool mit {actual_pool_size} "
                    "Verbindungen initialisiert."
                )


@contextmanager
def get_connection_context() -> Generator[sqlite3.Connection, None, None]:
    """
    Kontextmanager, der eine Verbindung aus dem Pool bereitstellt und nach Gebrauch zurückgibt.

    Yields:
        sqlite3.Connection: Eine SQLite-Verbindung aus dem Pool.
    """
    if not pool_initialized:
        logging.error(
            "Verbindungspool ist nicht initialisiert. "
            "Bitte rufe initialize_connection_pool auf."
        )
        raise RuntimeError("Verbindungspool nicht initialisiert.")
    conn = None
    try:
        conn = connection_pool.get(timeout=10)
        yield conn
    except queue.Empty:
        logging.error("Keine verfügbaren Datenbankverbindungen im Pool. Timeout erreicht.")
        raise
    finally:
        if conn:
            connection_pool.put(conn)


def close_all_connections(
    exclude_conn: Optional[sqlite3.Connection] = None
) -> None:
    """
    Schließt alle Verbindungen im Pool, optional mit Ausnahme einer bestimmten Verbindung.

    Args:
        exclude_conn (Optional[sqlite3.Connection]): Eine Verbindung, die nicht geschlossen werden soll.
    """
    if not pool_initialized:
        logging.warning(
            "Verbindungspool wurde nicht initialisiert. "
            "Keine Verbindungen zu schließen."
        )
        return
    closed_connections = 0
    while not connection_pool.empty():
        try:
            conn = connection_pool.get_nowait()
            if conn != exclude_conn:
                conn.close()
                closed_connections += 1
            else:
                # Falls es die zu exkludierende Verbindung ist, zurück in den Pool legen
                connection_pool.put(conn)
        except queue.Empty:
            break
        except sqlite3.Error as e:
            logging.error(
                f"Fehler beim Schließen der Datenbankverbindung: {e}"
            )
    logging.info(
        f"Alle {closed_connections} Datenbankverbindungen im Pool wurden geschlossen."
    )


def get_cached_entry(
    conn: sqlite3.Connection,
    file_path: str
) -> Optional[Dict[str, Any]]:
    """
    Ruft einen zwischengespeicherten Eintrag für einen gegebenen Dateipfad ab.

    Args:
        conn (sqlite3.Connection): Die SQLite-Verbindung.
        file_path (str): Pfad zur Datei.

    Returns:
        Optional[Dict[str, Any]]: Der zwischengespeicherte Eintrag oder None.
    """
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
                    f"Cache-Treffer für Datei: {absolute_file_path} "
                    f"mit Hash: {file_hash}"
                )
            except json.JSONDecodeError as e:
                logging.error(
                    f"Fehler beim Parsen von file_info für {absolute_file_path}: {e}"
                )
                conn.execute(
                    "DELETE FROM cache WHERE file_path = ?",
                    (absolute_file_path,)
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
            f"Fehler beim Abrufen des zwischengespeicherten Eintrags "
            f"für {absolute_file_path}: {e}"
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
    """
    Setzt oder aktualisiert den zwischengespeicherten Eintrag für einen gegebenen Dateipfad.

    Args:
        conn (sqlite3.Connection): Die SQLite-Verbindung.
        file_path (str): Der Pfad zur Datei.
        file_hash (Optional[str]): Hash der Datei.
        hash_algorithm (Optional[str]): Verwendeter Hash-Algorithmus.
        file_info (Dict[str, Any]): Informationen über die Datei.
        size (int): Größe der Datei in Bytes.
        mtime (float): Letzte Änderungszeit der Datei.
    """
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
            f"Fehler beim Setzen des zwischengespeicherten Eintrags "
            f"für {absolute_file_path}: {e}"
        )


def clean_cache(root_dir: Path) -> None:
    """
    Bereinigt den Cache, indem Einträge entfernt werden, die nicht mehr im Dateisystem vorhanden sind.

    Args:
        root_dir (Path): Das Wurzelverzeichnis zum Scannen von Dateien.
    """
    if not pool_initialized:
        logging.error(
            "Verbindungspool ist nicht initialisiert. "
            "Bitte rufe initialize_connection_pool auf."
        )
        raise RuntimeError("Verbindungspool nicht initialisiert.")

    included_files = set()
    try:
        for p in root_dir.rglob("*"):
            if p.is_file():
                included_files.add(str(p.resolve()))
    except Exception as e:
        logging.error(
            f"Fehler beim Scannen des Wurzelverzeichnisses {root_dir}: {e}"
        )
        return

    with get_connection_context() as conn:
        try:
            conn.execute("BEGIN TRANSACTION;")
            cursor = conn.execute("SELECT file_path FROM cache")
            cached_files = {row[0] for row in cursor.fetchall()}
        except sqlite3.Error as e:
            logging.error(
                f"Fehler beim Abrufen der zwischengespeicherten Dateipfade: {e}"
            )
            conn.execute("ROLLBACK;")
            return
        conn.execute("ROLLBACK;")

    files_to_remove = cached_files - included_files

    if files_to_remove:
        try:
            with get_connection_context() as conn:
                conn.executemany(
                    "DELETE FROM cache WHERE file_path = ?",
                    ((fp,) for fp in files_to_remove),
                )
                conn.commit()

                # Führe VACUUM aus, um die Datenbankgröße zu reduzieren
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
            with get_connection_context() as conn:
                conn.execute("ROLLBACK;")
    else:
        logging.info(
            "Keine Cache-Bereinigung erforderlich. Alle Einträge sind aktuell."
        )