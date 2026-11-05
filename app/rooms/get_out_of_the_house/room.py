"""
Door 1 -- "Get out of the house!"   (Corey's escape room)

Locations: bedroom -> hallway -> living room -> kitchen -> garage -> escape.
The hallway also branches to a locked spare bedroom, opened with a keypad code
found elsewhere in the house (the page number bookmarked in "War of the Worlds").

How a room works (full guide: rooms/README.md):
  * `defaults`      the room's own state (what's open, what's been found...)
  * describe_<loc>  prints what the player sees when they arrive somewhere
  * do_<loc>        handles a typed command (verb, rest) while in that location
  * before()        commands that work everywhere in the room (help, inventory)
  * view()          what scene.js is told, to draw the 3D picture
  * self.finish()   the player escaped -> the app records their time
"""
from escapism_app.parser import (
    LOOK_VERBS, OPEN_VERBS, TAKE_VERBS, door_number, has,
)
from escapism_app.room_base import BaseRoom

LAMP_VERBS = {"turn", "use", "switch", "light", "flip", "toggle"}
PHONE_VERBS = {"charge", "connect", "plug", "power", "press", "call", "use"}

ITEM_NAMES = {
    "keys": "set of 5 keys",
    "hanger": "metal hanger",
    "notepad": "notepad",
    "pen": "pen",
    "wrench": "wrench",
    "screwdriver": "screwdriver",
    "turtle": "stuffed turtle",
    "phone": "dead cell phone",
    "power_bank": "power bank",
}

PASSWORD = "Letsgetout123!"
SPARE_DOOR_CODE = "253"

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


