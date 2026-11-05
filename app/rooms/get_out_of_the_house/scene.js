// 3D scenes for "Get out of the house!" -- one function per location.
//
// Each function is called by the app with:
//   api  = { THREE, createScene, container, sendCommand }
//   view = the dictionary returned by view() in room.py (what the scene needs
//          to know: which things are open, what the player is carrying, ...)
// Clicking an object runs sendCommand("some command") -- the same as typing it.
// See rooms/README.md for the helpers (wall, markInteractive, addHitTarget).

export const scenes = {
  bedroom(api, view) {
    const { THREE, createScene, container, sendCommand } = api;

    const closetOpen = view.closet_open;
    const bedMade = view.bed_made;
    const drawerOpen = view.drawer_open;
    const lampOn = view.lamp_on;
    const hasKeys = view.has_keys;
    const hasHanger = view.has_hanger;

    const { scene, wall, markInteractive, addHitTarget, render, setupInteraction } =
      createScene(container, { roomWidth: 12, roomDepth: 8 });

    wall(12, 0.8, 0.2, 0, 0.4, -4);   // back
    wall(0.2, 0.8, 8, -6, 0.4, 0);    // left
    wall(0.2, 0.8, 8, 6, 0.4, 0);     // right
    wall(12, 0.8, 0.2, 0, 0.4, 4);    // front

    // --- bed ---
    const bedFrame = new THREE.Mesh(
      new THREE.BoxGeometry(3, 0.5, 1.8),
      new THREE.MeshStandardMaterial({ color: 0xa9793a, roughness: 0.8 })
    );
    bedFrame.position.set(-1.2, 0.25, -0.3);
    scene.add(bedFrame);
    const pillow = new THREE.Mesh(
      new THREE.BoxGeometry(0.7, 0.15, 1.4),
      new THREE.MeshStandardMaterial({ color: 0xf0a94a, roughness: 0.6 })
    );
    pillow.position.set(-2.2, 0.55, -0.3);
    scene.add(pillow);
    markInteractive(bedFrame, bedMade ? "look bed" : "make bed");
    markInteractive(pillow, bedMade ? "look bed" : "make bed");

    // --- nightstand + lamp ---
    const stand = new THREE.Mesh(
      new THREE.BoxGeometry(0.9, 0.6, 0.9),
      new THREE.MeshStandardMaterial({ color: 0x6b4f2c, roughness: 0.8 })
    );
    stand.position.set(1, 0.3, -1);
    scene.add(stand);
    markInteractive(stand, "look nightstand");

    if (drawerOpen && !hasKeys) {
      const keys = new THREE.Mesh(
        new THREE.TorusGeometry(0.12, 0.03, 8, 16),
        new THREE.MeshStandardMaterial({ color: 0xffd98a, metalness: 0.6, roughness: 0.3 })
      );
      keys.rotation.x = Math.PI / 2;
      keys.position.set(1, 0.65, -1);
      scene.add(keys);
      addHitTarget(1, 0.65, -1, 0.4, "take keys");
    }

    const lampBase = new THREE.Mesh(
      new THREE.CylinderGeometry(0.12, 0.15, 0.1, 12),
      new THREE.MeshStandardMaterial({ color: 0xf0a94a, roughness: 0.6 })
    );
    lampBase.position.set(1.3, 0.65, -1.2);
    scene.add(lampBase);
    const lampShade = new THREE.Mesh(
      new THREE.ConeGeometry(0.22, 0.3, 12, 1, true),
      new THREE.MeshStandardMaterial({
        color: lampOn ? 0xffd98a : 0xf0a94a,
        emissive: lampOn ? 0xffd98a : 0x000000,
        emissiveIntensity: lampOn ? 0.8 : 0,
        roughness: 0.4,
      })
    );
    lampShade.position.set(1.3, 0.95, -1.2);
    scene.add(lampShade);
    addHitTarget(1.3, 0.8, -1.2, 0.35, "turn on lamp");

    if (lampOn) {
      const glow = new THREE.PointLight(0xffd98a, 1.2, 3);
      glow.position.set(1.3, 1, -1.2);
      scene.add(glow);
    }

    // --- closet (left wall) ---
    const closet = new THREE.Mesh(
      new THREE.BoxGeometry(1.8, closetOpen ? 0.15 : 1.0, 2.2),
      new THREE.MeshStandardMaterial({ color: 0x6b4f2c, roughness: 0.9 })
    );
    closet.position.set(-4.6, closetOpen ? 0.08 : 0.5, -1.2);
    scene.add(closet);
    markInteractive(closet, "open closet");

    if (closetOpen && !hasHanger) {
      const hanger = new THREE.Mesh(
        new THREE.TorusGeometry(0.15, 0.025, 8, 16, Math.PI * 1.5),
        new THREE.MeshStandardMaterial({ color: 0xffd98a, metalness: 0.5, roughness: 0.3 })
      );
      hanger.position.set(-4.6, 0.3, -1.2);
      hanger.rotation.x = Math.PI / 2;
      scene.add(hanger);
      addHitTarget(-4.6, 0.3, -1.2, 0.4, "take hanger");
    }

    // --- exit door (right wall) ---
    const door = new THREE.Mesh(
      new THREE.BoxGeometry(0.3, 1.4, 1.6),
      new THREE.MeshStandardMaterial({
        color: 0xffd98a, emissive: 0xa9793a, emissiveIntensity: 0.3, roughness: 0.5,
      })
    );
    door.position.set(5.6, 0.7, 1.4);
    scene.add(door);
    markInteractive(door, "open door");
    addHitTarget(5.6, 0.7, 1.4, 0.45, "open door");

    render();
    setupInteraction(sendCommand);
  },

  hallway(api, view) {
    const { THREE, createScene, container, sendCommand } = api;

    const hallDoorUnlocked = view.hall_door_unlocked;
    const spareDoorUnlocked = view.spare_door_unlocked;

    const { scene, wall, markInteractive, addHitTarget, render, setupInteraction } =
      createScene(container, { roomWidth: 5, roomDepth: 16, viewSize: 9 });

    wall(5, 0.8, 0.2, 0, 0.4, -8);    // far end — the living room door sits flush against this
    wall(0.2, 0.8, 16, -2.5, 0.4, 0); // left
    wall(0.2, 0.8, 16, 2.5, 0.4, 0);  // right
    wall(5, 0.8, 0.2, 0, 0.4, 8);     // near end (behind camera-ish)

    // door back to the bedroom
    const backDoor = new THREE.Mesh(
      new THREE.BoxGeometry(1.2, 1.2, 0.2),
      new THREE.MeshStandardMaterial({ color: 0x6b4f2c, roughness: 0.8 })
    );
    backDoor.position.set(0, 0.6, 7.9);
    scene.add(backDoor);
    markInteractive(backDoor, "go bedroom");
    addHitTarget(0, 0.6, 7.9, 0.5, "go bedroom");

    // flickering ambient light, matching "the lights flicker"
    const flicker = new THREE.PointLight(0xffd98a, 1, 12);
    flicker.position.set(0, 3, 0);
    scene.add(flicker);
    setInterval(function () {
      flicker.intensity = 0.5 + Math.random() * 0.9;
    }, 120);

    // the living room door — straight down the hallway, needs the key from the bedroom
    const livingRoomDoor = new THREE.Mesh(
      new THREE.BoxGeometry(1.4, 1.3, 0.2),
      new THREE.MeshStandardMaterial({
        color: hallDoorUnlocked ? 0xffd98a : 0x6b4f2c,
        emissive: hallDoorUnlocked ? 0xa9793a : 0x000000,
        emissiveIntensity: hallDoorUnlocked ? 0.5 : 0,
        roughness: 0.8,
      })
    );
    livingRoomDoor.position.set(0, 0.65, -7.9);
    scene.add(livingRoomDoor);
    markInteractive(livingRoomDoor, "open living room door");
    addHitTarget(0, 0.65, -7.9, 0.6, "open living room door");

    // four more doors, two on each side wall — only the keypad one does
    // anything right now; the other three are future rooms still being built
    const keypadCommand = spareDoorUnlocked ? "open keypad door" : "enter code";
    const sideDoors = [
      { x: -2.5, z: -4, keypad: true },
      { x: -2.5, z: 4, keypad: false },
      { x: 2.5, z: -4, keypad: false },
      { x: 2.5, z: 4, keypad: false },
    ];
    sideDoors.forEach(function (d) {
      const command = d.keypad ? keypadCommand : "open stuck door";
      const lit = d.keypad && spareDoorUnlocked;
      const door = new THREE.Mesh(
        new THREE.BoxGeometry(0.2, 1.3, 1.1),
        new THREE.MeshStandardMaterial({
          color: lit ? 0xffd98a : 0x6b4f2c,
          emissive: lit ? 0xa9793a : 0x000000,
          emissiveIntensity: lit ? 0.5 : 0,
          roughness: 0.8,
        })
      );
      door.position.set(d.x, 0.65, d.z);
      scene.add(door);
      markInteractive(door, command);
      addHitTarget(d.x, 0.65, d.z, 0.5, command);

      if (d.keypad) {
        const panelX = d.x < 0 ? d.x + 0.1 : d.x - 0.1;
        const keypadPanel = new THREE.Mesh(
          new THREE.BoxGeometry(0.1, 0.25, 0.2),
          new THREE.MeshStandardMaterial({
            color: 0x1a150f, emissive: 0xffd98a, emissiveIntensity: 0.3, roughness: 0.5,
          })
        );
        keypadPanel.position.set(panelX, 0.65, d.z + 0.7);
        scene.add(keypadPanel);
        markInteractive(keypadPanel, command);
        addHitTarget(panelX, 0.65, d.z + 0.7, 0.3, command);
      }
    });

    render();
    setupInteraction(sendCommand);
  },

  spare_bedroom(api, view) {
    const { THREE, createScene, container, sendCommand } = api;

    const spareClosetOpen = view.spare_closet_open;
    const spareBedMade = view.spare_bed_made;
    const spareDrawerOpen = view.spare_drawer_open;
    const hasPhone = view.has_phone;

    const { scene, wall, markInteractive, addHitTarget, render, setupInteraction } =
      createScene(container, { roomWidth: 12, roomDepth: 8 });

    wall(12, 0.8, 0.2, 0, 0.4, -4);   // back
    wall(0.2, 0.8, 8, -6, 0.4, 0);    // left
    wall(0.2, 0.8, 8, 6, 0.4, 0);     // right
    wall(12, 0.8, 0.2, 0, 0.4, 4);    // front

    // --- bed, dusty and untouched until made ---
    const bedFrame = new THREE.Mesh(
      new THREE.BoxGeometry(3, 0.5, 1.8),
      new THREE.MeshStandardMaterial({ color: 0xa9793a, roughness: 0.9 })
    );
    bedFrame.position.set(-1.2, 0.25, -0.3);
    scene.add(bedFrame);
    const pillow = new THREE.Mesh(
      new THREE.BoxGeometry(0.7, 0.15, 1.4),
      new THREE.MeshStandardMaterial({ color: 0x6b4f2c, roughness: 0.9 })
    );
    pillow.position.set(-2.2, 0.55, -0.3);
    scene.add(pillow);
    markInteractive(bedFrame, spareBedMade ? "look bed" : "make bed");
    markInteractive(pillow, spareBedMade ? "look bed" : "make bed");

    // --- nightstand, with a dead phone in the drawer ---
    const stand = new THREE.Mesh(
      new THREE.BoxGeometry(0.9, 0.6, 0.9),
      new THREE.MeshStandardMaterial({ color: 0x6b4f2c, roughness: 0.8 })
    );
    stand.position.set(1, 0.3, -1);
    scene.add(stand);
    markInteractive(stand, "look nightstand");

    if (spareDrawerOpen && !hasPhone) {
      const phone = new THREE.Mesh(
        new THREE.BoxGeometry(0.15, 0.03, 0.3),
        new THREE.MeshStandardMaterial({ color: 0x1a150f, roughness: 0.4 })
      );
      phone.position.set(1, 0.64, -1);
      scene.add(phone);
      addHitTarget(1, 0.64, -1, 0.4, "take phone");
    }

    // --- closet (left wall), nothing useful inside ---
    const closet = new THREE.Mesh(
      new THREE.BoxGeometry(1.8, spareClosetOpen ? 0.15 : 1.0, 2.2),
      new THREE.MeshStandardMaterial({ color: 0x6b4f2c, roughness: 0.9 })
    );
    closet.position.set(-4.6, spareClosetOpen ? 0.08 : 0.5, -1.2);
    scene.add(closet);
    markInteractive(closet, "open closet");

    // --- door back to the hallway ---
    const door = new THREE.Mesh(
      new THREE.BoxGeometry(0.3, 1.4, 1.6),
      new THREE.MeshStandardMaterial({ color: 0x6b4f2c, roughness: 0.8 })
    );
    door.position.set(5.6, 0.7, 1.4);
    scene.add(door);
    markInteractive(door, "go hallway");
    addHitTarget(5.6, 0.7, 1.4, 0.45, "go hallway");

    render();
    setupInteraction(sendCommand);
  },

  living_room(api, view) {
    const { THREE, createScene, container, sendCommand } = api;

    const lrDoorUnlocked = view.lr_door_unlocked;
    const couchSearched = view.couch_searched;
    const reclinerSearched = view.recliner_searched;
    const hasNotepad = view.has_notepad;
    const hasPen = view.has_pen;
    const hasHanger = view.has_hanger;

    const { scene, wall, markInteractive, addHitTarget, render, setupInteraction } =
      createScene(container, { roomWidth: 12, roomDepth: 8 });

    wall(12, 0.8, 0.2, 0, 0.4, -4);  // back
    wall(0.2, 0.8, 8, -6, 0.4, 0);   // left
    wall(0.2, 0.8, 8, 6, 0.4, 0);    // right
    wall(12, 0.8, 0.2, 0, 0.4, 4);   // front (hallway side)

    // bookshelf, back-left corner
    const shelf = new THREE.Mesh(
      new THREE.BoxGeometry(1.6, 1.6, 0.5),
      new THREE.MeshStandardMaterial({ color: 0x6b4f2c, roughness: 0.9 })
    );
    shelf.position.set(-4.6, 0.8, -3.6);
    scene.add(shelf);
    markInteractive(shelf, "look bookshelf");

    const book = new THREE.Mesh(
      new THREE.BoxGeometry(0.15, 0.25, 0.4),
      new THREE.MeshStandardMaterial({ color: 0xffd98a, roughness: 0.5 })
    );
    book.position.set(-4.0, 0.7, -3.6);
    scene.add(book);
    addHitTarget(-4.0, 0.7, -3.6, 0.35, "look war of the worlds");

    // TV, against back wall
    const tv = new THREE.Mesh(
      new THREE.BoxGeometry(1.2, 0.9, 0.3),
      new THREE.MeshStandardMaterial({
        color: 0x333333, emissive: 0x6b4f2c, emissiveIntensity: 0.6, roughness: 0.3,
      })
    );
    tv.position.set(0, 0.9, -3.7);
    scene.add(tv);
    markInteractive(tv, "look tv");

    // couch, facing the TV
    const couch = new THREE.Mesh(
      new THREE.BoxGeometry(2.4, 0.6, 1),
      new THREE.MeshStandardMaterial({ color: 0xa9793a, roughness: 0.8 })
    );
    couch.position.set(-1, 0.3, -0.8);
    scene.add(couch);
    markInteractive(couch, "search couch");
    if (!couchSearched) {
      addHitTarget(-1, 0.3, -0.8, 0.4, "search couch");
    }

    // recliner, next to the couch
    const recliner = new THREE.Mesh(
      new THREE.BoxGeometry(1, 0.7, 1),
      new THREE.MeshStandardMaterial({ color: 0xf0a94a, roughness: 0.8 })
    );
    recliner.position.set(1.4, 0.35, -0.6);
    scene.add(recliner);
    markInteractive(recliner, "search recliner");
    if (!reclinerSearched) {
      addHitTarget(1.4, 0.35, -0.6, 0.4, "search recliner");
    }

    // desk, right side
    const desk = new THREE.Mesh(
      new THREE.BoxGeometry(1.6, 0.6, 0.9),
      new THREE.MeshStandardMaterial({ color: 0x6b4f2c, roughness: 0.8 })
    );
    desk.position.set(4.3, 0.3, 0);
    scene.add(desk);
    markInteractive(desk, "look desk");

    const monitor = new THREE.Mesh(
      new THREE.BoxGeometry(0.5, 0.4, 0.1),
      new THREE.MeshStandardMaterial({
        color: 0x222222, emissive: 0x4a3418, emissiveIntensity: 0.5, roughness: 0.3,
      })
    );
    monitor.position.set(4.3, 0.8, -0.3);
    scene.add(monitor);
    markInteractive(monitor, "use computer");
    addHitTarget(4.3, 0.8, -0.3, 0.35, "use computer");

    const keyboard = new THREE.Mesh(
      new THREE.BoxGeometry(0.5, 0.05, 0.2),
      new THREE.MeshStandardMaterial({ color: 0x3a2614, roughness: 0.7 })
    );
    keyboard.position.set(4.3, 0.63, 0.15);
    scene.add(keyboard);
    markInteractive(keyboard, "look under keyboard");
    addHitTarget(4.3, 0.63, 0.15, 0.3, "look under keyboard");

    if (!hasNotepad) {
      const notepad = new THREE.Mesh(
        new THREE.BoxGeometry(0.18, 0.02, 0.24),
        new THREE.MeshStandardMaterial({ color: 0xffd98a, roughness: 0.6 })
      );
      notepad.position.set(3.9, 0.64, 0.3);
      scene.add(notepad);
      addHitTarget(3.9, 0.64, 0.3, 0.3, "take notepad");
    }
    if (!hasPen) {
      const pen = new THREE.Mesh(
        new THREE.CylinderGeometry(0.02, 0.02, 0.15, 6),
        new THREE.MeshStandardMaterial({ color: 0xf0a94a, roughness: 0.4 })
      );
      pen.rotation.z = Math.PI / 2;
      pen.position.set(4.1, 0.65, 0.35);
      scene.add(pen);
      addHitTarget(4.1, 0.65, 0.35, 0.3, "take pen");
    }

    // front door, boarded (front wall)
    const frontDoor = new THREE.Mesh(
      new THREE.BoxGeometry(0.2, 1.4, 1.3),
      new THREE.MeshStandardMaterial({ color: 0x4a3418, roughness: 1 })
    );
    frontDoor.position.set(-3, 0.7, 3.9);
    scene.add(frontDoor);
    markInteractive(frontDoor, hasHanger ? "use hanger on front door" : "look front door");
    addHitTarget(-3, 0.7, 3.9, 0.45, hasHanger ? "use hanger on front door" : "look front door");

    // the other door, to the kitchen
    const otherDoor = new THREE.Mesh(
      new THREE.BoxGeometry(0.2, 1.4, 1.3),
      new THREE.MeshStandardMaterial({
        color: lrDoorUnlocked ? 0xffd98a : 0x6b4f2c,
        emissive: lrDoorUnlocked ? 0xa9793a : 0x000000,
        emissiveIntensity: lrDoorUnlocked ? 0.5 : 0,
        roughness: 0.8,
      })
    );
    otherDoor.position.set(3, 0.7, 3.9);
    scene.add(otherDoor);
    markInteractive(otherDoor, "open door");
    addHitTarget(3, 0.7, 3.9, 0.45, "open door");

    render();
    setupInteraction(sendCommand);
  },

  kitchen(api, view) {
    const { THREE, createScene, container, sendCommand } = api;

    const kitchenExitUnlocked = view.kitchen_exit_unlocked;
    const hasPowerBank = view.has_power_bank;

    const { scene, wall, markInteractive, addHitTarget, render, setupInteraction } =
      createScene(container, { roomWidth: 12, roomDepth: 8 });

    wall(12, 0.8, 0.2, 0, 0.4, -4);  // back
    wall(0.2, 0.8, 8, -6, 0.4, 0);   // left
    wall(0.2, 0.8, 8, 6, 0.4, 0);    // right
    wall(12, 0.8, 0.2, 0, 0.4, 4);   // front

    // fridge, left wall
    const fridge = new THREE.Mesh(
      new THREE.BoxGeometry(0.9, 1.6, 0.9),
      new THREE.MeshStandardMaterial({ color: 0x6b4f2c, roughness: 0.6 })
    );
    fridge.position.set(-4.8, 0.8, -3);
    scene.add(fridge);
    markInteractive(fridge, "look fridge");

    // stove, back wall
    const stove = new THREE.Mesh(
      new THREE.BoxGeometry(1, 0.9, 0.7),
      new THREE.MeshStandardMaterial({ color: 0x4a3418, roughness: 0.6 })
    );
    stove.position.set(-2.5, 0.45, -3.5);
    scene.add(stove);
    markInteractive(stove, "look stove clock");
    addHitTarget(-2.5, 0.45, -3.5, 0.45, "look stove clock");

    const clockLight = new THREE.Mesh(
      new THREE.BoxGeometry(0.1, 0.05, 0.02),
      new THREE.MeshStandardMaterial({ color: 0xffd98a, emissive: 0xffd98a, emissiveIntensity: 1 })
    );
    clockLight.position.set(-2.5, 0.75, -3.14);
    scene.add(clockLight);
    setInterval(function () {
      clockLight.visible = !clockLight.visible;
      render();
    }, 500);

    // sink, back wall
    const sink = new THREE.Mesh(
      new THREE.BoxGeometry(0.9, 0.5, 0.6),
      new THREE.MeshStandardMaterial({ color: 0xa9793a, roughness: 0.4 })
    );
    sink.position.set(-1, 0.3, -3.6);
    scene.add(sink);
    markInteractive(sink, "look sink");

    // cabinets, right wall
    const cabinet = new THREE.Mesh(
      new THREE.BoxGeometry(0.5, 1.4, 1.8),
      new THREE.MeshStandardMaterial({ color: 0x6b4f2c, roughness: 0.7 })
    );
    cabinet.position.set(5.6, 0.7, -2.5);
    scene.add(cabinet);
    markInteractive(cabinet, "look cabinet");

    // counter, right wall (below the cabinets, toward the front)
    const counter = new THREE.Mesh(
      new THREE.BoxGeometry(0.6, 0.5, 1.5),
      new THREE.MeshStandardMaterial({ color: 0xa9793a, roughness: 0.5 })
    );
    counter.position.set(5.6, 0.25, 1);
    scene.add(counter);
    markInteractive(counter, "look counter");

    if (!hasPowerBank) {
      const powerBank = new THREE.Mesh(
        new THREE.BoxGeometry(0.2, 0.08, 0.35),
        new THREE.MeshStandardMaterial({ color: 0xffd98a, roughness: 0.4 })
      );
      powerBank.position.set(5.6, 0.54, 1);
      scene.add(powerBank);
      addHitTarget(5.6, 0.54, 1, 0.35, "take power bank");
    }

    // round dining table + chairs, center
    const table = new THREE.Mesh(
      new THREE.CylinderGeometry(1, 1, 0.1, 16),
      new THREE.MeshStandardMaterial({ color: 0xa9793a, roughness: 0.6 })
    );
    table.position.set(0.5, 0.5, 0.5);
    scene.add(table);
    markInteractive(table, "look table");
    addHitTarget(0.5, 0.5, 0.5, 0.6, "look table");

    const tableLeg = new THREE.Mesh(
      new THREE.CylinderGeometry(0.1, 0.1, 0.5, 8),
      new THREE.MeshStandardMaterial({ color: 0x6b4f2c, roughness: 0.8 })
    );
    tableLeg.position.set(0.5, 0.25, 0.5);
    scene.add(tableLeg);

    const chairOffsets = [[1.5, 0.5], [-0.5, 0.5], [0.5, 1.5], [0.5, -0.5]];
    chairOffsets.forEach(function (pos) {
      const chair = new THREE.Mesh(
        new THREE.BoxGeometry(0.35, 0.4, 0.35),
        new THREE.MeshStandardMaterial({ color: 0x6b4f2c, roughness: 0.8 })
      );
      chair.position.set(pos[0], 0.2, pos[1]);
      scene.add(chair);
      markInteractive(chair, "look table");
    });

    // door to the garage, behind the table
    const door = new THREE.Mesh(
      new THREE.BoxGeometry(1.2, 1.3, 0.2),
      new THREE.MeshStandardMaterial({
        color: kitchenExitUnlocked ? 0xffd98a : 0x6b4f2c,
        emissive: kitchenExitUnlocked ? 0xa9793a : 0x000000,
        emissiveIntensity: kitchenExitUnlocked ? 0.5 : 0,
        roughness: 0.8,
      })
    );
    door.position.set(0.5, 0.65, 3.9);
    scene.add(door);
    markInteractive(door, "open door");
    addHitTarget(0.5, 0.65, 3.9, 0.5, "open door");

    render();
    setupInteraction(sendCommand);
  },

  garage(api, view) {
    const { THREE, createScene, container, sendCommand } = api;

    const clawPlugged = view.claw_plugged;
    const hasWrench = view.has_wrench;
    const hasScrewdriver = view.has_screwdriver;
    const hasTurtle = view.has_turtle;
    const hasHanger = view.has_hanger;

    const { scene, wall, markInteractive, addHitTarget, render, setupInteraction } =
      createScene(container, { roomWidth: 12, roomDepth: 8 });

    wall(12, 0.8, 0.2, 0, 0.4, -4);  // back
    wall(0.2, 0.8, 8, -6, 0.4, 0);   // left
    wall(0.2, 0.8, 8, 6, 0.4, 0);    // right

    // garage door, front wall — a dead end, never opens
    const garageDoor = new THREE.Mesh(
      new THREE.BoxGeometry(6, 1.6, 0.25),
      new THREE.MeshStandardMaterial({ color: 0x4a3418, roughness: 1 })
    );
    garageDoor.position.set(-2, 0.8, 3.9);
    scene.add(garageDoor);
    markInteractive(garageDoor, "open garage door");
    addHitTarget(-2, 0.8, 3.9, 0.7, "open garage door");

    // the actual exit door
    const exitDoor = new THREE.Mesh(
      new THREE.BoxGeometry(0.25, 1.4, 1.2),
      new THREE.MeshStandardMaterial({
        color: 0xffd98a, emissive: 0xa9793a, emissiveIntensity: 0.4, roughness: 0.6,
      })
    );
    exitDoor.position.set(5.6, 0.7, 3);
    scene.add(exitDoor);
    const exitCommand = hasHanger ? "use hanger on door" : "open door";
    markInteractive(exitDoor, exitCommand);
    addHitTarget(5.6, 0.7, 3, 0.5, exitCommand);

    // old car, left-center
    const carBody = new THREE.Mesh(
      new THREE.BoxGeometry(2.6, 0.6, 1.3),
      new THREE.MeshStandardMaterial({ color: 0x6b4f2c, roughness: 0.5 })
    );
    carBody.position.set(-2.5, 0.3, -1.2);
    scene.add(carBody);
    markInteractive(carBody, "look car");

    const hood = new THREE.Mesh(
      new THREE.BoxGeometry(0.9, 0.08, 1.2),
      new THREE.MeshStandardMaterial({ color: 0xa9793a, roughness: 0.5 })
    );
    hood.position.set(-3.5, 0.75, -1.2);
    hood.rotation.z = 0.5;
    scene.add(hood);
    markInteractive(hood, "look car");

    // workbench, right wall
    const bench = new THREE.Mesh(
      new THREE.BoxGeometry(0.6, 0.6, 2),
      new THREE.MeshStandardMaterial({ color: 0x6b4f2c, roughness: 0.8 })
    );
    bench.position.set(5.5, 0.3, -1);
    scene.add(bench);
    markInteractive(bench, "look counter");

    if (!hasWrench) {
      const wrench = new THREE.Mesh(
        new THREE.BoxGeometry(0.08, 0.03, 0.4),
        new THREE.MeshStandardMaterial({ color: 0xffd98a, metalness: 0.6, roughness: 0.3 })
      );
      wrench.position.set(5.2, 0.63, -1.5);
      scene.add(wrench);
      addHitTarget(5.2, 0.63, -1.5, 0.35, "take wrench");
    }
    if (!hasScrewdriver) {
      const screwdriver = new THREE.Mesh(
        new THREE.CylinderGeometry(0.03, 0.03, 0.35, 8),
        new THREE.MeshStandardMaterial({ color: 0xf0a94a, roughness: 0.4 })
      );
      screwdriver.rotation.z = Math.PI / 2;
      screwdriver.position.set(5.6, 0.63, -0.7);
      scene.add(screwdriver);
      addHitTarget(5.6, 0.63, -0.7, 0.35, "take screwdriver");
    }

    // claw machine, right-front corner
    const claw = new THREE.Mesh(
      new THREE.BoxGeometry(1, 1.6, 1),
      new THREE.MeshStandardMaterial({
        color: clawPlugged ? 0xffd98a : 0x4a3418,
        emissive: clawPlugged ? 0xffd98a : 0x000000,
        emissiveIntensity: clawPlugged ? 0.5 : 0,
        roughness: 0.4,
      })
    );
    claw.position.set(4.8, 0.8, 2.8);
    scene.add(claw);

    let clawCommand = "plug in claw machine";
    if (clawPlugged && !hasTurtle) { clawCommand = "play claw"; }
    else if (hasTurtle) { clawCommand = "look turtle"; }
    markInteractive(claw, clawCommand);
    addHitTarget(4.8, 0.8, 2.8, 0.6, clawCommand);

    if (clawPlugged) {
      const clawLight = new THREE.PointLight(0xffd98a, 1, 3);
      clawLight.position.set(4.8, 1.6, 2.8);
      scene.add(clawLight);
    }

    render();
    setupInteraction(sendCommand);
  },
};
