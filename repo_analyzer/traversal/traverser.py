# repo_analyzer/traversal/traverser.py

from pathlib import Path
from typing import List, Tuple, Dict, Any
import logging
from colorama import Fore, Style
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import json
import yaml
import sqlite3
import threading
import multiprocessing
from repo_analyzer.traversal.patterns import matches_patterns
from repo_analyzer.processing.file_processor import process_file
from repo_analyzer.config.defaults import DEFAULT_MAX_FILE_SIZE
from repo_analyzer.output.yaml_output import output_to_yaml
from repo_analyzer.output.xml_output import output_to_xml
from repo_analyzer.cache.sqlite_cache import get_cached_entry, set_cached_entry
from repo_analyzer.utils.mime_type import is_binary
from repo_analyzer.utils.helpers import is_binary_alternative

def recursive_traverse(
    root_dir: Path,
    excluded_folders: set,
    excluded_files: set,
    exclude_patterns: List[str],
    follow_symlinks: bool
) -> List[Path]:
    """
    Rekursive Traversierung des Verzeichnisses, wobei ausgeschlossene Ordner und Dateien übersprungen werden.
    """
    paths = []
    visited_paths = set()

    def _traverse(current_dir: Path):
        try:
            if follow_symlinks:
                resolved_dir = current_dir.resolve()
                if resolved_dir in visited_paths:
                    logging.warning(f"{Fore.RED}Zirkulärer symbolischer Link gefunden: {current_dir}{Style.RESET_ALL}")
                    return
                visited_paths.add(resolved_dir)
        except Exception as e:
            logging.error(f"{Fore.RED}Fehler beim Auflösen von {current_dir}: {e}{Style.RESET_ALL}")
            return

        try:
            for entry in current_dir.iterdir():
                if entry.is_dir():
                    if entry.name in excluded_folders or matches_patterns(entry.name, exclude_patterns):
                        logging.debug(f"{Fore.CYAN}Ausschließen von Ordner: {entry}{Style.RESET_ALL}")
                        continue
                    _traverse(entry)
                elif entry.is_file():
                    if entry.name in excluded_files or matches_patterns(entry.name, exclude_patterns):
                        logging.debug(f"{Fore.YELLOW}Ausschließen von Datei: {entry}{Style.RESET_ALL}")
                        continue
                    paths.append(entry)
        except PermissionError as e:
            logging.warning(f"{Fore.YELLOW}Konnte Verzeichnis nicht lesen: {current_dir} - {e}{Style.RESET_ALL}")
        except Exception as e:
            logging.error(f"{Fore.RED}Fehler beim Durchlaufen von {current_dir}: {e}{Style.RESET_ALL}")

    _traverse(root_dir)
    return paths

def count_total_files(
    root_dir: Path,
    excluded_folders: set,
    excluded_files: set,
    exclude_patterns: List[str],
    follow_symlinks: bool
) -> Tuple[int, int]:
    """
    Zählt die insgesamt eingeschlossenen und ausgeschlossenen Dateien.
    """
    included = 0
    excluded = 0
    visited_paths = set()

    def _traverse_count(current_dir: Path):
        nonlocal included, excluded
        try:
            if follow_symlinks:
                resolved_dir = current_dir.resolve()
                if resolved_dir in visited_paths:
                    logging.warning(f"{Fore.RED}Zirkulärer symbolischer Link gefunden: {current_dir}{Style.RESET_ALL}")
                    return
                visited_paths.add(resolved_dir)
        except Exception as e:
            logging.error(f"{Fore.RED}Fehler beim Auflösen von {current_dir}: {e}{Style.RESET_ALL}")
            return

        try:
            for entry in current_dir.iterdir():
                if entry.is_dir():
                    if entry.name in excluded_folders or matches_patterns(entry.name, exclude_patterns):
                        logging.debug(f"{Fore.CYAN}Ausschließen von Ordner: {entry}{Style.RESET_ALL}")
                        continue
                    _traverse_count(entry)
                elif entry.is_file():
                    if entry.name in excluded_files or matches_patterns(entry.name, exclude_patterns):
                        excluded += 1
                    else:
                        included += 1
        except PermissionError as e:
            logging.warning(f"{Fore.YELLOW}Konnte Verzeichnis nicht lesen: {current_dir} - {e}{Style.RESET_ALL}")
        except Exception as e:
            logging.error(f"{Fore.RED}Fehler beim Durchlaufen von {current_dir}: {e}{Style.RESET_ALL}")

    _traverse_count(root_dir)
    return included, excluded