class Room(BaseRoom):
    room_id = "get_out_of_the_house"
    title = "Get out of the house!"
    author = "Corey"
    door = 1
    start_loc = "bedroom"
    hidden_inputs = ("password",)   # the computer password is typed hidden

    defaults = {
        "cents": 0,
        "notes": [],
        # bedroom
        "lamp_on": False,
        "bed_made": False,
        "drawer_open": False,
        "closet_open": False,
        # hallway
        "hall_door_unlocked": False,
        "spare_door_unlocked": False,
        # spare bedroom
        "spare_bed_made": False,
        "spare_drawer_open": False,
        "spare_closet_open": False,
        "phone_charged": False,
        # living room
        "couch_searched": False,
        "recliner_searched": False,
        "page_seen": False,
        "pw_seen": False,
        "logged_in": False,
        "lr_door_unlocked": False,
        # kitchen
        "fridge_opened": False,
        "kitchen_exit_unlocked": False,
        # garage
        "claw_plugged": False,
        "claw_attempts": 0,
    }

    # ------------------------------------------------------------------
    # What the 3D scene needs to know
    # ------------------------------------------------------------------

    def view(self):
        v = self.to_state()
        for item in ITEM_NAMES:
            v["has_" + item] = item in self.inv
        return v

    # ------------------------------------------------------------------
    # Commands that work everywhere in this room
    # ------------------------------------------------------------------

    def before(self, verb, rest):
        if verb in ("help", "h", "?"):
            self.say("Things you can try:")
            for line in HELP_LINES:
                self.say("  " + line)
            return True
        if verb in ("inventory", "inv", "i"):
            self.show_inventory()
            return True
        if verb == "read" and has(rest, "notepad", "notes", "pad"):
            self.read_notepad()
            return True
        if verb == "write":
            self.write(rest)
            return True
        if has(rest, "phone") and (verb in LOOK_VERBS or verb in PHONE_VERBS):
            self._handle_phone(verb, rest)
            return True
        if verb in LOOK_VERBS and not rest:
            self.describe()
            return True
        return False

    def show_inventory(self):
        items = []
        for i in self.inv:
            if i == "phone":
                items.append("powered-on cell phone, no signal" if self.phone_charged
                              else "dead cell phone")
            else:
                items.append(ITEM_NAMES[i])
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

    def _leftover_note(self, items):
        """A gentle nudge if the player is about to leave discovered items behind."""
        if not items:
            return None
        if len(items) == 1:
            joined = items[0]
        else:
            joined = ", ".join(items[:-1]) + " or " + items[-1]
        return "You glance back — you haven't grabbed " + joined + " yet."

    def _bedroom_leftover_items(self):
        items = []
        if self.drawer_open and "keys" not in self.inv:
            items.append("the keys")
        if self.closet_open and "hanger" not in self.inv:
            items.append("the hanger")
        return items

    def _living_room_leftover_items(self):
        items = []
        if "notepad" not in self.inv:
            items.append("the notepad")
        if "pen" not in self.inv:
            items.append("the pen")
        return items

    def _spare_bedroom_leftover_items(self):
        items = []
        if self.spare_drawer_open and "phone" not in self.inv:
            items.append("the phone")
        return items

    def on_hallway_code(self, code):
        if code == SPARE_DOOR_CODE:
            self.spare_door_unlocked = True
            self.say("The keypad beeps green. Something inside the door unlocks.")
        else:
            self.say("The keypad flashes red. Wrong code.")

    def _handle_phone(self, verb, rest):
        if "phone" not in self.inv:
            self.say("You don't have a phone.")
            return
        if verb in LOOK_VERBS:
            if self.phone_charged:
                self.say('The phone is powered on, screen glowing faintly. Still: "No Service" '
                          "in the corner.")
            else:
                self.say("A dead cell phone. It needs power.")
            return
        if self.phone_charged:
            self.say("The phone is already on. Still no signal.")
            return
        if "power_bank" not in self.inv:
            self.say("You don't have anything to charge it with yet.")
            return
        self.phone_charged = True
        self.say("You connect the power bank to the phone. The screen flickers, then lights up.")
        self.say('No signal. "No Service" sits at the top of the screen. No calling out from here.')

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
            self.say("Straight ahead, the door to the living room stands unlocked.")
        else:
            self.say("Straight ahead is a locked door leading to the living room.")
        self.say("Two more doors line each side of the hallway.")
        if self.spare_door_unlocked:
            self.say("One of them stands open — the one with the keypad.")
        else:
            self.say("One has a small keypad beside it, locked. The other three don't "
                      "look like they go anywhere yet.")
        self.say("Behind you is the bedroom.")

    def describe_spare_bedroom(self):
        self.say("A second bedroom, the air gone stale and dusty.")
        self.say("The bed is neatly made." if self.spare_bed_made else
                 "The bed sits untouched, sheets twisted and gray with dust.")
        self.say("A night stand sits beside it, and a closet stands against the far wall.")
        self.say("The hallway is behind you.")

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
            note = self._leftover_note(self._bedroom_leftover_items())
            if note:
                self.say(note)
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
        if has(rest, "keypad", "code"):
            if verb in LOOK_VERBS:
                if self.spare_door_unlocked:
                    self.say("A door stands open — the keypad lock hangs disengaged.")
                else:
                    self.say("A locked door with a small keypad beside it. It wants a 3-digit code.")
                return
            if self.spare_door_unlocked:
                self.loc = "spare_bedroom"
                self.say("You open the door and step through.")
                self.describe()
                return
            self.say("Enter the 3-digit code:")
            self.awaiting = "hallway_code"
            return

        if verb in ("go", "walk", "enter", "leave", "exit") and has(rest, "bedroom", "back"):
            self.loc = "bedroom"
            self.say("You head back into the bedroom.")
            self.describe()
            return

        words = rest.split()
        side_door = (
            door_number(rest) is not None
            or any(w in ("stuck", "left", "right", "side", "sides", "other", "another", "next")
                   for w in words)
        )
        if side_door and "living" not in words:
            if verb in TAKE_VERBS:
                self.say("You can't take that.")
            elif verb in LOOK_VERBS:
                self.say("Just another door, like the others along the side of the hallway. "
                         "No keyhole, no handle that moves — this one isn't going anywhere.")
            else:
                self.say("You push and pull, but this door doesn't budge. Whatever's back "
                         "there, it's not opening from here.")
            return

        # Only the door straight ahead leads to the living room, and only when
        # the player says so (or talks about keys / locks).
        if has(rest, "living", "straight", "end", "far") or any(w in ("key", "keys", "lock", "locked", "keyhole") for w in words):
            if verb in TAKE_VERBS:
                self.say("You can't take that.")
                return
            if verb in LOOK_VERBS:
                if self.hall_door_unlocked:
                    self.say("The door to the living room, unlocked and ready to open.")
                else:
                    self.say("A plain wooden door at the end of the hallway, with a brass keyhole.")
                return
            self.try_living_room_door()
            return

        if has(rest, "door", "room"):
            self.say("Which door? The locked one straight ahead leads to the living room "
                     "(\"open living room door\"). The doors along the sides won't open — "
                     "except the one with the keypad.")
            return

        self.say("You're not sure how to do that.")

    def try_living_room_door(self):
        if self.hall_door_unlocked:
            self.say("You open the unlocked door and walk into the living room.")
        elif "keys" in self.inv:
            self.say("You try the keys one by one... one of them turns with a click!")
            self.hall_door_unlocked = True
        else:
            self.say("The door is locked. You need a key.")
            return
        self.loc = "living_room"
        self.describe()

    # ------------------------------------------------------------------
    # Spare bedroom (off the hallway, behind the keypad door)
    # ------------------------------------------------------------------

    def do_spare_bedroom(self, verb, rest):
        if verb == "make" and has(rest, "bed"):
            if self.spare_bed_made:
                self.say("The bed is already made.")
            else:
                self.spare_bed_made = True
                self.say("You straighten the sheets, same as the other bedroom. Nothing hidden "
                          "underneath.")
            return
        if verb in LOOK_VERBS and has(rest, "bed", "pillow", "sheet"):
            self.say("A neatly made bed." if self.spare_bed_made else
                      "The sheets are twisted and gray with dust, untouched for a long time.")
            return

        if has(rest, "closet") and (verb in LOOK_VERBS or verb in OPEN_VERBS):
            self.spare_closet_open = True
            self.say("You open the closet. Empty hangers, a little dust. Nothing useful in here.")
            return

        if has(rest, "drawer", "nightstand", "stand", "table") and (
                verb in LOOK_VERBS or verb in OPEN_VERBS):
            self.spare_drawer_open = True
            if "phone" in self.inv:
                self.say("The drawer is empty now.")
            else:
                self.say("You slide open the drawer and find a dead cell phone inside.")
            return

        if verb in TAKE_VERBS:
            if has(rest, "phone"):
                if "phone" in self.inv:
                    self.say("You already have the phone.")
                elif self.spare_drawer_open:
                    self.inv.append("phone")
                    self.say("You take the dead cell phone.")
                else:
                    self.say("You don't see a phone. Maybe check the nightstand.")
            else:
                self.say("You can't take that.")
            return

        if verb in ("go", "walk", "leave", "exit") and has(rest, "hall", "back"):
            self.loc = "hallway"
            self.say("You step back into the hallway.")
            note = self._leftover_note(self._spare_bedroom_leftover_items())
            if note:
                self.say(note)
            self.describe()
            return
        if verb in LOOK_VERBS and has(rest, "door"):
            self.say("A plain door leading back to the hallway.")
            return

        self.say("You're not sure how to do that.")

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
                self.say("You open the door and step through.")
            else:
                if "keys" not in self.inv:
                    self.say("The door is locked. You'll need a key.")
                    return
                self.lr_door_unlocked = True
                self.say("You try the keys, and one of them turns. The door unlocks.")
            note = self._leftover_note(self._living_room_leftover_items())
            if note:
                self.say(note)
            self.loc = "kitchen"
            self.describe()
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

    def on_password(self, guess):
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

        if has(rest, "power bank", "powerbank"):
            self.take_item("power_bank", verb in TAKE_VERBS, "a power bank", "counter")
            return

        if has(rest, "counter"):
            self.say("A kitchen counter." + ("" if "power_bank" in self.inv else
                      " A power bank sits on it, the only thing not covered in dust."))
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
        self.finish()
