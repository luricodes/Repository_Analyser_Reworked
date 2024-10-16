# repo_analyzer/main.py

from repo_analyzer.traversal.traverser import recursive_traverse, count_total_files
from repo_analyzer.traversal.patterns import matches_patterns
from repo_analyzer.config.loader import load_config
from repo_analyzer.config.defaults import DEFAULT_EXCLUDED_FOLDERS, DEFAULT_EXCLUDED_FILES, DEFAULT_MAX_FILE_SIZE, CACHE_DB_FILE
from repo_analyzer.logging.setup import setup_logging
from repo_analyzer.cache.sqlite_cache import initialize_db, clean_cache
from repo_analyzer.traversal.traverser import get_directory_structure
from repo_analyzer.output.yaml_output import output_to_yaml
from repo_analyzer.output.xml_output import output_to_xml
from repo_analyzer.cli.parser import parse_arguments

import json
from pathlib import Path
import logging
from typing import Tuple, Dict, Any
from colorama import Fore, Style
import multiprocessing
import threading

def main() -> None:
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
        ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in args.image_extensions
    )
    include_summary = args.include_summary  # Neue Option
    output_format = args.format
    threads = args.threads
    exclude_patterns = args.exclude_patterns
    encoding = args.encoding  # Neues Argument

    # Dynamische Bestimmung der Thread-Anzahl, falls nicht angegeben
    if threads is None:
        threads = multiprocessing.cpu_count() * 2
        logging.info(f"{Fore.CYAN}Dynamisch festgelegte Anzahl der Threads: {threads}{Style.RESET_ALL}")

    # Kombiniere die standardmäßigen und zusätzlichen Ausschlüsse aus Argumenten und Konfigurationsdatei
    config_excluded_folders = set(config.get('exclude_folders', []))
    config_excluded_files = set(config.get('exclude_files', []))
    config_exclude_patterns = config.get('exclude_patterns', [])

    excluded_folders = DEFAULT_EXCLUDED_FOLDERS.union(additional_excluded_folders, config_excluded_folders)
    excluded_files = DEFAULT_EXCLUDED_FILES.union(additional_excluded_files, config_excluded_files)
    exclude_patterns = exclude_patterns + config_exclude_patterns

    # Kombiniere die standardmäßigen und zusätzlichen Bilddateiendungen
    image_extensions = {
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp', '.tiff'
    }.union(additional_image_extensions)

    logging.info(f"{Fore.BLUE}Durchsuche das Verzeichnis: {root_directory}{Style.RESET_ALL}")
    logging.info(f"{Fore.MAGENTA}Ausgeschlossene Ordner: {', '.join(excluded_folders)}{Style.RESET_ALL}")
    logging.info(f"{Fore.MAGENTA}Ausgeschlossene Dateien: {', '.join(excluded_files)}{Style.RESET_ALL}")
    if not include_binary:
        logging.info(f"{Fore.RED}Binäre Dateien und Bilddateien sind ausgeschlossen.{Style.RESET_ALL}")
    else:
        logging.info(f"{Fore.GREEN}Binäre Dateien und Bilddateien werden einbezogen.{Style.RESET_ALL}")
    logging.info(f"{Fore.YELLOW}Maximale Dateigröße zum Lesen: {max_file_size} Bytes{Style.RESET_ALL}")
    logging.info(f"{Fore.CYAN}Ausgabe in: {output_file} ({output_format}){Style.RESET_ALL}")
    logging.info(f"{Fore.CYAN}Symbolische Links werden {'gefolgt' if follow_symlinks else 'nicht gefolgt'}{Style.RESET_ALL}")
    logging.info(f"{Fore.MAGENTA}Bilddateiendungen: {', '.join(sorted(image_extensions))}{Style.RESET_ALL}")
    logging.info(f"{Fore.MAGENTA}Ausschlussmuster: {', '.join(exclude_patterns)}{Style.RESET_ALL}")
    logging.info(f"{Fore.MAGENTA}Anzahl der Threads: {threads}{Style.RESET_ALL}")
    logging.info(f"{Fore.MAGENTA}Standard-Encoding: {encoding}{Style.RESET_ALL}")

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
            encoding=encoding
        )
    except KeyboardInterrupt:
        logging.warning(f"{Fore.RED}\nSkript wurde vom Benutzer abgebrochen.{Style.RESET_ALL}")
        # Optional: Speichere die aktuelle Struktur bis zum Abbruchpunkt
        try:
            output_data = {}
            if include_summary and summary:
                output_data["summary"] = summary
            if structure:
                output_data["structure"] = structure

            if include_summary and summary:
                if output_format == 'json':
                    with open(output_file, 'w', encoding='utf-8') as out_file:
                        json.dump(output_data, out_file, ensure_ascii=False, indent=4)
                elif output_format == 'yaml':
                    output_to_yaml(output_data, output_file)
                elif output_format == 'xml':
                    output_to_xml(output_data, output_file)

                logging.info(f"{Fore.YELLOW}Der aktuelle Stand der Ordnerstruktur und die Zusammenfassung wurden in '{output_file}' gespeichert.{Style.RESET_ALL}")
            else:
                if output_format == 'json':
                    with open(output_file, 'w', encoding='utf-8') as out_file:
                        json.dump(output_data, out_file, ensure_ascii=False, indent=4)
                elif output_format == 'yaml':
                    output_to_yaml(output_data, output_file)
                elif output_format == 'xml':
                    output_to_xml(output_data, output_file)

                logging.info(f"{Fore.YELLOW}Der aktuelle Stand der Ordnerstruktur wurde in '{output_file}' gespeichert.{Style.RESET_ALL}")
        except Exception as e:
            logging.error(f"{Fore.RED}Fehler beim Schreiben der Ausgabedatei nach Abbruch: {str(e)}{Style.RESET_ALL}")
        finally:
            conn.close()
            exit(1)
    except Exception as e:
        logging.error(f"{Fore.RED}Ein unerwarteter Fehler ist aufgetreten: {e}{Style.RESET_ALL}")
        conn.close()
        exit(1)

    # Entscheide, ob die Zusammenfassung hinzugefügt werden soll
    if include_summary and summary:
        output_data = {
            "summary": summary,
            "structure": structure
        }
    else:
        output_data = structure

    # Schreibe die Struktur (und ggf. die Zusammenfassung) in die Ausgabedatei
    try:
        if output_format == 'json':
            with open(output_file, 'w', encoding='utf-8') as out_file:
                json.dump(output_data, out_file, ensure_ascii=False, indent=4)
        elif output_format == 'yaml':
            output_to_yaml(output_data, output_file)
        elif output_format == 'xml':
            output_to_xml(output_data, output_file)

        if include_summary and summary:
            logging.info(f"{Fore.GREEN}Die Ordnerstruktur und die Zusammenfassung wurden erfolgreich in '{output_file}' gespeichert.{Style.RESET_ALL}")
        else:
            logging.info(f"{Fore.GREEN}Die Ordnerstruktur wurde erfolgreich in '{output_file}' gespeichert.{Style.RESET_ALL}")
    except Exception as e:
        logging.error(f"{Fore.RED}Fehler beim Schreiben der Ausgabedatei: {str(e)}{Style.RESET_ALL}")

    # Schließe die SQLite-Verbindung
    conn.close()


if __name__ == "__main__":
    main()