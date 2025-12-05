"""
Bouncer setup script
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme = Path("README.md").read_text() if Path("README.md").exists() else ""

setup(
    name="bouncer-agent",
    version="1.0.0",
    description="AI-powered file monitoring agent - Quality control at the door",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Bouncer Team",
    url="https://github.com/yourusername/bouncer",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "claude-agent-sdk>=0.1.12",
        "watchdog>=3.0.0",
        "pyyaml>=6.0.0",
        "aiohttp>=3.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pylint>=3.0.0",
            "black>=23.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "bouncer=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
