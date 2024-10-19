# repo_analyzer/traversal/traverser.py

import logging
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional, Generator
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from tqdm import tqdm

from repo_analyzer.processing.file_processor import process_file
from repo_analyzer.traversal.patterns import matches_patterns
from colorama import Fore, Style

from repo_analyzer.core.flags import shutdown_event

def traverse_and_collect(
    root_dir: Path,
    excluded_folders: Set[str],
    excluded_files: Set[str],
    exclude_patterns: List[str],
    follow_symlinks: bool
) -> Tuple[List[Path], int, int]:
    paths: List[Path] = []
    included = 0
    excluded = 0
    visited_paths: Set[Path] = set()

    stack = [root_dir]

    while stack:
        if shutdown_event.is_set():
            logging.info("Traversal aborted due to shutdown event.")
            break

        current_dir = stack.pop()
        try:
            if follow_symlinks:
                resolved_dir = current_dir.resolve()
                if resolved_dir in visited_paths:
                    logging.warning(
                        f"{Fore.RED}Zirkulärer symbolischer Link gefunden: {current_dir}{Style.RESET_ALL}"
                    )
                    continue
                visited_paths.add(resolved_dir)
        except Exception as e:
            logging.error(
                f"{Fore.RED}Fehler beim Auflösen von {current_dir}: {e}{Style.RESET_ALL}"
            )
            continue

        try:
            for entry in current_dir.iterdir():
                if shutdown_event.is_set():
                    logging.info("Traversal aborted due to shutdown event.")
                    break

                if entry.is_dir():
                    if (
                        entry.name in excluded_folders
                        or matches_patterns(entry.name, exclude_patterns)
                    ):
                        logging.debug(
                            f"{Fore.CYAN}Ausschließen von Ordner: {entry}{Style.RESET_ALL}"
                        )
                        continue
                    stack.append(entry)
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
                if shutdown_event.is_set():
                    break  # Abbruch bei gesetztem Flag
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
                if shutdown_event.is_set():
                    break  # Abbruch bei gesetztem Flag
                file_path: Path = future_to_file[future]
                try:
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

def get_directory_structure_stream(
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
) -> Generator[Dict[str, Any], None, None]:
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
        for file_path in files_to_process:
            if shutdown_event.is_set():
                break  # Abbruch bei gesetztem Flag
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

        try:
            for future in as_completed(future_to_file):
                if shutdown_event.is_set():
                    break  # Abbruch bei gesetztem Flag
                file_path: Path = future_to_file[future]
                try:
                    filename, file_info = future.result()
                    if file_info is not None:
                        try:
                            relative_parent: Path = file_path.parent.relative_to(root_dir)
                        except ValueError:
                            relative_parent = file_path.parent

                        yield {
                            "parent": str(relative_parent),
                            "filename": filename,
                            "info": file_info
                        }
                except Exception as e:
                    logging.error(f"Fehler beim Verarbeiten der Datei {file_path}: {e}")
                    yield {
                        "parent": str(file_path.parent.relative_to(root_dir)) if root_dir in file_path.parent.resolve().parents else str(file_path.parent),
                        "filename": file_path.name,
                        "info": {
                            "type": "error",
                            "content": f"Fehler beim Verarbeiten der Datei: {str(e)}",
                            "exception_type": type(e).__name__,
                            "exception_message": str(e)
                        }
                    }
                finally:
                    pbar.update(1)
        except KeyboardInterrupt:
            logging.warning("\nAbbruch durch Benutzer während der Verarbeitung. Versuche, laufende Aufgaben zu beenden...")
            executor.shutdown(wait=False, cancel_futures=True)
            pbar.close()
            raise

    pbar.close()

    # Zusammenfassung
    summary: Dict[str, Any] = {
        "total_files": total_files,
        "excluded_files": excluded_files_count,
        "included_files": included_files,
        "excluded_percentage": excluded_percentage,
        "failed_files": failed_files
    }

    if hash_algorithm is not None:
        summary["hash_algorithm"] = hash_algorithm

    yield {
        "summary": summary
    }
