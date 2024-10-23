# repo_analyzer/cli/parser.py

import argparse
import os
from pathlib import Path

def get_default_cache_path() -> str:
    home = Path.home()
    return str(home / "Documents" / "Datenbank") if os.name == 'nt' else str(home / ".repo_analyzer" / "cache")

def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Lists a repository into a JSON, YAML, XML, NDJSON, DOT, or CSV file."
        ),
        epilog=(
            "Examples:\\n"
            "  repo_analyzer /path/to/repo -o output.json\\n"
            "  repo_analyzer --exclude-folders build dist --include-binary --format yaml\\n"
            "  repo_analyzer /path/to/repo -o output.ndjson --format ndjson --stream\\n"
            "  repo_analyzer /path/to/repo -o output.dot --format dot\\n"
            "  repo_analyzer /path/to/repo -o output.csv --format csv\\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "root_directory",
        type=str,
        help="The root directory of the repository to be analyzed."
    )
    
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="Path to the output file."
    )
    parser.add_argument(
        "--hash-algorithm",
        type=str,
        choices=["md5", "sha1", "sha256", "sha512"],
        default="md5",
        help="Hash algorithm for verification (default: md5)."
    )
    parser.add_argument(
        "--include-binary",
        action="store_true",
        help="Includes binary files and image files in the analysis."
    )
    parser.add_argument(
        "--exclude-folders",
        nargs='*',
        default=[],
        help="List of folder names to be excluded from the analysis."
    )
    parser.add_argument(
        "--exclude-files",
        nargs='*',
        default=[],
        help="List of file names to be excluded from the analysis."
    )
    parser.add_argument(
        "--follow-symlinks",
        action="store_true",
        help="Follows symbolic links during traversal."
    )
    parser.add_argument(
        "--image-extensions",
        nargs='*',
        default=[],
        help="Additional image file extensions to be considered as binary."
    )
    parser.add_argument(
        "--exclude-patterns",
        nargs='*',
        default=[],
        help="Glob or regex patterns to exclude files and folders."
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=None,
        help="Number of threads for parallel processing (default: CPU cores * 2)."
    )
    parser.add_argument(
        "--encoding",
        type=str,
        default=None,
        help="Default encoding for text files (default: auto detection)."
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Enables streaming mode for JSON and NDJSON output. It is enabled by default for NDJSON.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enables verbose logging."
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Path to the log file."
    )
    parser.add_argument(
        "--no-hash",
        action="store_true",
        help="Disables hash verification."
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to the configuration file."
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=None,
        help="Maximum file size to read in MB (overrides configuration file)."
    )
    parser.add_argument(
        "--pool-size",
        type=int,
        default=5,
        help="Size of the database connection pool (default: 5)."
    )
    parser.add_argument(
        "--include-summary",
        action="store_true",
        help="Adds a summary of the analysis to the output file."
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["json", "yaml", "xml", "ndjson", "dot", "csv"],
        default="json",
        help="Output file format (default: json).",
    )
    parser.add_argument(
        "--cache-path",
        type=str,
        default=get_default_cache_path(),
        help="Path to the cache directory (default: ~/.repo_analyzer/cache)."
    )
    
    args = parser.parse_args()

    # Validate output extension
    expected_extension = f".{args.format}"
    if not args.output.lower().endswith(expected_extension):
        args.output += expected_extension

    # Additional validations
    if args.stream and args.format not in ["json", "ndjson"]:
        parser.error("--stream is only available for JSON and NDJSON formats.")

    # Automatically enable --stream for ndjson
    if args.format == "ndjson":
        args.stream = True


    return args
