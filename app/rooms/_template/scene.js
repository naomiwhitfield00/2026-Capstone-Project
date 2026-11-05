// The 3D picture for each place in your room. Totally optional: if a place has
// no function here, the player just sees "3D picture unavailable" and plays with text.
//
// Each function gets:
//   api.createScene(api.container, { roomWidth, roomDepth })   -> drawing helpers
//   api.THREE                                                   -> the 3D library
//   view   -> whatever view() in room.py returned
// Clicking something runs a command, exactly as if the player typed it.

export const scenes = {
  cell(api, view) {
    const { THREE, createScene, container } = api;
    const { scene, wall, markInteractive, addHitTarget, render, setupInteraction } =
      createScene(container, { roomWidth: 12, roomDepth: 8 });
    const sendCommand = api.sendCommand;

    // four low walls around the floor
    wall(12, 0.8, 0.2, 0, 0.4, -4);
    wall(0.2, 0.8, 8, -6, 0.4, 0);
    wall(0.2, 0.8, 8, 6, 0.4, 0);
    wall(12, 0.8, 0.2, 0, 0.4, 4);

    // a box on the floor. Clicking it types "open box".
    const box = new THREE.Mesh(
      new THREE.BoxGeometry(1.6, 0.8, 1),
      new THREE.MeshStandardMaterial({ color: view.box_open ? 0x8a5a2a : 0xa9793a })
    );
    box.position.set(-2, 0.4, 0);
    scene.add(box);
    markInteractive(box, "open box");

    // a door on the far wall
    const door = new THREE.Mesh(
      new THREE.BoxGeometry(1.4, 1.4, 0.2),
      new THREE.MeshStandardMaterial({ color: view.has_key ? 0x8fcf8f : 0x6b4f2c })
    );
    door.position.set(3, 0.7, -3.9);
    scene.add(door);
    markInteractive(door, "open door");

    render();
    setupInteraction(sendCommand);
  },
};
