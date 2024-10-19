# repo_analyzer/config/defaults.py

DEFAULT_EXCLUDED_FOLDERS = {
    'tmp',
    'node_modules',
    '.git',
    'dist',
    'build',
    'out',
    'target',
    'public',
    'cache',
    'temp',
    'coverage',
    'test-results',
    'reports',
    '.vscode',
    '.idea',
    'logs',
    'assets',
    'bower_components',
    '.next'
    'venv'
}

DEFAULT_EXCLUDED_FILES = {
    'config.json',
    'secret.txt',
    'package-lock.json',
    'favicon.ico',
    'GeistMonoVF.woff',
    'GeistVF.woff',
    '.repo_structure_cache',
}

DEFAULT_MAX_FILE_SIZE_MB = 50  #Megabyte

CACHE_DB_FILE = '.repo_structure_cache.db'
