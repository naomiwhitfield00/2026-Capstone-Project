"""The base class every escape room builds on.

A room author only writes `rooms/<your_room>/room.py` containing:

    class Room(BaseRoom):
        room_id   = "my_room"       # unique, no spaces
        title     = "My Room"       # shown above the door in the lobby
        author    = "Your name"
        door      = 2               # which lobby door (1-4) opens your room
        start_loc = "entry"         # where the player begins
        defaults  = {"lamp_on": False}   # your room's own state, with starting values

        def describe_entry(self): ...      # one describe_<location> per location
        def do_entry(self, verb, rest): ...# one do_<location> per location

See rooms/README.md for the full walk-through and rooms/_template/ for a
copy-and-edit starting point.
"""
import copy

from .parser import split_command


class BaseRoom:
    # ---- fill these in on your Room class -------------------------------
    room_id = ""
    title = ""
    author = ""
    door = 0
    start_loc = ""
    defaults = {}
    # Names of "awaiting" prompts whose typed text should be hidden (passwords).
    hidden_inputs = ()

    # ---- state ----------------------------------------------------------
    def __init__(self, state=None):
        values = {"loc": self.start_loc, "inv": [], "awaiting": None}
        values.update(copy.deepcopy(self.defaults))
        if state:
            values.update(copy.deepcopy(state))
        self._keys = list(values)
        for key, value in values.items():
            setattr(self, key, value)
        self.out = []          # lines the room wants to show the player
        self.finished = False  # set True (via self.finish()) when the player escapes

    def to_state(self):
        """Everything worth saving, as a plain dict."""
        return {key: getattr(self, key) for key in self._keys}

    def view(self):
        """What the 3D scene (scene.js) is allowed to know. Override to add
        extra values (e.g. 'has_keys'); by default it is the whole state."""
        return self.to_state()

    # ---- output ---------------------------------------------------------
    def say(self, text=""):
        self.out.append(text)

    def describe(self):
        getattr(self, f"describe_{self.loc}")()

    def finish(self):
        """Call when the player has escaped. The app saves their time and
        takes them back to the lobby."""
        self.finished = True

    # ---- input ----------------------------------------------------------
    def wants_hidden_input(self):
        return self.awaiting in self.hidden_inputs

    def before(self, verb, rest):
        """Optional hook: commands that work everywhere in your room (help,
        inventory...). Return True if you handled the command."""
        return False

    def handle(self, raw):
        """Process one line of player input. Responses end up in self.out."""
        if self.awaiting:
            name, self.awaiting = self.awaiting, None
            getattr(self, f"on_{name}")(raw.strip())
            return
        verb, rest = split_command(raw)
        if verb is None:
            return
        if self.before(verb, rest):
            return
        handler = getattr(self, f"do_{self.loc}", None)
        if handler is None:
            self.say("You're not sure how to do that.")
            return
        handler(verb, rest)
