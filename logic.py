"""
Escapism — game engine.

Rooms: bedroom -> hallway -> living room -> kitchen -> garage -> escape.

Mirrors the original console game's approach: instead of printing to the
terminal and calling input(), it collects output lines in self.out and
supports state being loaded from / saved to a plain dict (kept in the
Django session between requests).
"""

import random

FILLER = {"the", "a", "an", "at", "to", "my", "in", "into", "around", "through"}
LOOK_VERBS = {"look", "examine", "inspect", "check", "search", "l", "x", "view"}
TAKE_VERBS = {"take", "grab", "get", "pick", "collect"}
OPEN_VERBS = {"open", "turn", "unlock", "try", "push", "go", "walk", "enter", "leave", "exit"}
LAMP_VERBS = {"turn", "use", "switch", "light", "flip", "toggle"}

NUMBER_WORDS = {
    "1": 1, "one": 1, "first": 1, "1st": 1,
    "2": 2, "two": 2, "second": 2, "2nd": 2,
    "3": 3, "three": 3, "third": 3, "3rd": 3,
    "4": 4, "four": 4, "fourth": 4, "4th": 4,
    "5": 5, "five": 5, "fifth": 5, "5th": 5,
}

ITEM_NAMES = {
    "keys": "set of 5 keys",
    "hanger": "metal hanger",
    "notepad": "notepad",
    "pen": "pen",
    "wrench": "wrench",
    "screwdriver": "screwdriver",
    "turtle": "stuffed turtle",
}

PASSWORD = "Letsgetout123!"

HELP_LINES = [
    "look                     - describe where you are",
    "look <thing>             - examine something (look bed, look bookshelf...)",
    "open <thing>             - open a door, drawer, closet...",
    "take <item>              - pick something up",
    "use <item> on <thing>    - use something you're carrying",
    "go <place>               - move around (go hallway, go back, go kitchen...)",
    "write <thing>            - write something on your notepad (needs pen + notepad)",
    "read notepad             - read your notes",
    "inventory                - see what you're carrying",
    "help                     - show this list",
]

STATE_KEYS = [
    "loc", "inv", "cents", "notes", "lamp_on", "bed_made", "drawer_open",
    "closet_open", "good_door", "hall_door_unlocked", "couch_searched",
    "recliner_searched", "page_seen", "pw_seen", "logged_in", "won",
    "awaiting", "lr_door_unlocked", "fridge_opened", "kitchen_exit_unlocked",
    "claw_plugged", "claw_attempts",
]


def has(text, *keys):
    return any(k in text for k in keys)


def door_number(rest):
    for word in rest.split():
        if word in NUMBER_WORDS:
            return NUMBER_WORDS[word]
    return None


def new_state():
    return {
        "loc": "bedroom",
        "inv": [],
        "cents": 0,
        "notes": [],
        "lamp_on": False,
        "bed_made": False,
        "drawer_open": False,
        "closet_open": False,
        "good_door": random.randint(1, 5),
        "hall_door_unlocked": False,
        "couch_searched": False,
        "recliner_searched": False,
        "page_seen": False,
        "pw_seen": False,
        "logged_in": False,
        "won": False,
        "awaiting": None,  # None | "password"
        "lr_door_unlocked": False,
        "fridge_opened": False,
        "kitchen_exit_unlocked": False,
        "claw_plugged": False,
        "claw_attempts": 0,
    }


