# repo_analyzer/core/application.py

import logging
import multiprocessing
import sys
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from repo_analyzer.cache.sqlite_cache import (
    clean_cache,
    close_all_connections,
    get_connection_context,
    initialize_connection_pool,
)
from repo_analyzer.cli.parser import get_default_cache_path, parse_arguments
from repo_analyzer.config.config import Config
from repo_analyzer.config.defaults import (
    CACHE_DB_FILE,
    DEFAULT_EXCLUDED_FILES,
    DEFAULT_EXCLUDED_FOLDERS,
)
from repo_analyzer.core.summary import create_summary
from repo_analyzer.logging.setup import setup_logging
from repo_analyzer.output.output_factory import OutputFactory
from repo_analyzer.traversal.traverser import get_directory_structure

MAX_SIZE_MULTIPLIER = 1024 * 1024
DEFAULT_THREAD_MULTIPLIER = 2


def initialize_cache_directory(cache_path: Path) -> Path:
    """
    Initialisiert das Cache-Verzeichnis.

    Args:
        cache_path (Path): Der vom Benutzer angegebene Pfad oder der Standardpfad.

    Returns:
        Path: Der Pfad zum Cache-Verzeichnis.

    Raises:
        SystemExit: Wenn das Verzeichnis nicht erstellt werden kann.
    """
    try:
        cache_path.mkdir(parents=True, exist_ok=True)
        logging.debug(f"Cache-Verzeichnis erstellt oder existiert bereits: {cache_path}")
    except OSError as e:
        logging.error(f"Fehler beim Erstellen des Cache-Verzeichnisses '{cache_path}': {e}")
        sys.exit(1)
    return cache_path


