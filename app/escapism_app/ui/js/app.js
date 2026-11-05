// The game page. Talks to the local server (server.py) and draws everything:
// profile screen, the 3D scene, the text log, the clock and the leaderboards.

// (Three.js and the scene files are loaded on demand, so the menus and the text
// game still work even if the 3D library can't be loaded.)

const $ = (id) => document.getElementById(id);

// ---------------------------------------------------------------- server calls
async function api(path, body) {
  const options = body === undefined ? {} : {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
  const response = await fetch(path, options);
  return response.json();
}

// ---------------------------------------------------------------- state
let state = null;
let currentSceneKey = "";
let currentHandles = [];
let sceneToken = 0;
let clockTimer = null;

async function apply(newState) {
  state = newState;
  if (state.screen === "profile") {
    showProfileScreen();
  } else {
    showGameScreen();
  }
}

function show(id, visible) { $(id).classList.toggle("hidden", !visible); }

// ---------------------------------------------------------------- profile screen
let chosenLogo = "";

function showProfileScreen() {
  show("profileScreen", true);
  show("gameScreen", false);
  stopClock();
  disposeScene();
  currentSceneKey = "";

  const picker = $("logoPicker");
  picker.innerHTML = "";
  if (!chosenLogo || !state.logos.includes(chosenLogo)) { chosenLogo = state.logos[0] || ""; }
  state.logos.forEach((file) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "logo-choice" + (file === chosenLogo ? " selected" : "");
    button.innerHTML = `<img src="/logos/${encodeURIComponent(file)}" alt="${file}">`;
    button.addEventListener("click", () => {
      chosenLogo = file;
      picker.querySelectorAll(".logo-choice").forEach((b) => b.classList.remove("selected"));
      button.classList.add("selected");
    });
    picker.appendChild(button);
  });

  const list = $("profileList");
  list.innerHTML = "";
  show("existingProfiles", state.profiles.length > 0);
  state.profiles.forEach((p) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "profile-choice";
    button.innerHTML = (p.logo ? `<img src="/logos/${encodeURIComponent(p.logo)}" alt="">` : "") +
      `<span></span>`;
    button.querySelector("span").textContent = p.name;
    button.addEventListener("click", async () => apply(await api("/api/login", { name: p.name, logo: p.logo })));
    list.appendChild(button);
  });
  $("nameInput").focus();
}

$("profileForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const name = $("nameInput").value.trim() || "Anonymous";
  await apply(await api("/api/login", { name, logo: chosenLogo }));
});

// ---------------------------------------------------------------- game screen
function showGameScreen() {
  show("profileScreen", false);
  show("gameScreen", true);

  $("roomTitle").textContent = state.in_room ? state.room_title.toUpperCase() : "THE LOBBY";
  $("playerName").textContent = state.profile.name;
  const logo = $("playerLogo");
  logo.src = state.profile.logo ? "/logos/" + encodeURIComponent(state.profile.logo) : "";
  logo.style.display = state.profile.logo ? "" : "none";
  show("lobbyBtn", state.in_room);

  renderLog();
  setupInput();
  startClock();
  renderScene();
}

function renderLog() {
  const screen = $("screen");
  screen.innerHTML = "";
  state.log.forEach((entry) => {
    const div = document.createElement("div");
    if (entry.kind === "input") {
      div.className = "line input-line";
      div.innerHTML = '<span class="prompt">&gt;</span> ';
      div.appendChild(document.createTextNode(entry.text));
    } else if (entry.text) {
      div.className = "line system-line";
      div.textContent = entry.text;
    } else {
      div.className = "line blank-line";
      div.innerHTML = "&nbsp;";
    }
    screen.appendChild(div);
  });
  screen.scrollTop = screen.scrollHeight;
}

function setupInput() {
  const input = $("cmdInput");
  input.type = state.hidden_input ? "password" : "text";
  input.placeholder = state.hidden_input ? "enter password…" : "type a command, or 'help'";
  input.focus();
}

async function sendCommand(text) {
  if (!text || !text.trim()) { return; }
  $("cmdInput").value = "";
  await apply(await api("/api/command", { text }));
}

$("cmdForm").addEventListener("submit", (event) => {
  event.preventDefault();
  sendCommand($("cmdInput").value);
});

// ---------------------------------------------------------------- clock
function startClock() {
  stopClock();
  const clock = $("clock");
  if (!state.clock_start) { clock.textContent = "--:--"; return; }   // lobby: clock stopped
  const tick = () => {
    const elapsed = Math.max(0, Math.floor(Date.now() / 1000 - state.clock_start));
    clock.textContent = String(Math.floor(elapsed / 60)).padStart(2, "0") + ":" +
                        String(elapsed % 60).padStart(2, "0");
  };
  tick();
  clockTimer = setInterval(tick, 1000);
}
function stopClock() { if (clockTimer) { clearInterval(clockTimer); clockTimer = null; } }

