"""
paths.py — Frozen-aware path resolution for writable and read-only data.

In a PyInstaller frozen build:
  - Writable data (saves, settings) -> %APPDATA%\\LetsGolf\\
  - Read-only assets                -> sys._MEIPASS  (the bundle root)

In dev mode both return the repository root so nothing changes during
development.

On the web (Emscripten/pygbag) writable paths return the bare relative form
("saves", "data/settings.json") because the save system uses them as
localStorage keys rather than real filesystem paths.
"""

import os
import sys

_IS_WEB = sys.platform == "emscripten"


def _repo_root() -> str:
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def writable_root() -> str:
    """Root directory for user-writable data (saves, settings)."""
    if _IS_WEB:
        return ""
    if getattr(sys, "frozen", False):
        appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(appdata, "LetsGolf")
    return _repo_root()


def asset_root() -> str:
    """Root directory for read-only bundled assets."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return _repo_root()


def saves_dir() -> str:
    if _IS_WEB:
        return "saves"
    return os.path.join(writable_root(), "saves")


def settings_path() -> str:
    if _IS_WEB:
        return os.path.join("data", "settings.json")
    return os.path.join(writable_root(), "data", "settings.json")


def asset_path(*parts: str) -> str:
    return os.path.join(asset_root(), *parts)
