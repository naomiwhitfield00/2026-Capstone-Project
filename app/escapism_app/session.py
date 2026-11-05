"""The running game: who is playing, which room they are in, the text log, and
the clock. The server (server.py) is a thin layer that calls into this."""
import time
import traceback

from . import lobby, profiles, scores
from .registry import room_for_door, problems, door_slots

LOBBY = "__lobby__"


class Session:
    def __init__(self):
        self.profile = None       # {"name", "logo", "completed": [...]}
        self.room = None          # the active Room instance, or None in the lobby
        self.room_start = None    # epoch seconds when the player stepped into the room
        self.log = []             # [{"kind": "input"|"system", "text": ...}]

    # ---- profile ---------------------------------------------------------
    def login(self, name, logo):
        self.profile = profiles.save_profile(name, logo)
        self.room, self.room_start, self.log = None, None, []
        self._say(["Welcome, " + self.profile["name"] + "."])
        self._say(lobby.describe(self.completed()))
        if problems:
            self._say([""] + ["A room failed to load -- " + p for p in problems])

    def logout(self):
        self.profile, self.room, self.room_start, self.log = None, None, None, []

    def completed(self):
        return list(self.profile.get("completed", [])) if self.profile else []

    # ---- helpers ---------------------------------------------------------
    def _say(self, lines):
        for line in lines:
            self.log.append({"kind": "system", "text": line})

    def _enter_room(self, door):
        cls = room_for_door(door)
        self.room = cls()
        self.room_start = time.time()
        self.room.out = []
        self.room.describe()
        self._say(self.room.out)
        self.room.out = []

    def _back_to_lobby(self, intro=None):
        self.room, self.room_start = None, None
        if intro:
            self._say(intro)
        self._say(lobby.describe(self.completed()))

    # ---- commands --------------------------------------------------------
    def command(self, text):
        if not self.profile:
            return
        shown = "*" * len(text) if self.room and self.room.wants_hidden_input() else text
        self.log.append({"kind": "input", "text": shown})

        if self.room is None:
            lines, door = lobby.handle(text, self.completed())
            self._say(lines)
            if door:
                self._enter_room(door)
            return

        room = self.room
        room.out = []
        try:
            room.handle(text)
        except Exception:                                  # a bug in a room must not crash the app
            traceback.print_exc()
            room.out.append("(Something went wrong in this room's code. The game is still running.)")
        self._say(room.out)
        room.out = []
        if room.finished:
            self._finish_room(room)

    def _finish_room(self, room):
        seconds = int(time.time() - self.room_start) if self.room_start else 0
        scores.add_score(room.room_id, self.profile["name"], self.profile["logo"], seconds)
        self.profile = profiles.mark_completed(self.profile["name"], room.room_id) or self.profile
        self._say(["", f"Your time: {scores.fmt_time(seconds)}. Saved to the \"{room.title}\" leaderboard."])
        self._back_to_lobby(["", "You find yourself back in the lobby."])

    def leave_room(self):
        """The 'back to lobby' button: abandon the current room (no score)."""
        if self.room is not None:
            self._back_to_lobby(["", "You head back to the lobby. (Room progress is not saved.)"])

    # ---- what the page needs ----------------------------------------------
    def state(self):
        if not self.profile:
            return {"screen": "profile",
                    "profiles": profiles.load_all(),
                    "logos": profiles.available_logos()}
        in_room = self.room is not None
        if in_room:
            scene = {"kind": "room", "room_id": self.room.room_id, "loc": self.room.loc,
                     "module": f"/rooms/{self.room.folder_name}/scene.js",
                     "view": self.room.view()}
        else:
            door_list = lobby.doors(self.completed())
            for d in door_list:
                d["scores"] = (scores.top_scores(d["room_id"], 5) if d["status"] != "closed" else [])
                d["scores"] = [{"name": s["name"], "time": s["time"]} for s in d["scores"]]
            scene = {"kind": "lobby", "room_id": LOBBY, "loc": "lobby", "view": {"doors": door_list}}
        return {
            "screen": "game",
            "profile": self.profile,
            "in_room": in_room,
            "room_title": self.room.title if in_room else "Lobby",
            "clock_start": self.room_start,
            "hidden_input": bool(in_room and self.room.wants_hidden_input()),
            "log": self.log[-300:],
            "scene": scene,
        }

    def leaderboards(self):
        boards = []
        for slot in door_slots():
            rows = scores.top_scores(slot["room_id"], 10) if slot["available"] else []
            boards.append({"number": slot["number"], "title": slot["title"],
                           "available": slot["available"], "scores": rows})
        return boards
