// Shared scaffolding for Escapism's top-down 3D room scenes.
// app.js hands createScene() to every room's scene.js. A scene builds its
// furniture/objects with the helpers below, then calls render() and
// setupInteraction(sendCommand).

import * as THREE from "three";

export const COLORS = {
  AMBER: 0xf0a94a,
  AMBER_DIM: 0xa9793a,
  AMBER_BRIGHT: 0xffd98a,
  AMBER_FAINT: 0x6b4f2c,
  SCREEN_BG: 0x1a150f,
};

/**
 * Sets up a top-down orthographic scene inside `container`.
 * roomWidth/roomDepth size the floor; viewSize controls camera zoom
 * (smaller = more zoomed in). Returns handles for adding room objects.
 */
export function createScene(container, opts = {}) {
  const roomWidth = opts.roomWidth || 12;
  const roomDepth = opts.roomDepth || 8;
  const viewSize = opts.viewSize || 6.5;

  const scene = new THREE.Scene();

  const aspect = container.clientWidth / container.clientHeight;
  const camera = new THREE.OrthographicCamera(
    -viewSize * aspect, viewSize * aspect, viewSize, -viewSize, 0.1, 100
  );
  camera.position.set(0, 11, 7.5);
  camera.lookAt(0, 0, 0);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(renderer.domElement);

  scene.add(new THREE.AmbientLight(0x3a2614, 1.4));
  const dLight = new THREE.DirectionalLight(COLORS.AMBER_BRIGHT, 0.9);
  dLight.position.set(4, 10, 4);
  scene.add(dLight);

  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(roomWidth, roomDepth),
    new THREE.MeshStandardMaterial({ color: COLORS.SCREEN_BG, roughness: 1 })
  );
  floor.rotation.x = -Math.PI / 2;
  scene.add(floor);

  const interactive = [];

  function wall(w, h, depth, x, y, z) {
    const m = new THREE.Mesh(
      new THREE.BoxGeometry(w, h, depth),
      new THREE.MeshStandardMaterial({ color: COLORS.AMBER_FAINT, roughness: 0.9 })
    );
    m.position.set(x, y, z);
    scene.add(m);
    return m;
  }

  function markInteractive(mesh, command) {
    mesh.userData.command = command;
    interactive.push(mesh);
    return mesh;
  }

  /**
   * An invisible, generously-sized sphere used as the actual click target
   * for small items (keys, a hanger, a doorknob...). Visual geometry can
   * stay small/detailed; this is what raycasting actually hits, so small
   * objects are still easy to click. `size` is the sphere radius in scene
   * units — 0.35–0.5 is a good range for anything fiddly.
   */
  function addHitTarget(x, y, z, size, command) {
    const proxy = new THREE.Mesh(
      new THREE.SphereGeometry(size, 8, 8),
      new THREE.MeshBasicMaterial({ transparent: true, opacity: 0 })
    );
    proxy.position.set(x, y, z);
    scene.add(proxy);
    markInteractive(proxy, command);
    return proxy;
  }

  function render() {
    renderer.render(scene, camera);
  }

  /** Wires up click-to-command and hover cursor. Call this last, after
   * all room objects are added. */
  function setupInteraction(sendCommand) {
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    function pick(event) {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(mouse, camera);
      const hits = raycaster.intersectObjects(interactive, false);
      return hits.length ? hits[0].object : null;
    }

    renderer.domElement.addEventListener("click", function (event) {
      const obj = pick(event);
      if (obj && obj.userData.command && typeof sendCommand === "function") {
        sendCommand(obj.userData.command);
      }
    });

    renderer.domElement.addEventListener("mousemove", function (event) {
      const obj = pick(event);
      renderer.domElement.style.cursor = obj ? "pointer" : "default";
    });

    function onResize() {
      const w = container.clientWidth;
      const h = container.clientHeight;
      const a = w / h;
      camera.left = -viewSize * a;
      camera.right = viewSize * a;
      camera.top = viewSize;
      camera.bottom = -viewSize;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
      render();
    }
    window.addEventListener("resize", onResize);
    removeResize = function () { window.removeEventListener("resize", onResize); };
  }

  let removeResize = null;

  /** Frees the scene. app.js calls this before building the next one. */
  function dispose() {
    if (removeResize) { removeResize(); }
    renderer.dispose();
    if (renderer.domElement.parentNode) {
      renderer.domElement.parentNode.removeChild(renderer.domElement);
    }
  }

  return {
    scene, camera, renderer, interactive,
    wall, markInteractive, addHitTarget, render, setupInteraction, dispose,
  };
}

export function showFallback(container, message) {
  container.innerHTML =
    '<div style="display:flex;align-items:center;justify-content:center;' +
    'height:100%;color:var(--amber-faint);font-size:12px;text-align:center;' +
    'padding:12px;">' + message + '</div>';
}
