import base64
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple, Union

from ..cache.sqlite_cache import get_cached_entry, set_cached_entry, get_connection_context
from ..processing.hashing import compute_file_hash
from ..utils.mime_type import is_binary

import charset_normalizer

logger = logging.getLogger(__name__)

def process_file(
    file_path: Path,
    max_file_size: int,
    include_binary: bool,
    image_extensions: Set[str],
    encoding: Optional[str] = None,  # Standard-Encoding ist jetzt None
    hash_algorithm: Optional[str] = "md5",
) -> Tuple[str, Optional[Dict[str, Any]]]:
    filename = file_path.name

    try:
        stat = file_path.stat()
        current_size = stat.st_size
        current_mtime = stat.st_mtime
    except OSError as e:
        logger.error(f"Failed to get file stats for {file_path}: {e}")
        return filename, {
            "type": "error",
            "content": f"Failed to get file stats: {str(e)}",
            "exception_type": type(e).__name__,
            "exception_message": str(e)
        }

    if current_size > max_file_size:
        logger.info(f"File too large and will be excluded: {file_path} ({current_size} bytes)")
        return filename, {
            "type": "excluded",
            "reason": "file_size",
            "size": current_size
        }

    file_hash = None
    file_info = None

    if hash_algorithm is not None:
        cached_entry = _check_cache(file_path, current_size, current_mtime, hash_algorithm)
        if cached_entry:
            return filename, cached_entry

    if hash_algorithm is not None:
        file_hash = _compute_hash(file_path, hash_algorithm)
        if isinstance(file_hash, dict) and file_hash.get("type") == "error":
            return filename, file_hash

    file_info = _process_file_content(file_path, include_binary, image_extensions, max_file_size, encoding)
    if file_info.get("type") in ["error", "excluded"]:
        return filename, file_info

    _add_metadata(file_info, stat)

    if hash_algorithm is not None and file_hash is not None:
        _update_cache(file_path, file_hash, hash_algorithm, file_info, current_size, current_mtime)

    return filename, file_info

def _check_cache(file_path: Path, current_size: int, current_mtime: float, hash_algorithm: str) -> Optional[Dict[str, Any]]:
    with get_connection_context() as conn:
        cached_entry = get_cached_entry(conn, str(file_path.resolve()))

    if cached_entry:
        cached_size = cached_entry.get("size")
        cached_mtime = cached_entry.get("mtime")
        cached_algorithm = cached_entry.get("hash_algorithm")

        if (
            cached_size == current_size and
            cached_mtime == current_mtime and
            cached_algorithm == hash_algorithm
        ):
            logger.debug(f"Cache hit for file: {file_path}")
            return cached_entry.get("file_info")

    return None

def _compute_hash(file_path: Path, hash_algorithm: str) -> Union[str, Dict[str, Any]]:
    try:
        return compute_file_hash(file_path, algorithm=hash_algorithm)
    except Exception as e:
        logger.error(f"Failed to compute hash for {file_path}: {e}")
        return {
            "type": "error",
            "content": f"Failed to compute hash: {str(e)}",
            "exception_type": type(e).__name__,
            "exception_message": str(e)
        }

def _process_file_content(file_path: Path, include_binary: bool, image_extensions: Set[str], max_file_size: int, encoding: str) -> Dict[str, Any]:
    file_extension = file_path.suffix.lower()
    is_image = file_extension in image_extensions

    try:
        binary = is_binary(file_path)

        if (binary or is_image) and not include_binary:
            logger.debug(f"Excluding {'binary' if binary else 'image'} file: {file_path}")
            return {
                "type": "excluded",
                "reason": "binary_or_image"
            }

        if binary:
            return _read_binary_file(file_path, max_file_size)
        else:
            return _read_text_file(file_path, max_file_size, encoding)

    except PermissionError as e:
        logger.error(f"Permission denied when reading file: {file_path}")
        return {
            "type": "error",
            "content": f"Permission denied: {str(e)}",
            "exception_type": type(e).__name__,
            "exception_message": str(e)
        }
    except IsADirectoryError:
        logger.error(f"Attempted to process a directory as a file: {file_path}")
        return {
            "type": "error",
            "content": "Is a directory"
        }
    except OSError as e:
        logger.error(f"OS error when processing file {file_path}: {e}")
        return {
            "type": "error",
            "content": f"OS error: {str(e)}",
            "exception_type": type(e).__name__,
            "exception_message": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error when processing file {file_path}: {e}")
        return {
            "type": "error",
            "content": f"Unexpected error: {str(e)}",
            "exception_type": type(e).__name__,
            "exception_message": str(e)
        }

def _read_binary_file(file_path: Path, max_file_size: int) -> Dict[str, Any]:
    try:
        file_size = file_path.stat().st_size
        if file_size > max_file_size:
            logger.info(f"Binary file too large to include: {file_path} ({file_size} bytes)")
            return {
                "type": "excluded",
                "reason": "binary_too_large",
                "size": file_size
            }
        
        with open(file_path, 'rb') as f:
            content = base64.b64encode(f.read()).decode('utf-8')
        logger.debug(f"Included binary file: {file_path}")
        return {
            "type": "binary",
            "content": content
        }
    except Exception as e:
        logger.error(f"Error reading binary file {file_path}: {e}")
        return {
            "type": "error",
            "content": f"Failed to read binary file: {str(e)}",
            "exception_type": type(e).__name__,
            "exception_message": str(e)
        }

def _read_text_file(file_path: Path, max_file_size: int, encoding: Optional[str]) -> Dict[str, Any]:
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(max_file_size)

        if encoding is None:
            result = charset_normalizer.from_bytes(raw_data).best()
            if result:
                encoding_to_use = result.encoding
                content = result.str()
                logger.debug(f"Detected encoding '{encoding_to_use}' for file {file_path}")
            else:
                encoding_to_use = 'utf-8'
                content = raw_data.decode(encoding_to_use, errors='replace')
                logger.warning(f"Could not detect encoding for {file_path}. Falling back to 'utf-8'.")
        else:
            encoding_to_use = encoding
            content = raw_data.decode(encoding_to_use, errors='replace')
            logger.debug(f"Using provided encoding '{encoding}' for file {file_path}")

        logger.debug(f"Read text file: {file_path} with encoding {encoding_to_use}")
        return {
            "type": "text",
            "encoding": encoding_to_use,
            "content": content
        }
    except Exception as e:
        logger.error(f"Error reading text file {file_path}: {e}")
        return {
            "type": "error",
            "content": f"Failed to read text file: {str(e)}",
            "exception_type": type(e).__name__,
            "exception_message": str(e)
        }

def _add_metadata(file_info: Dict[str, Any], stat: os.stat_result) -> None:
    try:
        file_info.update({
            "size": stat.st_size,
            "created": getattr(stat, 'st_birthtime', None),
            "modified": stat.st_mtime,
            "permissions": oct(stat.st_mode)
        })
    except Exception as e:
        logger.warning(f"Could not retrieve complete metadata: {e}")

def _update_cache(file_path: Path, file_hash: str, hash_algorithm: str, file_info: Dict[str, Any], current_size: int, current_mtime: float) -> None:
    with get_connection_context() as conn:
        set_cached_entry(
            conn,
            str(file_path.resolve()),
            file_hash,
            hash_algorithm,
            file_info,
            current_size,
            current_mtime
        )
