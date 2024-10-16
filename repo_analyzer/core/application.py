# repo_analyzer/core/application.py

import json
import logging
import multiprocessing
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from repo_analyzer.cache.sqlite_cache import clean_cache, initialize_db
from repo_analyzer.cli.parser import parse_arguments
from repo_analyzer.config.defaults import DEFAULT_EXCLUDED_FOLDERS, CACHE_DB_FILE, DEFAULT_EXCLUDED_FILES
from repo_analyzer.config.loader import load_config
from repo_analyzer.logging.setup import setup_logging
from repo_analyzer.output.output_factory import OutputFactory
from repo_analyzer.traversal.traverser import get_directory_structure
from repo_analyzer.core.summary import create_summary

def run() -> None:
    args = parse_arguments()

    # Lade die Konfigurationsdatei, falls angegeben
    config = load_config(args.config)

    # Setup Logging mit Verbosity und optionalem Logfile
    setup_logging(args.verbose, args.log_file)

    root_directory = Path(args.root_directory).resolve()
    output_file = args.output
    max_file_size = args.max_size
    include_binary = args.include_binary
    additional_excluded_folders = set(args.exclude_folders)
    additional_excluded_files = set(args.exclude_files)
    follow_symlinks = args.follow_symlinks
    additional_image_extensions = set(
        ext.lower() if ext.startswith('.') else f'.{ext.lower()}'
        for ext in args.image_extensions
    )
    include_summary = args.include_summary  # Neue Option
    output_format = args.format
    threads = args.threads
    exclude_patterns = args.exclude_patterns
    encoding = args.encoding  # Neues Argument

    # Dynamische Bestimmung der Thread-Anzahl, falls nicht angegeben
    if threads is None:
        threads = multiprocessing.cpu_count() * 2
        logging.info(
            f"Dynamisch festgelegte Anzahl der Threads: {threads}"
        )

    # Kombiniere die standardmäßigen und zusätzlichen Ausschlüsse aus Argumenten und Konfigurationsdatei
    config_excluded_folders = set(config.get('exclude_folders', []))
    config_excluded_files = set(config.get('exclude_files', []))
    config_exclude_patterns = config.get('exclude_patterns', [])

    excluded_folders = DEFAULT_EXCLUDED_FOLDERS.union(
        additional_excluded_folders, config_excluded_folders
    )
    excluded_files = set(DEFAULT_EXCLUDED_FILES).union(
        additional_excluded_files, config_excluded_files
    )
    exclude_patterns = exclude_patterns + config_exclude_patterns

    # Kombiniere die standardmäßigen und zusätzlichen Bilddateiendungen
    image_extensions = {
        '.png',
        '.jpg',
        '.jpeg',
        '.gif',
        '.bmp',
        '.svg',
        '.webp',
        '.tiff',
    }.union(additional_image_extensions)

    logging.info(
        f"Durchsuche das Verzeichnis: {root_directory}"
    )
    logging.info(
        f"Ausgeschlossene Ordner: {', '.join(excluded_folders)}"
    )
    logging.info(
        f"Ausgeschlossene Dateien: {', '.join(excluded_files)}"
    )
    if not include_binary:
        logging.info(
            f"Binäre Dateien und Bilddateien sind ausgeschlossen."
        )
    else:
        logging.info(
            f"Binäre Dateien und Bilddateien werden einbezogen."
        )
    logging.info(
        f"Maximale Dateigröße zum Lesen: {max_file_size} Bytes"
    )
    logging.info(
        f"Ausgabe in: {output_file} ({output_format})"
    )
    logging.info(
        f"Symbolische Links werden "
        f"{'gefolgt' if follow_symlinks else 'nicht gefolgt'}"
    )
    logging.info(
        f"Bilddateiendungen: {', '.join(sorted(image_extensions))}"
    )
    logging.info(
        f"Ausschlussmuster: {', '.join(exclude_patterns)}"
    )
    logging.info(
        f"Anzahl der Threads: {threads}"
    )
    logging.info(
        f"Standard-Encoding: {encoding}"
    )

    # Initialisiere den SQLite-Cache
    cache_db_path = root_directory / CACHE_DB_FILE
    conn = initialize_db(str(cache_db_path))

    # Lock für den Cache
    cache_lock = threading.Lock()

    # Bereinige den Cache
    clean_cache(conn, root_directory, cache_lock)

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
        )
    except KeyboardInterrupt:
        logging.warning(
            "Skript wurde vom Benutzer abgebrochen."
        )
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
        except Exception as e:
            logging.error(
                f"Fehler beim Schreiben der Ausgabedatei nach Abbruch: {str(e)}"
            )
        finally:
            conn.close()
            exit(1)
    except Exception as e:
        logging.error(
            f"Ein unerwarteter Fehler ist aufgetreten: {e}"
        )
        conn.close()
        exit(1)

    # Erstelle die Zusammenfassung
    output_data = create_summary(structure, summary, include_summary)

    # Schreibe die Struktur (und ggf. die Zusammenfassung) in die Ausgabedatei
    try:
        OutputFactory.get_output(output_format)(output_data, output_file)

        logging.info(
            f"Die Ordnerstruktur"
            f"{' und die Zusammenfassung ' if include_summary else ''}"
            f"wurden erfolgreich in '{output_file}' gespeichert."
        )
    except Exception as e:
        logging.error(
            f"Fehler beim Schreiben der Ausgabedatei: {str(e)}"
        )

    # Schließe die SQLite-Verbindung
    conn.close()
