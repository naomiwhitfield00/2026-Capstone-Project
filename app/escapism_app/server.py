"""A tiny local web server. The game window (or your browser) talks to it.

It only listens on 127.0.0.1, so nothing on the network can reach it.

  GET  /                      the game page (ui/index.html)
  GET  /css|js|logos|vendor/  files from ui/
  GET  /rooms/<room>/...      scene.js and assets from a room's folder
  GET  /api/state             everything the page needs to draw itself
  POST /api/login             {name, logo}
  POST /api/logout
  POST /api/command           {text}
  POST /api/leave_room
  GET  /api/leaderboards
  GET  /api/ping              heartbeat (lets the app exit when the browser tab closes)
"""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from . import APP_NAME, APP_VERSION
from .paths import rooms_dir, ui_dir
from .session import Session

THREE_CDN = "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js"
MIME = {
    ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml", ".png": "image/png",
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp",
    ".json": "application/json", ".glb": "model/gltf-binary", ".gltf": "model/gltf+json",
    ".mp3": "audio/mpeg", ".ogg": "audio/ogg", ".wav": "audio/wav",
}
UI_FOLDERS = ("css", "js", "logos", "vendor")


class AppState:
    """Shared by all requests (the game has exactly one player)."""
    def __init__(self):
        self.session = Session()
        self.last_ping = None          # None until a page has loaded
        self.lock = threading.Lock()


def make_server(host="127.0.0.1", port=0):
    app = AppState()

    class Handler(BaseHTTPRequestHandler):
        server_version = f"{APP_NAME}/{APP_VERSION}"

        def log_message(self, *args):  # keep the console quiet
            pass

        # ---- responses -----------------------------------------------
        def _send(self, status, body, content_type):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, data, status=200):
            self._send(status, json.dumps(data).encode("utf-8"), "application/json")

        def _file(self, path):
            if not path.is_file():
                self._send(404, b"Not found", "text/plain")
                return
            self._send(200, path.read_bytes(), MIME.get(path.suffix.lower(), "application/octet-stream"))

        @staticmethod
        def _safe(base, relative):
            """Resolve `relative` under `base`, refusing anything that escapes it."""
            target = (base / relative).resolve()
            try:
                target.relative_to(base.resolve())
            except ValueError:
                return None
            return target

        # ---- GET -----------------------------------------------------
        def do_GET(self):
            path = unquote(urlparse(self.path).path)
            if path in ("/", "/index.html"):
                html = (ui_dir() / "index.html").read_text(encoding="utf-8")
                local_three = ui_dir() / "vendor" / "three.module.js"
                html = html.replace("__THREE_URL__", "/vendor/three.module.js"
                                    if local_three.exists() else THREE_CDN)
                html = html.replace("__VERSION__", APP_VERSION)
                self._send(200, html.encode("utf-8"), MIME[".html"])
            elif path == "/api/state":
                app.last_ping = time.time()
                with app.lock:
                    self._json(app.session.state())
            elif path == "/api/leaderboards":
                with app.lock:
                    self._json(app.session.leaderboards())
            elif path == "/api/ping":
                app.last_ping = time.time()
                self._json({"ok": True})
            elif path.startswith("/rooms/"):
                target = self._safe(rooms_dir(), path[len("/rooms/"):])
                ok = target is not None and target.suffix.lower() in MIME and target.name != "room.py"
                self._file(target) if ok else self._send(404, b"Not found", "text/plain")
            elif path.split("/")[1:2] and path.split("/")[1] in UI_FOLDERS:
                target = self._safe(ui_dir(), path.lstrip("/"))
                self._file(target) if target else self._send(404, b"Not found", "text/plain")
            else:
                self._send(404, b"Not found", "text/plain")

        # ---- POST ----------------------------------------------------
        def do_POST(self):
            path = urlparse(self.path).path
            length = int(self.headers.get("Content-Length") or 0)
            try:
                data = json.loads(self.rfile.read(length) or b"{}")
            except ValueError:
                data = {}
            with app.lock:
                s = app.session
                if path == "/api/login":
                    s.login(str(data.get("name", "")), str(data.get("logo", "")))
                elif path == "/api/logout":
                    s.logout()
                elif path == "/api/command":
                    s.command(str(data.get("text", ""))[:200])
                elif path == "/api/leave_room":
                    s.leave_room()
                else:
                    self._send(404, b"Not found", "text/plain")
                    return
                self._json(s.state())

    httpd = ThreadingHTTPServer((host, port), Handler)
    httpd.app_state = app
    return httpd
