"""The lobby: the room with four doors. Not an escape room itself -- it just
sends the player through whichever door they pick."""
from .parser import LOOK_VERBS, OPEN_VERBS, TAKE_VERBS, door_number, has, split_command
from .registry import DOOR_COUNT, door_slots

HELP = [
    "open door <1-4>   - go through a door",
    "look door <1-4>   - read a door's plaque",
    "look              - describe the lobby",
    "Or just click a door in the picture.",
]


def doors(completed):
    """Door list for the 3D lobby: status is 'open', 'done' or 'closed'."""
    result = []
    for slot in door_slots():
        status = "closed"
        if slot["available"]:
            status = "done" if slot["room_id"] in completed else "open"
        result.append(dict(slot, id=slot["room_id"], status=status))
    return result


def describe(completed):
    lines = [f"A dim, quiet lobby. {DOOR_COUNT} doors are set into the far wall, numbered 1 to {DOOR_COUNT}."]
    for d in doors(completed):
        n = d["number"]
        if d["status"] == "done":
            lines.append(f"Door {n} ({d['title']}): you've escaped this one. You can go again to beat your time.")
        elif d["status"] == "open":
            lines.append(f"Door {n} ({d['title']}) is unlocked. Warm light spills from underneath.")
        else:
            lines.append(f"Door {n} is shut tight.")
    lines.append("Try 'open door 1'.")
    return lines


def handle(raw, completed):
    """Returns (lines, room_door_number_or_None)."""
    verb, rest = split_command(raw)
    if verb is None:
        return [], None
    if verb in ("help", "h", "?"):
        return ["Things you can try:"] + ["  " + h for h in HELP], None
    if verb in LOOK_VERBS and not rest:
        return describe(completed), None

    num = door_number(rest)
    if not (has(rest, "door") or num is not None):
        return ["You're not sure how to do that."], None
    if verb in TAKE_VERBS:
        return ["You can't take that."], None
    if num is None:
        return ["Which door? Try 'open door 1'."], None
    slot = next((d for d in doors(completed) if d["number"] == num), None)
    if slot is None:
        return [f"There's no door {num}. The doors are numbered 1 to {DOOR_COUNT}."], None

    if verb in LOOK_VERBS:
        if slot["status"] == "closed":
            return [f"Door {num}: heavy, closed, and silent. Nothing about it gives way."], None
        extra = " You've already escaped it." if slot["status"] == "done" else ""
        return [f"Door {num}: a plaque reads \"{slot['title']}\". It's unlocked.{extra}"], None
    if verb not in OPEN_VERBS:
        return ["You're not sure how to do that."], None
    if slot["status"] == "closed":
        return [f"Door {num} is closed tight and doesn't budge. Whatever's behind it isn't ready yet."], None
    return [f"You push open door {num} and step through."], num
