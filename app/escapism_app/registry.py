"""Finds the escape rooms.

Every folder inside `rooms/` that contains a `room.py` with a class called
`Room` is an escape room. Folders starting with "_" (like `_template`) are
ignored. Nobody has to edit a shared file to add a room: drop in your folder
and set `door = N` on your Room class.
"""
import importlib.util
import sys
import traceback

from . import parser, room_base  # noqa: F401  (imported so the packaged .exe includes them for room files)
from .paths import rooms_dir

DOOR_COUNT = 4
_cache = None
problems = []   # human-readable messages about rooms that failed to load


def _load_room_class(folder):
    module_name = f"escapism_rooms_{folder.name}"
    spec = importlib.util.spec_from_file_location(module_name, folder / "room.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module.Room


def load_rooms(force=False):
    """Returns {door_number: Room class}."""
    global _cache
    if _cache is not None and not force:
        return _cache
    problems.clear()
    found = {}
    root = rooms_dir()
    folders = sorted(p for p in root.iterdir()
                     if p.is_dir() and not p.name.startswith(("_", ".")) and (p / "room.py").exists()) \
        if root.exists() else []
    for folder in folders:
        try:
            cls = _load_room_class(folder)
            cls.folder_name = folder.name
            if not cls.room_id:
                raise ValueError("Room.room_id is empty")
            if cls.door not in range(1, DOOR_COUNT + 1):
                raise ValueError(f"Room.door must be 1-{DOOR_COUNT}, not {cls.door!r}")
            if cls.door in found:
                raise ValueError(f"door {cls.door} is already used by "
                                 f"'{found[cls.door].folder_name}'")
            if not cls.start_loc or not hasattr(cls, f"describe_{cls.start_loc}"):
                raise ValueError(f"Room.start_loc {cls.start_loc!r} needs a describe_{cls.start_loc}() method")
            found[cls.door] = cls
        except Exception as exc:                      # keep the game running; report the problem
            problems.append(f"rooms/{folder.name}: {exc}")
            traceback.print_exc()
    _cache = found
    return found


def room_for_door(number):
    return load_rooms().get(number)


def room_by_id(room_id):
    for cls in load_rooms().values():
        if cls.room_id == room_id:
            return cls
    return None


def door_slots():
    """One entry per lobby door: the room's info, or a 'coming soon' placeholder."""
    rooms = load_rooms()
    slots = []
    for number in range(1, DOOR_COUNT + 1):
        cls = rooms.get(number)
        if cls:
            slots.append({"number": number, "room_id": cls.room_id, "title": cls.title,
                          "author": cls.author, "available": True})
        else:
            slots.append({"number": number, "room_id": f"door{number}", "title": "Coming soon",
                          "author": "", "available": False})
    return slots
