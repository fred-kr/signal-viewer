"""
Site configuration module.

Supplies the running `SVApp` instance with path information.
"""

from pathlib import Path

INSTALLDIR = Path(__file__).parent
ICONDIR = INSTALLDIR / "icons"
DOCDIR = INSTALLDIR / "doc"
BINDIR = INSTALLDIR / "bin"