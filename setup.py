from setuptools import setup, find_packages

# Basic platform-independent requirements
install_requires = [
    "colorama>=0.4.6",
    "dicttoxml>=1.7.16",
    "PyYAML>=6.0.1",
    "tqdm>=4.65.0",
    "charset-normalizer>=3.2.0",
    "msgpack>=1.0.5",
    "typing-extensions>=4.7.1",
    "pathspec>=0.11.2",
    "rich>=13.5.2",
    "click>=8.1.7",
    "python-magic-bin>=0.4.14; platform_system == 'Windows'",
    "python-magic>=0.4.27; platform_system != 'Windows'"
]

# Development dependencies
extras_require = {
    'dev': [
        'pytest>=7.4.0',
        'pytest-cov>=4.1.0',
        'black>=23.7.0',
        'isort>=5.12.0',
        'mypy>=1.4.1',
        'flake8>=6.1.0',
    ]
}

setup(
    name="repo_analyzer",
    version="0.9.0",
    author="Lucas Richert",
    author_email="info@lucasrichert.tech",
    description="A tool for analyzing repository structures",
    packages=find_packages(),
    python_requires='>=3.9',
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "repo_analyzer=repo_analyzer.main:run",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
