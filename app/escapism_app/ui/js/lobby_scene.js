// The lobby scene: four doors, each with a floor number and a leaderboard
// panel above it. Built by app.js whenever the player is in the lobby.
//   view.doors = [{id, number, title, status: "open"|"done"|"closed", scores: [{name, time}]}]

export function buildLobby(api, view) {
  const { THREE, createScene, container, sendCommand } = api;

    const doors = view.doors;

    const { scene, wall, markInteractive, addHitTarget, render, setupInteraction } =
    createScene(container, { roomWidth: 12, roomDepth: 8 });

    wall(12, 0.8, 0.2, 0, 0.4, -4);   // back (the four doors sit against this)
    wall(0.2, 0.8, 8, -6, 0.4, 0);    // left
    wall(0.2, 0.8, 8, 6, 0.4, 0);     // right
    wall(12, 0.8, 0.2, 0, 0.4, 4);    // front

    // a rug in the middle of the lobby, just for looks
    const rug = new THREE.Mesh(
    new THREE.BoxGeometry(5, 0.02, 3),
    new THREE.MeshStandardMaterial({ color: 0x5a2e2e, roughness: 1 })
    );
    rug.position.set(0, 0.01, 0.6);
    scene.add(rug);

    // flat floor label: a big door number with a status word underneath
    function floorLabel(number, word, x, z) {
    const canvas = document.createElement("canvas");
    canvas.width = 256; canvas.height = 128;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#ffd98a";
    ctx.textAlign = "center";
    ctx.font = "bold 70px monospace";
    ctx.fillText(String(number), 128, 70);
    ctx.font = "bold 28px monospace";
    ctx.fillText(word, 128, 112);
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    const label = new THREE.Mesh(
      new THREE.PlaneGeometry(1.6, 0.8),
      new THREE.MeshBasicMaterial({ map: texture, transparent: true })
    );
    label.rotation.x = -Math.PI / 2;
    label.position.set(x, 0.05, z);
    scene.add(label);
    }

    // leaderboard panel floating above a door, tilted to face the camera so the
    // text stays readable from the top-down view
    function leaderboardPanel(door, x) {
    const W = 512, H = 320;
    const canvas = document.createElement("canvas");
    canvas.width = W; canvas.height = H;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#1a150f";
    ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = door.status === "closed" ? "#6b4f2c" : "#ffd98a";
    ctx.lineWidth = 8;
    ctx.strokeRect(4, 4, W - 8, H - 8);

    ctx.fillStyle = "#ffd98a";
    ctx.textAlign = "center";
    const titleText = String(door.title).toUpperCase();
    let titleSize = 34;
    ctx.font = "bold " + titleSize + "px monospace";
    while (titleSize > 14 && ctx.measureText(titleText).width > W - 40) {
      titleSize -= 2;
      ctx.font = "bold " + titleSize + "px monospace";
    }
    ctx.fillText(titleText, W / 2, 56);
    ctx.fillStyle = "#a9793a";
    ctx.font = "bold 22px monospace";
    ctx.fillText(door.status === "closed" ? "DOOR " + door.number : "FASTEST ESCAPES", W / 2, 88);

    if (door.status === "closed") {
      ctx.fillStyle = "#6b4f2c";
      ctx.font = "bold 30px monospace";
      ctx.fillText("COMING SOON", W / 2, 190);
    } else if (!door.scores || door.scores.length === 0) {
      ctx.fillStyle = "#a9793a";
      ctx.font = "bold 28px monospace";
      ctx.fillText("NO TIMES YET", W / 2, 190);
    } else {
      ctx.font = "bold 28px monospace";
      door.scores.slice(0, 5).forEach(function (s, i) {
        const y = 134 + i * 36;
        ctx.fillStyle = i === 0 ? "#ffd98a" : "#f0a94a";
        ctx.textAlign = "left";
        ctx.fillText((i + 1) + ". " + String(s.name).slice(0, 12), 28, y);
        ctx.textAlign = "right";
        ctx.fillText(s.time, W - 28, y);
      });
    }

    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    const panel = new THREE.Mesh(
      new THREE.PlaneGeometry(2.7, 1.7),
      new THREE.MeshBasicMaterial({ map: texture })
    );
    panel.rotation.x = -0.97;          // faces the camera at (0, 11, 7.5)
    panel.position.set(x, 2.5, -4.4);
    scene.add(panel);
    }

    const looks = {
    open:   { color: 0xffd98a, emissive: 0xa9793a, intensity: 0.5, word: "OPEN" },
    done:   { color: 0x8fcf8f, emissive: 0x2f6f2f, intensity: 0.5, word: "ESCAPED" },
    closed: { color: 0x4a4038, emissive: 0x000000, intensity: 0,   word: "CLOSED" },
    };
    const xs = [-4.5, -1.5, 1.5, 4.5];

    doors.forEach(function (d, i) {
    const look = looks[d.status] || looks.closed;
    const x = xs[i];
    const door = new THREE.Mesh(
      new THREE.BoxGeometry(1.4, 1.4, 0.2),
      new THREE.MeshStandardMaterial({
        color: look.color,
        emissive: look.emissive,
        emissiveIntensity: look.intensity,
        roughness: 0.6,
      })
    );
    door.position.set(x, 0.7, -3.9);
    scene.add(door);
    const command = "open door " + d.number;
    markInteractive(door, command);
    addHitTarget(x, 0.7, -3.9, 0.7, command);
    floorLabel(d.number, look.word, x, -2.9);
    leaderboardPanel(d, x);
    });

    render();
    setupInteraction(sendCommand);
}
