// Runs every scene function against a stand-in for Three.js to catch typos and
// missing view values. (It cannot check how the picture LOOKS -- open the game for that.)
// Usage: node tests/test_scenes.mjs '<json view>'   (see run_scene_tests in test_app.py)
import { pathToFileURL } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const views = JSON.parse(process.argv[2]);

function chain() {
  const fn = function () { return chain(); };
  return new Proxy(fn, {
    get: (t, k) => (k === Symbol.toPrimitive ? () => 0 : k === "then" ? undefined : chain()),
    set: () => true, apply: () => chain(), construct: () => chain(),
  });
}
const THREE = new Proxy({}, { get: () => function () { return chain(); } });
globalThis.document = { createElement: () => ({ getContext: () => chain(), width: 0, height: 0 }) };

let commands = [];
const api = {
  THREE, container: chain(), sendCommand: () => {},
  createScene: () => ({
    scene: chain(), wall: () => chain(), render: () => {}, setupInteraction: () => {},
    markInteractive: (m, c) => { commands.push(c); return m; },
    addHitTarget: (x, y, z, s, c) => { commands.push(c); return chain(); },
  }),
};
let failures = 0;
for (const [name, file] of Object.entries({ rooms: "rooms/get_out_of_the_house/scene.js" })) {
  const mod = await import(pathToFileURL(path.join(root, file)).href);
  for (const [loc, view] of Object.entries(views)) {
    commands = [];
    try { mod.scenes[loc](api, view); console.log("ok", loc, commands.length, "clickables"); }
    catch (e) { failures++; console.log("FAIL", loc, e.message); }
  }
}
const lobby = await import(pathToFileURL(path.join(root, "escapism_app/ui/js/lobby_scene.js")).href);
commands = [];
try {
  lobby.buildLobby(api, { doors: [
    { number: 1, id: "a", title: "Get out of the house!", status: "open", scores: [{ name: "Corey", time: "1:00" }] },
    { number: 2, id: "b", title: "Coming soon", status: "closed", scores: [] },
    { number: 3, id: "c", title: "Done room", status: "done", scores: [] },
    { number: 4, id: "d", title: "Coming soon", status: "closed", scores: [] }] });
  console.log("ok lobby", commands);
} catch (e) { failures++; console.log("FAIL lobby", e.message); }
process.exit(failures ? 1 : 0);