def run() -> None:
    """
    Hauptfunktion zur Analyse von Repositorys.

    Diese Funktion parst die Argumente, lädt die Konfiguration,
    richtet das Logging ein, initialisiert den Cache, traversiert
    das Verzeichnis und erstellt die Ausgabe.
    """
    args = parse_arguments()

    # Initialisiere die Konfigurationsverwaltung
    config_manager = Config()
    try:
        config_manager.load(args.config)
    except FileNotFoundError:
        logging.error(f"Konfigurationsdatei nicht gefunden: {args.config}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Fehler beim Laden der Konfigurationsdatei: {e}")
        sys.exit(1)
    config = config_manager.data

    # Setup Logging mit Verbosity und optionalem Logfile
    setup_logging(args.verbose, args.log_file)

    # Variablenzuweisung mit Typannotationen
    root_directory: Path = Path(args.root_directory).resolve()
    output_file: str = args.output
    include_binary: bool = args.include_binary
    additional_excluded_folders: Set[str] = set(args.exclude_folders)
    additional_excluded_files: Set[str] = set(args.exclude_files)
    follow_symlinks: bool = args.follow_symlinks
    additional_image_extensions: Set[str] = {
        ext.lower() if ext.startswith('.') else f'.{ext.lower()}'
        for ext in args.image_extensions
    }
    include_summary: bool = args.include_summary
    output_format: str = args.format
    threads: Optional[int] = args.threads
    exclude_patterns: List[str] = args.exclude_patterns
    encoding: str = args.encoding
    cache_path: Path = Path(args.cache_path).expanduser().resolve()

    # Bestimmung des Hash-Algorithmus oder Deaktivierung
    if args.no_hash:
        hash_algorithm = None
        logging.info("Hash-Verifizierung ist deaktiviert.")
    else:
        hash_algorithm = args.hash_algorithm
        logging.info(f"Verwende Hash-Algorithmus: {hash_algorithm}")

    # Dynamische Bestimmung der Thread-Anzahl, falls nicht angegeben
    if threads is None:
        threads = multiprocessing.cpu_count() * DEFAULT_THREAD_MULTIPLIER
        logging.info(f"Dynamisch festgelegte Anzahl der Threads: {threads}")

    # Bestimmung der max_file_size mit Priorität: CLI-Argument > Config-Datei > Default
    try:
        if args.max_size is not None:
            max_file_size = args.max_size * MAX_SIZE_MULTIPLIER
        else:
            max_file_size = config_manager.get_max_size(cli_max_size=None)

        logging.info(f"Maximale Dateigröße zum Lesen: {max_file_size / MAX_SIZE_MULTIPLIER} MB")
    except ValueError as ve:
        logging.error(f"Fehler bei der Bestimmung der maximalen Dateigröße: {ve}")
        sys.exit(1)

    # Kombiniere die standardmäßigen und zusätzlichen Ausschlüsse aus Argumenten und Konfigurationsdatei
    config_excluded_folders: Set[str] = set(config.get('exclude_folders', []))
    config_excluded_files: Set[str] = set(config.get('exclude_files', []))
    config_exclude_patterns: List[str] = config.get('exclude_patterns', [])

    excluded_folders: Set[str] = (
        DEFAULT_EXCLUDED_FOLDERS
        .union(additional_excluded_folders, config_excluded_folders)
    )
    excluded_files: Set[str] = (
        set(DEFAULT_EXCLUDED_FILES)
        .union(additional_excluded_files, config_excluded_files)
    )
    exclude_patterns: List[str] = exclude_patterns + config_exclude_patterns

    # Kombiniere die standardmäßigen und zusätzlichen Bilddateiendungen
    image_extensions: Set[str] = {
        '.png',
        '.jpg',
        '.jpeg',
        '.gif',
        '.bmp',
        '.svg',
        '.webp',
        '.tiff',
    }.union(additional_image_extensions)

    logging.info(f"Durchsuche das Verzeichnis: {root_directory}")
    logging.info(f"Ausgeschlossene Ordner: {', '.join(sorted(excluded_folders))}")
    logging.info(f"Ausgeschlossene Dateien: {', '.join(sorted(excluded_files))}")
    if not include_binary:
        logging.info("Binäre Dateien und Bilddateien sind ausgeschlossen.")
    else:
        logging.info("Binäre Dateien und Bilddateien werden einbezogen.")
    logging.info(f"Ausgabe in: {output_file} ({output_format})")
    logging.info(
        f"Symbolische Links werden {'gefolgt' if follow_symlinks else 'nicht gefolgt'}"
    )
    logging.info(f"Bilddateiendungen: {', '.join(sorted(image_extensions))}")
    logging.info(f"Ausschlussmuster: {', '.join(exclude_patterns)}")
    logging.info(f"Anzahl der Threads: {threads}")
    logging.info(f"Standard-Encoding: {encoding}")
    logging.info(f"Cache-Pfad: {cache_path}")

    # Initialisiere das Cache-Verzeichnis
    cache_dir: Path = initialize_cache_directory(cache_path)
    cache_db_path: Path = cache_dir / CACHE_DB_FILE
    db_path_str = str(cache_db_path)
    try:
        initialize_connection_pool(db_path_str)
    except Exception as e:
        logging.error(f"Fehler beim Initialisieren des Verbindungspools: {e}")
        sys.exit(1)

    # Bereinige den Cache basierend auf dem Root-Verzeichnis
    try:
        clean_cache(root_directory)
    except Exception as e:
        logging.error(f"Fehler beim Bereinigen des Caches: {e}")
        sys.exit(1)

    # Lock für den Cache
    cache_lock: threading.Lock = threading.Lock()

    # Verwenden Sie den Kontextmanager, um eine Verbindung zu erhalten
    with get_connection_context() as conn:
        try:
            structure, summary = get_directory_structure(
                root_dir=root_directory,
                max_file_size=max_file_size,
                include_binary=include_binary,
                excluded_folders=excluded_folders,
                excluded_files=excluded_files,
                follow_symlinks=follow_symlinks,
                image_extensions=image_extensions,
                exclude_patterns=exclude_patterns,
                conn=conn,
                lock=cache_lock,
                threads=threads,
                encoding=encoding,
                hash_algorithm=hash_algorithm,
            )
        except KeyboardInterrupt:
            logging.warning("Skript wurde vom Benutzer abgebrochen.")
            # Optional: Speichere die aktuelle Struktur bis zum Abbruchpunkt
            try:
                output_data: Dict[str, Any] = {}
                if include_summary and summary:
                    output_data["summary"] = summary
                if structure:
                    output_data["structure"] = structure

                OutputFactory.get_output(output_format)(output_data, output_file)

                logging.info(
                    f"Der aktuelle Stand der Ordnerstruktur"
                    f"{' und die Zusammenfassung ' if include_summary else ''}"
                    f"wurden in '{output_file}' gespeichert."
                )
            except (OSError, IOError) as e:
                logging.error(
                    f"Fehler beim Schreiben der Ausgabedatei nach Abbruch: {str(e)}"
                )
            finally:
                sys.exit(1)
        except (OSError, IOError) as e:
            logging.error(f"Ein IO-Fehler ist aufgetreten: {e}")
            sys.exit(1)
        except Exception as e:
            logging.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
            sys.exit(1)

        # Erstelle die Zusammenfassung
        try:
            output_data: Dict[str, Any] = create_summary(
                structure, summary, include_summary, hash_algorithm
            )
        except Exception as e:
            logging.error(f"Fehler beim Erstellen der Zusammenfassung: {e}")
            output_data = structure  # Fallback ohne Zusammenfassung

        # Schreibe die Struktur (und ggf. die Zusammenfassung) in die Ausgabedatei
        try:
            OutputFactory.get_output(output_format)(output_data, output_file)

            logging.info(
                f"Die Ordnerstruktur"
                f"{' und die Zusammenfassung ' if include_summary else ''}"
                f"wurden erfolgreich in '{output_file}' gespeichert."
            )
        except (OSError, IOError) as e:
            logging.error(f"Fehler beim Schreiben der Ausgabedatei: {str(e)}")

    # Schließe die SQLite-Verbindungen nach Abschluss
    try:
        close_all_connections()
    except Exception as e:
        logging.error(f"Fehler beim Schließen der Verbindungen: {e}")
