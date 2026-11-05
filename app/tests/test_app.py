"""Run:  python tests/test_app.py      (from the app/ folder)
Plays the whole game through the engine and through the real HTTP server."""
import json
import os
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path

os.environ["ESCAPISM_DATA_DIR"] = tempfile.mkdtemp()
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from escapism_app import profiles, registry, scores                # noqa: E402
from escapism_app.server import make_server                        # noqa: E402
from escapism_app.session import Session                           # noqa: E402

WIN = ["open closet", "take hanger", "look nightstand", "take key", "open door",
       "open living room door", "search couch", "search recliner", "look bookshelf",
       "look war of the worlds", "take notepad", "take pen", "look under keyboard",
       "write password", "write page number", "open door", "take power bank", "open door",
       "plug in claw machine", "play claw", "play claw", "use hanger on door"]


def test_registry():
    rooms = registry.load_rooms(force=True)
    assert not registry.problems, registry.problems
    assert list(rooms) == [1] and rooms[1].room_id == "get_out_of_the_house"
    slots = registry.door_slots()
    assert [s["available"] for s in slots] == [True, False, False, False]
    print("registry OK")


def test_playthrough():
    s = Session()
    assert s.state()["screen"] == "profile" and s.state()["logos"]
    s.login("  Corey   ", "key.svg")
    assert s.profile["name"] == "Corey"
    st = s.state()
    assert st["scene"]["kind"] == "lobby" and st["clock_start"] is None
    s.command("open door 2"); assert s.room is None                      # closed door
    s.command("open door 1"); assert s.room and s.state()["clock_start"]
    for c in WIN:
        s.command(c)
    assert s.room is None and s.profile["completed"] == ["get_out_of_the_house"], s.log[-5:]
    top = scores.top_scores("get_out_of_the_house")
    assert len(top) == 1 and top[0]["name"] == "Corey"
    door1 = s.state()["scene"]["view"]["doors"][0]
    assert door1["status"] == "done" and door1["scores"][0]["name"] == "Corey"
    s.command("open door 1"); assert s.room.loc == "bedroom"             # replay works
    s.leave_room(); assert s.room is None
    print("playthrough OK")


def test_hallway_doors():
    s = Session(); s.login("Tester", "key.svg"); s.command("open door 1")
    s.room.loc = "hallway"
    for c in ["open door", "open door 3", "open the other door", "open left door", "push door"]:
        s.command(c); assert s.room.loc == "hallway", c
    s.command("open living room door"); assert s.room.loc == "hallway"   # no key yet
    s.room.inv.append("keys"); s.command("open living room door"); assert s.room.loc == "living_room"
    print("hallway doors OK")


def test_password_and_keypad():
    s = Session(); s.login("Tester", "key.svg"); s.command("open door 1")
    s.room.loc = "living_room"; s.command("login")
    assert s.state()["hidden_input"]
    s.command("Letsgetout123!")
    assert any(e["kind"] == "input" and e["text"] == "*" * 14 for e in s.log)
    assert s.room.logged_in
    s.room.loc = "hallway"; s.command("open keypad"); s.command("253"); s.command("open keypad")
    assert s.room.loc == "spare_bedroom"
    print("password + keypad OK")


def test_scene_views():
    """Every view.<name> a scene.js reads must exist in the room's view()."""
    import re
    text = (ROOT / "rooms/get_out_of_the_house/scene.js").read_text()
    used = set(re.findall(r"view\.(\w+)", text))
    s = Session(); s.login("Tester", "key.svg"); s.command("open door 1")
    missing = used - set(s.room.view())
    assert not missing, missing
    lobby_used = set(re.findall(r"view\.(\w+)", (ROOT / "escapism_app/ui/js/lobby_scene.js").read_text()))
    assert lobby_used <= {"doors"}, lobby_used
    print("scene views OK:", len(used), "values")


def test_scene_scripts():
    """Run every scene.js against a Three.js stand-in (needs Node.js; skipped if missing)."""
    import shutil, subprocess
    if not shutil.which("node"):
        print("scene scripts SKIPPED (Node.js not installed)")
        return
    s = Session(); s.login("Tester", "key.svg"); s.command("open door 1")
    views = {}
    for loc in ["bedroom", "hallway", "spare_bedroom", "living_room", "kitchen", "garage"]:
        s.room.loc = loc
        views[loc] = s.room.view()
    result = subprocess.run(["node", str(ROOT / "tests/test_scenes.mjs"), json.dumps(views)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    print("scene scripts OK")


def test_server():
    httpd = make_server()
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"

    def get(path):
        return urllib.request.urlopen(base + path)

    def post(path, data):
        req = urllib.request.Request(base + path, json.dumps(data).encode(),
                                     {"Content-Type": "application/json"})
        return json.load(urllib.request.urlopen(req))

    page = get("/").read().decode()
    assert "__THREE_URL__" not in page and "importmap" in page
    assert get("/js/app.js").headers["Content-Type"].startswith("text/javascript")
    assert get("/css/escapism.css").status == 200
    assert get("/logos/key.svg").headers["Content-Type"] == "image/svg+xml"
    assert get("/rooms/get_out_of_the_house/scene.js").status == 200
    for bad in ["/rooms/get_out_of_the_house/room.py", "/css/../../run_escapism.py",
                "/js/%2e%2e/%2e%2e/run_escapism.py", "/nope"]:
        try:
            get(bad); raise AssertionError("should be 404: " + bad)
        except urllib.error.HTTPError as err:
            assert err.code == 404, (bad, err.code)

    state = json.load(get("/api/state"))
    assert state["screen"] == "profile"
    state = post("/api/login", {"name": "Web", "logo": "door.svg"})
    assert state["screen"] == "game" and state["scene"]["kind"] == "lobby"
    state = post("/api/command", {"text": "open door 1"})
    assert state["scene"]["module"] == "/rooms/get_out_of_the_house/scene.js"
    assert state["scene"]["loc"] == "bedroom" and "lamp_on" in state["scene"]["view"]
    boards = json.load(get("/api/leaderboards"))
    assert len(boards) == 4 and boards[1]["available"] is False
    state = post("/api/logout", {})
    assert state["screen"] == "profile" and any(p["name"] == "Web" for p in state["profiles"])
    httpd.shutdown()
    print("server OK")


if __name__ == "__main__":
    test_registry(); test_playthrough(); test_hallway_doors()
    test_password_and_keypad(); test_scene_views(); test_scene_scripts(); test_server()
    print("ALL APP TESTS PASSED")
