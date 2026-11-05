"""
TEMPLATE escape room -- copy this whole folder, rename it, then edit.

    1. Copy rooms/_template  ->  rooms/my_room_name
    2. Change room_id, title, author and door below.
    3. Write your locations: a describe_<place>() and a do_<place>() for each.
    4. (Optional) edit scene.js to draw each place in 3D.
    5. Run the game and open your door in the lobby.

Folders whose names start with "_" are ignored by the game, so this template
never shows up as a real room.
"""
from escapism_app.parser import LOOK_VERBS, OPEN_VERBS, TAKE_VERBS, has
from escapism_app.room_base import BaseRoom


class Room(BaseRoom):
    room_id = "my_room"          # unique id, lowercase, no spaces (leaderboard scores use it)
    title = "My Escape Room"     # the name printed above your door in the lobby
    author = "Your Name"
    door = 2                     # which lobby door opens this room: 1, 2, 3 or 4
    start_loc = "cell"           # the place where the player starts

    # Everything your room needs to remember. "loc" (where the player is) and
    # "inv" (what they carry, a list of item names) are added for you.
    defaults = {
        "box_open": False,
    }

    # --- what the 3D scene is told (see scene.js). Default = all the state above.
    def view(self):
        v = self.to_state()
        v["has_key"] = "key" in self.inv
        return v

    # --- shown when the player arrives somewhere (and when they type "look")
    def describe_cell(self):
        self.say("A small stone cell. A wooden box sits on the floor.")
        self.say("There is a door in the far wall.")

    # --- handles typed commands while the player is in the "cell"
    #     verb = first word ("open"), rest = everything else ("box")
    def do_cell(self, verb, rest):
        if has(rest, "box") and (verb in OPEN_VERBS or verb in LOOK_VERBS):
            self.box_open = True
            if "key" in self.inv:
                self.say("The box is empty now.")
            else:
                self.say("Inside the box: a small brass key.")
            return

        if verb in TAKE_VERBS and has(rest, "key"):
            if self.box_open and "key" not in self.inv:
                self.inv.append("key")
                self.say("You take the key.")
            else:
                self.say("You don't see a key.")
            return

        if has(rest, "door") and verb in OPEN_VERBS:
            if "key" in self.inv:
                self.say("The key turns. You step out into the light.")
                self.say("*** YOU ESCAPED! ***")
                self.finish()          # <-- the player won: the app saves their time
            else:
                self.say("The door is locked.")
            return

        self.say("You're not sure how to do that.")
