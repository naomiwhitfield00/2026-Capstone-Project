"""Player profiles (a name + a logo), saved as JSON in the player's data folder."""
import json
import re

from .paths import data_dir, ui_dir

LOGO_TYPES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}


def _file():
    return data_dir() / "profiles.json"


def available_logos():
    """File names found in ui/logos/. Drop new images in there to add logos."""
    folder = ui_dir() / "logos"
    if not folder.exists():
        return []
    return sorted(p.name for p in folder.iterdir() if p.suffix.lower() in LOGO_TYPES)


def load_all():
    try:
        return json.loads(_file().read_text(encoding="utf-8")).get("profiles", [])
    except (OSError, ValueError):
        return []


def _save_all(profiles):
    _file().write_text(json.dumps({"profiles": profiles}, indent=2), encoding="utf-8")


def clean_name(name):
    name = re.sub(r"\s+", " ", (name or "")).strip()[:20]
    return name or "Anonymous"


def save_profile(name, logo):
    """Create the profile, or update the logo if that name already exists."""
    name = clean_name(name)
    logos = available_logos()
    if logo not in logos:
        logo = logos[0] if logos else ""
    profiles = load_all()
    for p in profiles:
        if p["name"].lower() == name.lower():
            p["logo"] = logo
            _save_all(profiles)
            return p
    profile = {"name": name, "logo": logo, "completed": []}
    profiles.append(profile)
    _save_all(profiles)
    return profile


def find(name):
    for p in load_all():
        if p["name"].lower() == (name or "").lower():
            return p
    return None


def mark_completed(name, room_id):
    """Remember that this player has escaped a room (the lobby shows it as done)."""
    profiles = load_all()
    for p in profiles:
        if p["name"].lower() == name.lower():
            done = p.setdefault("completed", [])
            if room_id not in done:
                done.append(room_id)
            _save_all(profiles)
            return p
    return None
