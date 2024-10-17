from setuptools import setup, find_packages
from typing import Optional, List, Dict, Any

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setup(
    name="repo_analyzer",
    version="0.9.0",
    author="Lucas Richert",
    author_email="info@lucasrichert.tech",
    description="Ein Tool zur Analyse von Repository-Strukturen",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "colorama>=0.4.4",
        "dicttoxml>=1.7.4",
        "python-magic-bin>=0.4.14",
        "PyYAML>=5.4.1",
        "tqdm>=4.60.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
        "console_scripts": [
            "repo_analyzer=repo_analyzer.main:run",
        ],
    },
)
