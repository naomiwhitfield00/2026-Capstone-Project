"""Downloads Three.js (the 3D library) into the game so it works offline.
Run once:   python tools/fetch_three.py
(The game also tries to do this by itself the first time it starts.)"""
import sys
import urllib.request
from pathlib import Path

URL = "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js"
target = Path(__file__).resolve().parent.parent / "escapism_app" / "ui" / "vendor" / "three.module.js"
target.parent.mkdir(parents=True, exist_ok=True)
try:
    with urllib.request.urlopen(URL, timeout=30) as response:
        target.write_bytes(response.read())
except Exception as exc:
    sys.exit(f"Could not download Three.js: {exc}\nDownload {URL} by hand and save it as {target}")
print("Saved", target, f"({target.stat().st_size // 1024} KB)")
