"""Where things live on disk.

* `app_root()`  -- the folder that contains `escapism_app/` and `rooms/`.
                  Works both when running from source and when packaged
                  into an .exe with PyInstaller.
* `data_dir()`  -- where the player's profiles and scores are saved
                  (outside the program folder, so updates never erase them).
"""
import os
import sys
from pathlib import Path


def app_root() -> Path:
    if getattr(sys, "frozen", False):                 # packaged with PyInstaller
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


def ui_dir() -> Path:
    return app_root() / "escapism_app" / "ui"


def rooms_dir() -> Path:
    return app_root() / "rooms"


def data_dir() -> Path:
    override = os.environ.get("ESCAPISM_DATA_DIR")     # used by the tests
    if override:
        path = Path(override)
    elif os.name == "nt":
        path = Path(os.environ.get("APPDATA", Path.home())) / "Escapism"
    else:
        path = Path.home() / ".escapism"
    path.mkdir(parents=True, exist_ok=True)
    return path