// ---------------------------------------------------------------- 3D scene
function disposeScene() {
  currentHandles.forEach((h) => { try { h.dispose(); } catch (e) { /* ignore */ } });
  currentHandles = [];
  $("scene3d").innerHTML = "";
}

async function renderScene() {
  const scene = state.scene;
  const key = JSON.stringify([scene.room_id, scene.loc, scene.view]);
  if (key === currentSceneKey) { return; }       // nothing changed -- keep the picture
  currentSceneKey = key;
  const token = ++sceneToken;
  disposeScene();

  const container = $("scene3d");
  try {
    const THREE = await import("three");
    const { createScene } = await import("/js/scene3d.js");
    const api3d = {
      THREE,
      container,
      sendCommand,
      // each room's scene.js calls this; we remember it so we can free it later
      createScene: (el, options) => {
        const handle = createScene(el, options);
        currentHandles.push(handle);
        return handle;
      },
    };
    if (scene.kind === "lobby") {
      const { buildLobby } = await import("/js/lobby_scene.js");
      if (token !== sceneToken) { return; }
      buildLobby(api3d, scene.view);
    } else {
      const module = await import(scene.module + "?v=" + Date.now());
      if (token !== sceneToken) { return; }
      const build = module.scenes && module.scenes[scene.loc];
      if (!build) { throw new Error("no scene for location '" + scene.loc + "'"); }
      build(api3d, scene.view);
    }
  } catch (err) {
    console.error("Escapism 3D scene failed to load:", err);
    if (token !== sceneToken) { return; }
    container.innerHTML = '<div class="scene-fallback">3D picture unavailable here — use the text commands below.</div>';
  }
}

// ---------------------------------------------------------------- buttons
$("lobbyBtn").addEventListener("click", async () => {
  if (confirm("Go back to the lobby? Your progress in this room will be lost.")) {
    await apply(await api("/api/leave_room", {}));
  }
});
$("switchBtn").addEventListener("click", async () => {
  if (!state.in_room || confirm("Switch player? Your progress in this room will be lost.")) {
    await apply(await api("/api/logout", {}));
  }
});

// ---------------------------------------------------------------- leaderboards
$("boardsBtn").addEventListener("click", async () => {
  const boards = await api("/api/leaderboards");
  const body = $("boardsBody");
  body.innerHTML = "";
  boards.forEach((board) => {
    const h = document.createElement("h2");
    h.className = "board-heading";
    h.textContent = `Door ${board.number} — ${board.title}`;
    body.appendChild(h);
    if (!board.available) {
      body.insertAdjacentHTML("beforeend", '<p class="empty-board">This door is still locked. Check back soon.</p>');
    } else if (!board.scores.length) {
      body.insertAdjacentHTML("beforeend", '<p class="empty-board">No one has escaped this room yet. Be the first.</p>');
    } else {
      const table = document.createElement("table");
      table.className = "board";
      table.innerHTML = "<thead><tr><th>#</th><th>Player</th><th>Date</th><th>Time</th></tr></thead>";
      const tbody = document.createElement("tbody");
      board.scores.forEach((s, i) => {
        const tr = document.createElement("tr");
        const nameCell = document.createElement("td");
        if (s.logo) {
          const img = document.createElement("img");
          img.src = "/logos/" + encodeURIComponent(s.logo);
          img.className = "board-logo";
          nameCell.appendChild(img);
        }
        nameCell.appendChild(document.createTextNode(s.name));
        [String(i + 1)].forEach((t) => { const td = document.createElement("td"); td.textContent = t; tr.appendChild(td); });
        tr.appendChild(nameCell);
        [s.date, s.time].forEach((t) => { const td = document.createElement("td"); td.textContent = t; tr.appendChild(td); });
        tbody.appendChild(tr);
      });
      table.appendChild(tbody);
      body.appendChild(table);
    }
  });
  show("boardsOverlay", true);
});
$("boardsClose").addEventListener("click", () => { show("boardsOverlay", false); if ($("cmdInput")) { $("cmdInput").focus(); } });

// ---------------------------------------------------------------- start
document.body.addEventListener("click", (event) => {
  const input = $("cmdInput");
  if (input && state && state.screen === "game" && !event.target.closest("button, input, .overlay")) { input.focus(); }
});
setInterval(() => { fetch("/api/ping").catch(() => {}); }, 5000);   // heartbeat (browser mode)
apply(await api("/api/state"));
