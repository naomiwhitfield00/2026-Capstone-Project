"""Local leaderboards. One JSON file on this computer -- scores are NOT shared
between computers (each install has its own boards)."""
import json
import time

from .paths import data_dir


def _file():
    return data_dir() / "scores.json"


def _load():
    try:
        return json.loads(_file().read_text(encoding="utf-8")).get("scores", [])
    except (OSError, ValueError):
        return []


def add_score(room_id, name, logo, seconds):
    scores = _load()
    scores.append({"room_id": room_id, "name": name, "logo": logo,
                   "seconds": int(seconds), "date": time.strftime("%Y-%m-%d %H:%M")})
    _file().write_text(json.dumps({"scores": scores}, indent=2), encoding="utf-8")


def fmt_time(seconds):
    return f"{seconds // 60}:{seconds % 60:02d}"


def top_scores(room_id, limit=10):
    rows = sorted((s for s in _load() if s["room_id"] == room_id),
                  key=lambda s: (s["seconds"], s["date"]))[:limit]
    return [dict(s, time=fmt_time(s["seconds"])) for s in rows]
