# Adding an escape room

Every escape room lives in **its own folder** inside `rooms/`. Nobody edits anybody
else's files, and you never touch the lobby or the engine. The game finds your folder
by itself.

```
rooms/
  get_out_of_the_house/     <- Door 1 (Corey)
      room.py                  the game logic (Python)
      scene.js                 the 3D pictures (optional)
      assets/                  your own images/sounds/models (optional)
  your_room_name/           <- your room
      room.py
      scene.js
  _template/                <- copy this to start (ignored by the game)
```

## Steps

1. **Copy** `rooms/_template` to `rooms/<your_room_name>` (lowercase, underscores).
2. Open your new `room.py` and change the four lines at the top of the `Room` class:
   `room_id`, `title`, `author` and **`door`** (which lobby door, 1-4, is yours).
   Two rooms can't share a door number - the game will tell you if they do.
3. Write your places. For every place the player can be you write two methods:
   * `describe_<place>(self)` - what the player reads on arrival.
   * `do_<place>(self, verb, rest)` - what happens when they type something.
     For `open the box` the game gives you `verb="open"` and `rest="box"`.
4. When the player wins, call **`self.finish()`**. The app records their time on your
   door's leaderboard and sends them back to the lobby.
5. Run the game (`python run_escapism.py`) and open your door.

If your room has a mistake the game keeps running, shows a message in the text box, and
prints details in the console window.

## The pieces of a room

| What | Where | Notes |
|------|-------|-------|
| `room_id`, `title`, `author`, `door`, `start_loc` | top of `class Room` | `start_loc` is the first place, e.g. `"cell"` -> needs `describe_cell` and `do_cell` |
| `defaults = {...}` | `class Room` | everything your room remembers, with starting values. Use them as `self.box_open`. |
| `self.inv` | built in | list of item names the player carries (`self.inv.append("key")`) |
| `self.say("text")` | built in | print a line to the player |
| `self.loc = "hallway"` | built in | move the player, then call `self.describe()` |
| `self.awaiting = "code"` | built in | ask the player for typed input; their next line goes to `on_code(self, text)`. Add the name to `hidden_inputs = ("code",)` to hide what they type (passwords). |
| `before(self, verb, rest)` | optional | commands that work everywhere in your room (help, inventory). Return `True` if you handled it. |
| `view(self)` | optional | the facts your 3D scene needs. Default: all of your state. |
| `self.finish()` | built in | **the player escaped** |

Helpers you can import: `from escapism_app.parser import has, LOOK_VERBS, TAKE_VERBS, OPEN_VERBS, door_number`
(`has(rest, "box", "chest")` is true if either word appears).

Stick to Python's standard library in `room.py` (that keeps the packaged .exe working).
If you really need another module, tell Corey so the build script can include it.

## The 3D picture (`scene.js`) - optional

You don't need to know JavaScript to ship a room: without a `scene.js` the player sees the
text game and a "3D picture unavailable" message. To add pictures, copy the pattern in
`_template/scene.js` - each place gets one function (named after the place) that draws
boxes and makes them clickable:

```js
markInteractive(box, "open box");   // clicking the box types "open box"
```

`get_out_of_the_house/scene.js` has many more examples (beds, couches, doors, a claw machine...).
If a click does nothing or the wrong thing, check what command the object sends - it must be
a command your `do_<place>` understands. (Tip: give clickable doors a *specific* command like
`"open living room door"`, not just `"open door"`.)

## Testing your room without the whole game

```
python tests/test_app.py        # runs every room through the engine
```
Add your room's winning commands to a test of your own in `tests/` if you'd like it checked
automatically.
