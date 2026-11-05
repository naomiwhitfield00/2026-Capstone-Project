"""Small helpers shared by every escape room's text parser.

Import what you need in your room.py:

    from escapism_app.parser import has, LOOK_VERBS, TAKE_VERBS, OPEN_VERBS
"""

# Words ignored when reading a command ("look at the bed" -> "look bed").
FILLER = {"the", "a", "an", "at", "to", "my", "in", "into", "around", "through"}

LOOK_VERBS = {"look", "examine", "inspect", "check", "search", "l", "x", "view"}
TAKE_VERBS = {"take", "grab", "get", "pick", "collect"}
OPEN_VERBS = {"open", "turn", "unlock", "try", "push", "go", "walk", "enter", "leave", "exit"}

# "one", "first", "2nd" ... -> 1..4 (used for the lobby's doors, and handy in rooms)
DOOR_NUMBERS = {
    "1": 1, "one": 1, "first": 1, "1st": 1,
    "2": 2, "two": 2, "second": 2, "2nd": 2,
    "3": 3, "three": 3, "third": 3, "3rd": 3,
    "4": 4, "four": 4, "fourth": 4, "4th": 4,
}


def has(text, *keys):
    """True if any of `keys` appears anywhere in `text`."""
    return any(k in text for k in keys)


def door_number(text):
    """Pull a door number (1-4) out of a command, or None."""
    for word in text.split():
        if word in DOOR_NUMBERS:
            return DOOR_NUMBERS[word]
    return None


def split_command(raw):
    """'Look at the BED' -> ('look', 'bed').  Returns (None, '') for blank input."""
    words = [w for w in raw.lower().split() if w not in FILLER]
    if not words:
        return None, ""
    return words[0], " ".join(words[1:])
