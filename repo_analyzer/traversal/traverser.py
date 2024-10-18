# repo_analyzer/traversal/traverser.py

import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional

from colorama import Fore, Style
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from tqdm import tqdm

from repo_analyzer.processing.file_processor import process_file
from repo_analyzer.traversal.patterns import matches_patterns
from repo_analyzer.cache.sqlite_cache import get_connection_context


def traverse_and_collect(
    root_dir: Path,
    excluded_folders: Set[str],
    excluded_files: Set[str],
    exclude_patterns: List[str],
    follow_symlinks: bool
) -> Tuple[List[Path], int, int]:
    """
    Durchläuft das Verzeichnis rekursiv, sammelt eingeschlossene Dateien und zählt
    die Anzahl der eingeschlossenen und ausgeschlossenen Dateien.

    Args:
        root_dir (Path): Das Wurzelverzeichnis zum Traversieren.
        excluded_folders (Set[str]): Eine Menge von Ordnernamen, die ausgeschlossen werden sollen.
        excluded_files (Set[str]): Eine Menge von Dateinamen, die ausgeschlossen werden sollen.
        exclude_patterns (List[str]): Eine Liste von Mustern zum Ausschließen von Dateien und Ordnern.
        follow_symlinks (bool): Gibt an, ob symbolischen Links gefolgt werden sollen.

    Returns:
        Tuple[List[Path], int, int]: Eine Liste der eingeschlossenen Dateipfade,
                                      die Anzahl der eingeschlossenen Dateien und
                                      die Anzahl der ausgeschlossenen Dateien.
    """
    paths: List[Path] = []
    included = 0
    excluded = 0
    visited_paths: Set[Path] = set()

    def _traverse(current_dir: Path) -> None:
        nonlocal included, excluded
        try:
            if follow_symlinks:
                resolved_dir: Path = current_dir.resolve()
                if resolved_dir in visited_paths:
                    logging.warning(
                        f"{Fore.RED}Zirkulärer symbolischer Link gefunden: {current_dir}{Style.RESET_ALL}"
                    )
                    return
                visited_paths.add(resolved_dir)
        except Exception as e:
            logging.error(
                f"{Fore.RED}Fehler beim Auflösen von {current_dir}: {e}{Style.RESET_ALL}"
            )
            return

        try:
            for entry in current_dir.iterdir():
                if entry.is_dir():
                    if (
                        entry.name in excluded_folders
                        or matches_patterns(entry.name, exclude_patterns)
                    ):
                        logging.debug(
                            f"{Fore.CYAN}Ausschließen von Ordner: {entry}{Style.RESET_ALL}"
                        )
                        continue
                    _traverse(entry)
                elif entry.is_file():
                    if (
                        entry.name in excluded_files
                        or matches_patterns(entry.name, exclude_patterns)
                    ):
                        logging.debug(
                            f"{Fore.YELLOW}Ausschließen von Datei: {entry}{Style.RESET_ALL}"
                        )
                        excluded += 1
                        continue
                    paths.append(entry)
                    included += 1
        except PermissionError as e:
            logging.warning(
                f"{Fore.YELLOW}Konnte Verzeichnis nicht lesen: {current_dir} - {e}{Style.RESET_ALL}"
            )
        except Exception as e:
            logging.error(
                f"{Fore.RED}Fehler beim Durchlaufen von {current_dir}: {e}{Style.RESET_ALL}"
            )

    _traverse(root_dir)
    return paths, included, excluded


