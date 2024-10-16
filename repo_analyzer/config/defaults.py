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
    'bower_components'
}

DEFAULT_EXCLUDED_FILES = {
    'config.json', 'secret.txt', 'package-lock.json',
    'favicon.ico', 'GeistMonoVF.woff', 'GeistVF.woff'
}

DEFAULT_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

CACHE_DB_FILE = '.repo_structure_cache.db'