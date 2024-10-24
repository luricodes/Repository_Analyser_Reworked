# Repository Analyzer

[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Repository Analyzer is a powerful Python tool for analyzing and documenting repository structures. It provides detailed insights into your codebase by generating structured reports in multiple formats.

## Features

- **Multiple Output Formats**: 
  - JSON (with streaming support)
  - YAML
  - XML
  - NDJSON (with streaming support)
  - DOT (GraphViz)
  - CSV
  - S-expressions
  - MessagePack (with streaming support)

- **Advanced File Analysis**:
  - Automatic file type detection
  - Encoding detection and normalization
  - Binary file handling
  - File hashing (MD5, SHA1, SHA256, SHA512)
  - File metadata extraction
  - Customizable file size limits

- **Performance Features**:
  - Multi-threading support
  - SQLite-based caching system
  - Streaming mode for large repositories
  - Memory-efficient processing

- **Filtering Capabilities**:
  - Exclude specific folders and files
  - Pattern-based exclusions (glob and regex)
  - Binary file filtering
  - Custom image extension handling

## Installation

### Prerequisites

- Python 3.9 or higher
- Git

### Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/yourusername/repo_analyzer
cd repo_analyzer
```

2. Create and activate a virtual environment:

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install the package:

```bash
# For users
pip install .

# For developers
pip install -e ".[dev]"
```

## Usage

Basic usage:
```bash
repo_analyzer /path/to/repository -o output.json
```

Common examples:
```bash
# Generate JSON output
repo_analyzer /path/to/repo -o analysis.json

# Generate YAML with binary files included
repo_analyzer /path/to/repo -o analysis.yaml --include-binary

# Generate XML excluding specific folders
repo_analyzer /path/to/repo -o analysis.xml --exclude-folders node_modules dist

# Stream large repositories to NDJSON
repo_analyzer /path/to/repo -o analysis --format ndjson ----hash-algorithm sha512
```

For more options:
```bash
repo_analyzer --help
```

### Command Line Options

```
Arguments:
  root_directory          The root directory to analyze

Options:
  -o, --output           Path to the output file
  -f, --format           Output format (default: json)
  --stream               Enable streaming mode (JSON/NDJSON/MessagePack only)
  --hash-algorithm       Hash algorithm (md5, sha1, sha256, sha512)
  --include-binary       Include binary and image files
  --exclude-folders      List of folders to exclude
  --exclude-files        List of files to exclude
  --follow-symlinks      Follow symbolic links
  --image-extensions     Additional image file extensions
  --exclude-patterns     Glob or regex patterns for exclusion
  --threads              Number of threads (default: CPU cores * 2)
  --encoding            Default encoding (default: auto-detect)
  --verbose             Enable verbose logging
  --log-file           Path to log file
  --no-hash            Disable hash verification
  --config             Path to configuration file
  --max-size           Maximum file size in MB
  --pool-size          Database connection pool size
  --include-summary    Add analysis summary to output
  --cache-path         Path to cache directory
```

## Configuration

You can provide configuration through a YAML or JSON file:

```yaml
# config.yaml
exclude_folders:
  - node_modules
  - venv
  - .git
exclude_files:
  - "*.pyc"
  - "*.pyo"
max_size: 50  # MB
```

## Technical Details

### Architecture

Repository Analyzer uses a modular architecture with the following key components:

1. **Core Engine**:
   - Multi-threaded file traversal
   - Concurrent file processing
   - Event-based shutdown handling

2. **File Processing**:
   - MIME type detection using python-magic
   - Charset detection with charset-normalizer
   - Configurable hash computation

3. **Caching System**:
   - SQLite-based file cache
   - Connection pooling
   - WAL journal mode for better concurrency

4. **Output Processing**:
   - Factory pattern for output formats
   - Streaming support for large datasets
   - Atomic file writing

### Performance Considerations

- Uses thread pools for parallel processing
- Implements connection pooling for database operations
- Supports streaming mode for memory-efficient processing
- Includes caching to avoid redundant file analysis
- Provides progress bars for long-running operations

### Default Behaviors

- Excludes common build and temporary directories
- Auto-detects file encodings
- Uses MD5 for file hashing by default
- Limits file size processing to 50MB by default

## Use Cases

- Use it in dot format for putting your repo in a visual map
- I personally created it to have a full repo in one file to pass it further to ChatGPT or Claude
- Documentation of project structures
- Codebase analysis and auditing
- Repository comparisons
- Migration planning
- Dependency analysis
- Project archiving
- The SQLite Database can also be used as repo store

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Lucas Richert  
Contact: info@lucasrichert.tech

## Acknowledgments

- Built with [colorama](https://pypi.org/project/colorama/) for colored output
- Uses [python-magic](https://pypi.org/project/python-magic/) for file type detection
- Uses [charset-normalizer](https://pypi.org/project/charset-normalizer/) for encoding detection
- Uses [tqdm](https://pypi.org/project/tqdm/) for progress bars