def get_directory_structure(
    root_dir: Path,
    max_file_size: int,
    include_binary: bool,
    excluded_folders: set,
    excluded_files: set,
    follow_symlinks: bool,
    image_extensions: set,
    exclude_patterns: List[str],
    conn: sqlite3.Connection,
    lock: threading.Lock,
    threads: int,
    encoding: str = 'utf-8'
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Erstellt die Verzeichnisstruktur als verschachteltes Dictionary.
    """
    dir_structure: Dict[str, Any] = {}
    
    # Zähle alle relevanten Dateien für die Fortschrittsanzeige
    included_files, excluded_files_count = count_total_files(root_dir, excluded_folders, excluded_files, exclude_patterns, follow_symlinks)
    total_files = included_files + excluded_files_count
    excluded_percentage = (excluded_files_count / total_files) * 100 if total_files else 0

    logging.info(f"{Fore.MAGENTA}Gesamtzahl der Dateien: {total_files}{Style.RESET_ALL}")
    logging.info(f"{Fore.YELLOW}Ausgeschlossene Dateien: {excluded_files_count} ({excluded_percentage:.2f}%){Style.RESET_ALL}")
    logging.info(f"{Fore.GREEN}Verarbeitete Dateien: {included_files}{Style.RESET_ALL}")

    pbar = tqdm(total=included_files, desc="Verarbeite Dateien", unit="file", dynamic_ncols=True)

    failed_files: List[Dict[str, str]] = []

    # Sammle alle Dateien, die verarbeitet werden sollen
    files_to_process = recursive_traverse(root_dir, excluded_folders, excluded_files, exclude_patterns, follow_symlinks)

    # Verwende ThreadPoolExecutor für parallele Verarbeitung
    with ThreadPoolExecutor(max_workers=threads) as executor:
        future_to_file = {}
        try:
            for file_path in files_to_process:
                future = executor.submit(
                    process_file,
                    file_path,
                    max_file_size,
                    include_binary,
                    image_extensions,
                    conn,
                    lock,
                    encoding=encoding
                )
                future_to_file[future] = file_path.parent
        except KeyboardInterrupt:
            logging.warning(f"{Fore.RED}\nAbbruch durch Benutzer. Versuche, laufende Aufgaben zu beenden...{Style.RESET_ALL}")
            executor.shutdown(wait=False, cancel_futures=True)
            pbar.close()
            raise  # Weiterreichen der Ausnahme, um sie im Hauptthread zu handhaben
        except Exception as e:
            logging.error(f"{Fore.RED}Unerwarteter Fehler während des Einreichens von Aufgaben: {e}{Style.RESET_ALL}")
            executor.shutdown(wait=False, cancel_futures=True)
            pbar.close()
            raise

        try:
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    filename, file_info = future.result()
                    if file_info is not None:
                        # Erstelle die verschachtelte Struktur
                        relative_parent = file_path.relative_to(root_dir)
                        current = dir_structure
                        for part in relative_parent.parts:
                            current = current.setdefault(part, {})
                        current[filename] = file_info
                except Exception as e:
                    # Finde den vollständigen Pfad zur Datei
                    try:
                        filename = future_to_file[future].name
                        file_path_full = future_to_file[future] / filename
                    except Exception:
                        file_path_full = str(future_to_file[future])
                    
                    # Erstelle die verschachtelte Struktur mit Fehlerinformationen
                    relative_parent = file_path.relative_to(root_dir)
                    current = dir_structure
                    for part in relative_parent.parts:
                        current = current.setdefault(part, {})
                    current[file_path_full.name if isinstance(file_path_full, Path) else 'unknown'] = {
                        "type": "error",
                        "content": f"<Fehler bei der Verarbeitung: {str(e)}>"
                    }
                    logging.error(f"{Fore.RED}Fehler beim Verarbeiten der Datei {file_path_full}: {e}{Style.RESET_ALL}")
                    failed_files.append({"file": str(file_path_full), "error": str(e)})
                finally:
                    pbar.update(1)
        except KeyboardInterrupt:
            logging.warning(f"{Fore.RED}\nAbbruch durch Benutzer während der Verarbeitung. Versuche, laufende Aufgaben zu beenden...{Style.RESET_ALL}")
            executor.shutdown(wait=False, cancel_futures=True)
            pbar.close()
            raise

    pbar.close()

    # Erstelle die Zusammenfassung
    summary = {
        "total_files": total_files,
        "excluded_files": excluded_files_count,
        "included_files": included_files,
        "excluded_percentage": excluded_percentage,
        "failed_files": failed_files  # Neue Liste für fehlgeschlagene Dateien
    }

    # Logge eine Zusammenfassung der verarbeiteten und ausgeschlossenen Dateien
    logging.info(f"{Fore.CYAN}Zusammenfassung:{Style.RESET_ALL}")
    logging.info(f"  {Fore.GREEN}Verarbeitete Dateien:{Style.RESET_ALL} {included_files}")
    logging.info(f"  {Fore.YELLOW}Ausgeschlossene Dateien:{Style.RESET_ALL} {excluded_files_count} ({excluded_percentage:.2f}%)")
    logging.info(f"  {Fore.RED}Fehlgeschlagene Dateien:{Style.RESET_ALL} {len(failed_files)}")

    return dir_structure, summary