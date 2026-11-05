"""Starts the local server and opens the game in its own window.

* If `pywebview` is installed (it is, in the packaged .exe) the game opens in a
  real application window.
* Otherwise it opens your normal web browser and quits a few seconds after you
  close the tab.
"""
import sys
import threading
import time
import urllib.request
import webbrowser

from . import APP_NAME
from .paths import ui_dir
from .server import THREE_CDN, make_server


def ensure_three():
    """Saves Three.js next to the game so it works offline. Quietly skips it if
    we can't download it (the page then loads it from the internet instead)."""
    target = ui_dir() / "vendor" / "three.module.js"
    if target.exists():
        return
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(THREE_CDN, timeout=15) as response:
            target.write_bytes(response.read())
    except Exception:
        pass


def _watch_for_closed_tab(httpd):
    """Browser mode: exit once the page stops sending heartbeats."""
    app = httpd.app_state
    while True:
        time.sleep(2)
        if app.last_ping and time.time() - app.last_ping > 15:
            httpd.shutdown()
            return


def main():
    ensure_three()
    httpd = make_server()
    port = httpd.server_address[1]
    url = f"http://127.0.0.1:{port}/"
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    try:
        import webview                                   # optional: a real app window
    except ImportError:
        webview = None

    if webview is not None:
        webview.create_window(APP_NAME, url, width=1280, height=820, min_size=(900, 600))
        webview.start()                                  # returns when the window is closed
    else:
        print(f"{APP_NAME} is running at {url}")
        print("Close the browser tab to quit (or press Ctrl+C).")
        webbrowser.open(url)
        watcher = threading.Thread(target=_watch_for_closed_tab, args=(httpd,), daemon=True)
        watcher.start()
        try:
            while watcher.is_alive():
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
    httpd.shutdown()
    sys.exit(0)