class Game:
    def __init__(self, state):
        for key in STATE_KEYS:
            setattr(self, key, state.get(key, new_state()[key]))
        self.out = []

    def to_state(self):
        return {key: getattr(self, key) for key in STATE_KEYS}

    def say(self, text=""):
        self.out.append(text)

    # ------------------------------------------------------------------
    # Top-level input handling
    # ------------------------------------------------------------------

    def handle(self, raw):
        """Process one line of player input. Fills self.out with response lines."""
        if self.awaiting == "password":
            self.awaiting = None
            self._check_password(raw.strip())
            return

        words = [w for w in raw.lower().split() if w not in FILLER]
        if not words:
            return
        verb, rest = words[0], " ".join(words[1:])

        if verb in ("help", "h", "?"):
            self.say("Things you can try:")
            for line in HELP_LINES:
                self.say("  " + line)
            return
        if verb in ("inventory", "inv", "i"):
            self.show_inventory()
            return
        if verb == "read" and has(rest, "notepad", "notes", "pad"):
            self.read_notepad()
            return
        if verb == "write":
            self.write(rest)
            return
        if has(rest, "code") and verb not in ("write",):
            self.say("You don't see anywhere to use a code right now.")
            return
        if verb in LOOK_VERBS and not rest:
            self.describe()
            return

        getattr(self, f"do_{self.loc}")(verb, rest)

    def show_inventory(self):
        items = [ITEM_NAMES[i] for i in self.inv]
        if self.cents:
            items.append(f"${self.cents / 100:.2f} in loose change")
        self.say("You are carrying: " + (", ".join(items) if items else "nothing") + ".")

    def read_notepad(self):
        if "notepad" not in self.inv:
            self.say("You don't have a notepad.")
        elif not self.notes:
            self.say("The notepad is blank.")
        else:
            self.say("Your notepad says:")
            for note in self.notes:
                self.say("  - " + note)

    def write(self, rest):
        if "notepad" not in self.inv or "pen" not in self.inv:
            self.say("You need both a notepad and a pen to write anything down.")
            return
        if has(rest, "password", "pass"):
            if not self.pw_seen:
                self.say("You don't have a password to write down yet.")
                return
            note = f"Password: {PASSWORD}"
        elif has(rest, "page", "253", "code", "number", "bookmark"):
            if not self.page_seen:
                self.say("You haven't found a page number to write down yet.")
                return
            note = "War of the Worlds bookmark: page 253"
        else:
            self.say("Write what? Try 'write password' or 'write page number'.")
            return
        if note in self.notes:
            self.say("You've already written that down.")
        else:
            self.notes.append(note)
            self.say("You jot down: " + note)

    def take_item(self, item, taking, label, surface="desk"):
        if item in self.inv:
            self.say(f"You already have {label}.")
        elif taking:
            self.inv.append(item)
            self.say(f"You pick up {label}.")
        else:
            self.say(f"{label.capitalize()} sits on the {surface}. You could take it.")

    # ------------------------------------------------------------------
    # Room descriptions
    # ------------------------------------------------------------------

    def describe(self):
        getattr(self, f"describe_{self.loc}")()

    def describe_bedroom(self):
        if self.lamp_on:
            self.say("A warm glow from the lamp lights up a small bedroom.")
        else:
            self.say("You are in a dimly lit bedroom.")
        self.say("The bed is neatly made." if self.bed_made else
                 "The bed looks like it has been slept in.")
        self.say("A night stand with a lamp sits beside it.")
        if self.closet_open:
            self.say("The closet door is open, showing a row of ordinary clothes.")
        else:
            self.say("A closet door is barely open.")
        self.say("The main door out of the room is across from the bed.")

    def describe_hallway(self):
        self.say("A long hallway stretches out in front of you. The lights flicker, "
                  "throwing shadows up and down the walls.")
        if self.hall_door_unlocked:
            self.say(f"There are five doors. Door {self.good_door} is unlocked and stands ready to open.")
        else:
            self.say("There are five doors along the hall, numbered 1 to 5.")
        self.say("Behind you is the bedroom.")

    def describe_living_room(self):
        self.say("A living room. A bookshelf stands in the corner, and a couch and recliner "
                  "face an old CRT TV, its screen hissing with static.")
        self.say("On the far side of the room is a desk with a monitor, keyboard, mouse, "
                  "mousepad, and a notepad with a pen.")
        if self.lr_door_unlocked:
            self.say("There are two doors: a front door boarded up tight, and the door you "
                      "unlocked leading further into the house.")
        else:
            self.say("There are two doors: a front door boarded up tight, and another door, closed.")
        self.say("The hallway is behind you.")

    def describe_kitchen(self):
        self.say("A kitchen. A fridge, stove, cabinets, and a sink line the walls, and a "
                  "small round dining table with four chairs sits in the middle.")
        if self.kitchen_exit_unlocked:
            self.say("Behind the table, an unlocked door leads onward.")
        else:
            self.say("Behind the table and chairs is a locked door.")
        self.say("The living room is behind you.")

    def describe_garage(self):
        self.say("A garage. An old car sits with its hood up, parts scattered across the "
                  "floor and a workbench along one wall.")
        if self.claw_plugged:
            self.say("A claw machine in the corner hums and flashes, freshly plugged in.")
        else:
            self.say("A dark, unplugged claw machine sits in the corner, full of prizes.")
        self.say("A large garage door is shut tight, and there's one more door besides.")
        self.say("The kitchen is behind you.")

    # ------------------------------------------------------------------
    # Bedroom
    # ------------------------------------------------------------------

    def do_bedroom(self, verb, rest):
        if verb in LAMP_VERBS and has(rest, "lamp", "light"):
            self.lamp_on = not self.lamp_on
            self.say("The lamp clicks on. Warm light fills the room." if self.lamp_on
                      else "The lamp clicks off. The room falls dim again.")
            return
        if verb in LOOK_VERBS and has(rest, "lamp"):
            self.say("A simple bedside lamp. It's currently " + ("on." if self.lamp_on else "off."))
            return

        if verb == "make" and has(rest, "bed"):
            if self.bed_made:
                self.say("The bed is already made.")
            else:
                self.bed_made = True
                self.say("You straighten the sheets and fluff the pillow. Nothing hidden "
                          "in there, but at least it looks tidy.")
            return
        if verb in LOOK_VERBS and has(rest, "bed", "pillow", "sheet"):
            self.say("A neatly made bed." if self.bed_made else
                      "The sheets are rumpled and the pillow is dented. Someone slept here "
                      "recently. Maybe you? You could try to 'make bed'.")
            return

        if has(rest, "closet") and (verb in LOOK_VERBS or verb in OPEN_VERBS):
            if not self.closet_open:
                self.closet_open = True
                self.say("You pull the closet door open. Just ordinary clothes on a rail... "
                          "and a metal hanger dangling at the end.")
            elif "hanger" in self.inv:
                self.say("Just ordinary clothes.")
            else:
                self.say("Just ordinary clothes, and a metal hanger dangling at the end.")
            return

        if has(rest, "drawer", "nightstand", "stand", "table") and (
                verb in LOOK_VERBS or verb in OPEN_VERBS):
            self.drawer_open = True
            if "keys" in self.inv:
                self.say("The drawer is empty now.")
            else:
                self.say("You slide open the drawer and find a set of keys. About five of them on a ring.")
            return

        if verb in TAKE_VERBS:
            if has(rest, "key"):
                if "keys" in self.inv:
                    self.say("You already have the keys.")
                elif self.drawer_open:
                    self.inv.append("keys")
                    self.say("You take the ring of keys. Five of them, all different.")
                else:
                    self.say("You don't see any keys. Maybe check the night stand.")
            elif has(rest, "hanger"):
                if "hanger" in self.inv:
                    self.say("You already have the hanger.")
                elif self.closet_open:
                    self.inv.append("hanger")
                    self.say("You unhook the metal hanger from the closet rail.")
                else:
                    self.say("You don't see a hanger. The closet door is barely open, though.")
            else:
                self.say("You can't take that.")
            return

        if verb in ("leave", "exit") or (
                verb in OPEN_VERBS and has(rest, "knob", "door", "out", "hall")):
            self.say("You turn the knob and step out of the bedroom.")
            self.loc = "hallway"
            self.describe()
            return
        if verb in LOOK_VERBS and has(rest, "door"):
            self.say("A plain wooden door. The knob turns freely.")
            return

        self.say("You're not sure how to do that.")

    # ------------------------------------------------------------------
    # Hallway
    # ------------------------------------------------------------------

    def do_hallway(self, verb, rest):
        if verb in ("go", "walk", "enter", "leave", "exit") and has(rest, "bedroom", "back"):
            self.loc = "bedroom"
            self.say("You head back into the bedroom.")
            self.describe()
            return

        num = door_number(rest)

        if verb in LOOK_VERBS and has(rest, "door"):
            if num:
                self.say(f"Door {num}: plain wood with a brass keyhole.")
            else:
                self.say("Five doors, all similar: plain wood with brass keyholes.")
            return

        if has(rest, "door", "living", "room") or num:
            if verb in TAKE_VERBS:
                self.say("You can't take that.")
                return
            if num is None:
                if self.hall_door_unlocked:
                    num = self.good_door
                else:
                    self.say("Which door? Try 'open door 1' through 'open door 5'.")
                    return
            self.try_door(num)
            return

        self.say("You're not sure how to do that.")

    def try_door(self, num):
        if num == self.good_door:
            if self.hall_door_unlocked:
                self.say("You open the unlocked door and walk in.")
            elif "keys" in self.inv:
                self.say(f"You try the keys one by one on door {num}... the fourth one turns with a click!")
                self.hall_door_unlocked = True
            else:
                self.say(f"Door {num} is locked. You need a key.")
                return
            self.loc = "living_room"
            self.describe()
        else:
            if "keys" in self.inv:
                self.say(f"You try every key on door {num}. None of them fit, and the door "
                          "doesn't budge. It feels like there's solid wall behind it.")
            else:
                self.say(f"Door {num} is locked and doesn't budge.")

    # ------------------------------------------------------------------
    # Living room
    # ------------------------------------------------------------------

    def do_living_room(self, verb, rest):
        looking = verb in LOOK_VERBS
        taking = verb in TAKE_VERBS

        if has(rest, "tv", "television", "static"):
            self.say("An old CRT television, hissing with static. Nothing but snow on the screen.")
            return

        if has(rest, "front"):
            if verb == "use" and has(rest, "hanger"):
                if "hanger" not in self.inv:
                    self.say("You don't have a hanger.")
                else:
                    self.say("You bend the hanger and hook it around the edge of a board, "
                              "prying it back just enough to peek through the gap.")
                    self.say("Darkness outside. Something shifts out there. Something that "
                              "doesn't want to be seen. You let the board slap back into place.")
            else:
                self.say("The front door is boarded up tightly with planks and nails. "
                          "Are we keeping something from coming in?")
            return

        if has(rest, "door") and not has(rest, "front"):
            if looking:
                self.say("A plain door, unlocked." if self.lr_door_unlocked else
                          "A plain door. It's locked.")
                return
            if self.lr_door_unlocked:
                self.loc = "kitchen"
                self.say("You open the door and step through.")
                self.describe()
                return
            if "keys" in self.inv:
                self.lr_door_unlocked = True
                self.say("You try the keys, and one of them turns. The door unlocks.")
                self.loc = "kitchen"
                self.describe()
            else:
                self.say("The door is locked. You'll need a key.")
            return

        if verb in ("go", "walk", "leave", "exit") and has(rest, "hall", "back", "bedroom"):
            self.loc = "hallway"
            self.say("You step back into the flickering hallway.")
            self.describe()
            return

        if has(rest, "couch", "sofa", "recliner", "chair", "cushion"):
            if has(rest, "recliner", "chair"):
                self.search_seat("recliner")
            elif has(rest, "couch", "sofa"):
                self.search_seat("couch")
            else:
                self.say("Which one, the couch or the recliner?")
            return

        is_shelf = has(rest, "shelf", "books")
        is_book = has(rest, "war", "worlds", "novel") or (has(rest, "book") and not is_shelf)
        if is_book:
            self.inspect_book()
            return
        if is_shelf:
            self.say("Numerous books line the shelf, but one really stands out: "
                      "'War of the Worlds'.")
            return

        if has(rest, "keyboard"):
            if has(rest, "under", "beneath"):
                self.pw_seen = True
                self.say(f'You lift the keyboard. A sticky note reads: "{PASSWORD}"')
                self.say("That looks like a password. Maybe write it down.")
            else:
                self.say("A regular keyboard. Something might be hidden under it.")
            return
        if has(rest, "monitor", "computer", "login", "log") or verb in ("login", "log", "type"):
            self.computer(looking)
            return
        if has(rest, "mousepad"):
            self.say("A plain mousepad. Nothing under it.")
            return
        if has(rest, "mouse"):
            self.say("An ordinary computer mouse.")
            return
        if has(rest, "notepad", "note", "pad"):
            self.take_item("notepad", taking, "a notepad", "desk")
            return
        if has(rest, "pen"):
            self.take_item("pen", taking, "a pen", "desk")
            return
        if has(rest, "desk"):
            self.say("On the desk: a monitor, keyboard, mouse, mousepad, and a notepad with a pen.")
            return

        self.say("You're not sure how to do that.")

    def search_seat(self, seat):
        if seat == "couch":
            if self.couch_searched:
                self.say("You've already searched the couch cushions.")
            else:
                self.couch_searched = True
                self.cents += 75
                self.say("You dig between the couch cushions and pull out 75 cents.")
        else:
            if self.recliner_searched:
                self.say("You've already searched the recliner.")
            else:
                self.recliner_searched = True
                self.cents += 125
                self.say("You feel around the recliner cushions and pull out $1.25.")

    def inspect_book(self):
        self.page_seen = True
        self.say("You pull 'War of the Worlds' off the shelf. A bookmark sticks out of it, "
                  "marking page 253.")
        self.say("Worth writing down.")

    def computer(self, just_looking):
        if self.logged_in:
            self.say("The screen shows an open text file called READ_ME.txt:")
            self.show_readme()
            return
        self.say("The monitor glows with a login screen. It's asking for a password.")
        if just_looking:
            return
        self.say("Password:")
        self.awaiting = "password"

    def show_readme(self):
        self.say('  "If you\'re reading this, you woke up again."')
        self.say('  "There\'s a way out through the back of the house."')
        self.say('  "Don\'t waste time on the front door."')

    def _check_password(self, guess):
        if guess == PASSWORD:
            self.logged_in = True
            self.say("Access granted. A single file sits on the desktop: READ_ME.txt")
            self.show_readme()
        else:
            self.say("Access denied.")

    # ------------------------------------------------------------------
    # Kitchen
    # ------------------------------------------------------------------

    def do_kitchen(self, verb, rest):
        looking = verb in LOOK_VERBS

        if verb in ("go", "walk", "leave", "exit") and has(rest, "living", "back"):
            self.loc = "living_room"
            self.say("You step back into the living room.")
            self.describe()
            return

        if has(rest, "fridge", "refrigerator"):
            self.fridge_opened = True
            self.say("You open the fridge. Nothing salvageable in there — just spoiled "
                      "leftovers and a smell you'd rather forget.")
            return

        if has(rest, "stove", "oven"):
            if has(rest, "clock"):
                self.say("The stove's clock blinks 12:00, over and over. The power must "
                          "have gone out at some point.")
            else:
                self.say("An old stove. Its clock blinks 12:00. Inside the oven is an old "
                          "bake sheet, nothing else.")
            return

        if has(rest, "sink", "faucet"):
            self.say("The sink is empty. You try the faucet, but no water comes out.")
            return

        if has(rest, "cabinet"):
            self.say("Empty cabinets, save for a few chipped plates.")
            return

        if has(rest, "table", "chair"):
            self.say("A small round dining table with four chairs.")
            return

        if has(rest, "door"):
            if looking:
                self.say("An unlocked door behind the table and chairs." if self.kitchen_exit_unlocked
                          else "A locked door behind the table and chairs.")
                return
            if self.kitchen_exit_unlocked:
                self.loc = "garage"
                self.say("You open the door and step through.")
                self.describe()
                return
            if "keys" in self.inv:
                self.kitchen_exit_unlocked = True
                self.say("One of the keys fits. The door unlocks.")
                self.loc = "garage"
                self.describe()
            else:
                self.say("The door is locked. You'll need a key.")
            return

        self.say("You're not sure how to do that.")

    # ------------------------------------------------------------------
    # Garage
    # ------------------------------------------------------------------

    def do_garage(self, verb, rest):
        looking = verb in LOOK_VERBS
        taking = verb in TAKE_VERBS

        if verb in ("go", "walk", "leave", "exit") and has(rest, "kitchen", "back"):
            self.loc = "kitchen"
            self.say("You step back into the kitchen.")
            self.describe()
            return

        if has(rest, "car"):
            self.say("An old car, hood up, parts scattered across the floor and workbench. "
                      "Whatever's missing, it isn't going anywhere.")
            return

        if has(rest, "garage") and has(rest, "door"):
            self.say("The garage door is locked down tight. It isn't budging, no matter what you try.")
            return

        if has(rest, "counter", "workbench", "bench"):
            self.say("Tools scattered across the workbench: a wrench and a screwdriver.")
            return

        if has(rest, "wrench"):
            self.take_item("wrench", taking, "a wrench", "workbench")
            return

        if has(rest, "screwdriver"):
            self.take_item("screwdriver", taking, "a screwdriver", "workbench")
            return

        if has(rest, "turtle"):
            if "turtle" in self.inv:
                self.say("Your stuffed turtle. Soft, a little dusty, clearly a prize.")
            else:
                self.say("You don't have a turtle. Maybe win one from the claw machine?")
            return

        if has(rest, "claw", "machine", "arcade"):
            if verb == "plug" or has(rest, "plug", "cord"):
                if self.claw_plugged:
                    self.say("It's already plugged in and running.")
                else:
                    self.claw_plugged = True
                    self.say("You find the cord and plug it into a wall outlet. The claw "
                              "machine rattles to life with a loud whir, lights flashing.")
                return
            if verb in ("play", "insert", "use", "try"):
                self.play_claw()
                return
            self.say("A claw machine, full of prizes." + ("" if self.claw_plugged else
                      " It's dark — looks unplugged."))
            return

        if has(rest, "hanger") and not has(rest, "door"):
            if "hanger" in self.inv:
                self.say("Use the hanger on what? Maybe the door.")
            else:
                self.say("You don't have a hanger.")
            return

        if has(rest, "door") and not has(rest, "garage"):
            if verb == "use" and has(rest, "hanger"):
                self.use_hanger_on_exit()
                return
            if looking:
                self.say("A plain door. It's locked.")
                return
            if "keys" in self.inv:
                self.say("You try every key on the ring. None of them fit. This lock looks different.")
                return
            self.say("The door is locked.")
            return

        self.say("You're not sure how to do that.")

    def play_claw(self):
        if not self.claw_plugged:
            self.say("The claw machine is dark. It needs to be plugged in first.")
            return
        if "turtle" in self.inv:
            self.say("You already won your prize. No sense feeding it more coins.")
            return
        if self.cents < 100:
            self.say("You don't have enough coins. You need a dollar's worth to play.")
            return
        self.cents -= 100
        self.claw_attempts += 1
        if self.claw_attempts == 1:
            self.say("You feed in a dollar's worth of coins. The claw drops, grips, and "
                      "drops the prize again halfway up. You lose.")
        else:
            self.inv.append("turtle")
            self.say("You feed in another dollar's worth of coins. This time the claw holds "
                      "on. A stuffed turtle drops into the tray. You grab it.")

    def use_hanger_on_exit(self):
        if "hanger" not in self.inv:
            self.say("You don't have a hanger.")
            return
        self.inv.remove("hanger")
        self.say("You work the bent hanger into the lock and wiggle it back and forth. "
                  "Something inside finally gives.")
        self.say("The door swings open. You leave the hanger hanging from the lock and step through.")
        self.say("")
        self.say("*** YOU ESCAPED! ***")
        self.won = True
