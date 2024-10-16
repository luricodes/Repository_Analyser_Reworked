from setuptools import setup, find_packages
from typing import Optional, List, Dict, Any

setup(
    name="repo_analyzer",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "colorama",
        "dicttoxml",
        "python-magic",
        "PyYAML",
        "tqdm",
    ],
    entry_points={
        "console_scripts": [
            "repo_analyzer=repo_analyzer.main:main",
        ],
    },
)