def get_directory_structure(
    root_dir: Path,
    max_file_size: int,
    include_binary: bool,
    excluded_folders: Set[str],
    excluded_files: Set[str],
    follow_symlinks: bool,
    image_extensions: Set[str],
    exclude_patterns: List[str],
    threads: int,
    encoding: str = 'utf-8',
    hash_algorithm: Optional[str] = "md5",
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Ermittelt die Verzeichnisstruktur und eine Zusammenfassung der Dateien.

    Args:
        root_dir (Path): Das Wurzelverzeichnis zum Traversieren.
        max_file_size (int): Maximale Dateigröße in Bytes.
        include_binary (bool): Ob binäre Dateien einbezogen werden sollen.
        excluded_folders (Set[str]): Ausgeschlossene Ordner.
        excluded_files (Set[str]): Ausgeschlossene Dateien.
        follow_symlinks (bool): Ob symbolischen Links gefolgt werden soll.
        image_extensions (Set[str]): Zusätzliche Bilddateiendungen.
        exclude_patterns (List[str]): Ausgeschlossene Muster.
        threads (int): Anzahl der Threads für die parallele Verarbeitung.
        encoding (str, optional): Standard-Encoding für Textdateien.
        hash_algorithm (Optional[str], optional): Hash-Algorithmus zur Verifizierung.

    Returns:
        Tuple[Dict[str, Any], Dict[str, Any]]: Die Verzeichnisstruktur und die Zusammenfassung.
    """
    dir_structure: Dict[str, Any] = {}

    files_to_process, included_files, excluded_files_count = traverse_and_collect(
        root_dir,
        excluded_folders,
        excluded_files,
        exclude_patterns,
        follow_symlinks
    )
    total_files: int = included_files + excluded_files_count
    excluded_percentage: float = (excluded_files_count / total_files * 100) if total_files else 0.0

    logging.info(f"Gesamtzahl der Dateien: {total_files}")
    logging.info(f"Ausgeschlossene Dateien: {excluded_files_count} ({excluded_percentage:.2f}%)")
    logging.info(f"Verarbeitete Dateien: {included_files}")
    
    pbar: tqdm = tqdm(
        total=included_files,
        desc="Verarbeite Dateien",
        unit="file",
        dynamic_ncols=True
    )

    failed_files: List[Dict[str, str]] = []

    with ThreadPoolExecutor(max_workers=threads) as executor:
        future_to_file: Dict[Future[Tuple[str, Any]], Path] = {}
        try:
            for file_path in files_to_process:
                future = executor.submit(
                    process_file,
                    file_path,
                    max_file_size,
                    include_binary,
                    image_extensions,
                    encoding=encoding,
                    hash_algorithm=hash_algorithm,
                )
                future_to_file[future] = file_path
        except KeyboardInterrupt:
            logging.warning("\nAbbruch durch Benutzer. Versuche, laufende Aufgaben zu beenden...")
            executor.shutdown(wait=False, cancel_futures=True)
            pbar.close()
            raise
        except Exception as e:
            logging.error(f"Unerwarteter Fehler während des Einreichens von Aufgaben: {e}")
            executor.shutdown(wait=False, cancel_futures=True)
            pbar.close()
            raise

        try:
            for future in as_completed(future_to_file):
                file_path: Path = future_to_file[future]
                try:
                    filename: str
                    file_info: Any
                    filename, file_info = future.result()
                    if file_info is not None:
                        try:
                            relative_parent: Path = file_path.parent.relative_to(root_dir)
                        except ValueError:
                            relative_parent = file_path.parent

                        current: Dict[str, Any] = dir_structure
                        for part in relative_parent.parts:
                            current = current.setdefault(part, {})
                        current[filename] = file_info
                except Exception as e:
                    try:
                        relative_parent: Path = file_path.parent.relative_to(root_dir)
                    except ValueError:
                        relative_parent = file_path.parent

                    current: Dict[str, Any] = dir_structure
                    for part in relative_parent.parts:
                        current = current.setdefault(part, {})
                    current[
                        file_path.name
                    ] = {
                        "type": "error",
                        "content": f"<Fehler bei der Verarbeitung: {str(e)}>"
                    }
                    logging.error(f"Fehler beim Verarbeiten der Datei {file_path}: {e}")
                    failed_files.append(
                        {"file": str(file_path), "error": str(e)}
                    )
                finally:
                    pbar.update(1)
        except KeyboardInterrupt:
            logging.warning("\nAbbruch durch Benutzer während der Verarbeitung. Versuche, laufende Aufgaben zu beenden...")
            executor.shutdown(wait=False, cancel_futures=True)
            pbar.close()
            raise

    pbar.close()

    summary: Dict[str, Any] = {
        "total_files": total_files,
        "excluded_files": excluded_files_count,
        "included_files": included_files,
        "excluded_percentage": excluded_percentage,
        "failed_files": failed_files
    }

    if hash_algorithm is not None:
        summary["hash_algorithm"] = hash_algorithm

    logging.info("Zusammenfassung:")
    logging.info(f"  Verarbeitete Dateien: {included_files}")
    logging.info(f"  Ausgeschlossene Dateien: {excluded_files_count} ({excluded_percentage:.2f}%)")
    logging.info(f"  Fehlgeschlagene Dateien: {len(failed_files)}")
    if hash_algorithm is not None:
        logging.info(f"  Verwendeter Hash-Algorithmus: {hash_algorithm}")

    return dir_structure, summary
