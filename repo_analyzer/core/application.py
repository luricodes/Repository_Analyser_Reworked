# repo_analyzer/core/application.py

import logging
import signal
import multiprocessing
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Set, List

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
    DEFAULT_MAX_FILE_SIZE_MB
)
from repo_analyzer.logging.setup import setup_logging
from repo_analyzer.output.output_factory import OutputFactory
from repo_analyzer.traversal.traverser import get_directory_structure, get_directory_structure_stream
from colorama import init as colorama_init

from .flags import shutdown_event

DEFAULT_THREAD_MULTIPLIER = 2

def signal_handler(sig, frame):
    if not shutdown_event.is_set():
        logging.warning("Programme interrupted by user (CTRL+C).")
        shutdown_event.set()
    else:
        logging.warning("Second CTRL+C recognised. Immediate cancellation.")
        sys.exit(1)

def initialize_cache_directory(cache_path: Path) -> Path:
    try:
        cache_path.mkdir(parents=True, exist_ok=True)
        logging.debug(f"Cache directory created or already exists: {cache_path}")
    except OSError as e:
        logging.error(f"Error when creating the cache directory '{cache_path}': {e}")
        sys.exit(1)
    return cache_path

def run() -> None:
    colorama_init(autoreset=True)
    args = parse_arguments()

    # Register the global signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    config_manager = Config()
    try:
        config_manager.load(args.config)
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {args.config}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error loading the configuration file: {e}")
        sys.exit(1)
    config = config_manager.data

    setup_logging(args.verbose, args.log_file)

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
    stream_mode: bool = args.stream
    threads: Optional[int] = args.threads
    exclude_patterns: List[str] = args.exclude_patterns
    encoding: Optional[str] = args.encoding
    cache_path: Path = Path(args.cache_path).expanduser().resolve()
    pool_size: int = args.pool_size

    if args.no_hash:
        hash_algorithm = None
        logging.info("Hash verification is deactivated.")
    else:
        hash_algorithm = args.hash_algorithm
        logging.info(f"Use hash algorithm: {hash_algorithm}")

    if threads is None:
        threads = multiprocessing.cpu_count() * DEFAULT_THREAD_MULTIPLIER
        logging.info(f"Dynamically defined number of threads: {threads}")

    try:
        max_file_size = config_manager.get_max_size(cli_max_size=args.max_size)
        logging.info(f"Maximum file size for reading: {max_file_size / (1024 * 1024)} MB")
    except ValueError as ve:
        logging.error(f"Error when determining the maximum file size: {ve}")
        sys.exit(1)

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

    logging.info(f"Search the directory: {root_directory}")
    logging.info(f"Excluded folders: {', '.join(sorted(excluded_folders))}")
    logging.info(f"Excluded files: {', '.join(sorted(excluded_files))}")
    if not include_binary:
        logging.info("Binary files and image files are excluded.")
    else:
        logging.info("Binary files and image files are included.")
    logging.info(f"Issue in: {output_file} ({output_format})")
    logging.info(
        f"Symbolic links are {'followed' if follow_symlinks else 'not followed'}"
    )
    logging.info(f"Image file extensions: {', '.join(sorted(image_extensions))}")
    logging.info(f"Exclusion pattern: {', '.join(exclude_patterns)}")
    logging.info(f"Number of threads: {threads}")
    logging.info(f"Standard encoding: {encoding}")
    logging.info(f"Cache path: {cache_path}")

    cache_dir: Path = initialize_cache_directory(cache_path)
    cache_db_path: Path = cache_dir / CACHE_DB_FILE
    db_path_str: str = str(cache_db_path)
    try:
        initialize_connection_pool(db_path_str, pool_size=pool_size)
    except Exception as e:
        logging.error(f"Error when initialising the connection pool: {e}")
        sys.exit(1)

    try:
        clean_cache(root_directory)
    except Exception as e:
        logging.error(f"Error when clearing the cache: {e}")
        sys.exit(1)

    try:
        if stream_mode:
            # Use Streaming-Mode
            if output_format in ["json", "ndjson", "msgpack"]:
                # USE JSON-Streaming or NDJSON-Output or MsgPack-Output
                data_gen = get_directory_structure_stream(
                    root_dir=root_directory,
                    max_file_size=max_file_size,
                    include_binary=include_binary,
                    excluded_folders=excluded_folders,
                    excluded_files=excluded_files,
                    follow_symlinks=follow_symlinks,
                    image_extensions=image_extensions,
                    exclude_patterns=exclude_patterns,
                    threads=threads,
                    encoding=encoding,
                    hash_algorithm=hash_algorithm,
                )
                output_function = OutputFactory.get_output(output_format, streaming=stream_mode)
                output_function(data_gen, output_file)
            else:
                logging.error("--stream is only available for the JSON, NDJSON & MsgPack formats.")
                sys.exit(1)
        else:
            # Standardmode
            structure, summary = get_directory_structure(
                root_dir=root_directory,
                max_file_size=max_file_size,
                include_binary=include_binary,
                excluded_folders=excluded_folders,
                excluded_files=excluded_files,
                follow_symlinks=follow_symlinks,
                image_extensions=image_extensions,
                exclude_patterns=exclude_patterns,
                threads=threads,
                encoding=encoding,
                hash_algorithm=hash_algorithm,
            )
            # Generate summary
            output_data: Dict[str, Any] = {
                "summary": summary,
                "structure": structure
            } if include_summary else structure
            OutputFactory.get_output(output_format)(output_data, output_file)

        logging.info(
            f"The current status of the folder structure"
            f"{' and the summary ' if include_summary else ''}"
            f" have been saved in'{output_file}'"
        )
    except KeyboardInterrupt:
        if shutdown_event.is_set():
            logging.warning("Forced programme abort.")
        else:
            logging.warning("Programme interrupted by user (CTRL+C).")
        sys.exit(1)
    except (OSError, IOError) as e:
        logging.error(
            f"Error when writing the output file after cancellation: {str(e)}"
        )
        sys.exit(1)
    except ValueError as ve:
        logging.error(f"Error when selecting the output format: {ve}")
        sys.exit(1)
    finally:
        try:
            close_all_connections()
        except Exception as e:
            logging.error(f"Error when closing the connections: {e}")
