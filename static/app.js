/* SteppeGuard AI — 3D Three.js Interactive Engine + 2D Fallback + API Controller */

const state = {
  preset_id: "abai_high_wind",
  seed: 42,
  risk_lambda: 3.5,
  gamma: 0.90,
  tau: null,
  wind_override: null,
  resource_level: "High",
  model_choice: "logistic_regression",
  sensor_events: [],
  extra_obstacles: [],
  inspect_cell: [5, 5],
  showAstar: true,
  showBfs: true,
  showUcs: false,
  showExplored: true,
  renderMode: "3d",
  data: null,
  benchmarksLoaded: false,
  animatingSearch: false,
  animStep: 0,
  animTimer: null,
  droneProgress: 0,
  activeTab: "mission",
  hitlDecisions: {},
  fetchAbort: null,
  debounceTimer: null,
};

function riskToColorHex(risk, obstacle) {
  if (obstacle) return 0x475569;
  const r = Math.max(0, Math.min(1, risk));
  if (r < 0.25) return 0x166534;      // Deep safe steppe green
  if (r < 0.45) return 0x65a30d;      // Dry olive
  if (r < 0.65) return 0xf59e0b;      // Amber warning
  if (r < 0.82) return 0xf97316;      // Orange fire front
  return 0xef4444;                    // Intense crimson wildfire
}

function riskToCss(risk, obstacle) {
  if (obstacle) return "#475569";
  if (risk < 0.25) return "#166534";
  if (risk < 0.45) return "#65a30d";
  if (risk < 0.65) return "#f59e0b";
  if (risk < 0.82) return "#f97316";
  return "#ef4444";
}

/* ============================================================================
   3D THREE.JS TACTICAL STEPPE ENGINE (Zero external controls, 100% offline)
   ============================================================================ */
class Steppe3DScene {
  constructor(canvas, onSelectCell) {
    this.canvas = canvas;
    this.onSelectCell = onSelectCell;
    this.available = typeof THREE !== "undefined";
    if (!this.available) return;

    this.tileSize = 1.05;
    this.gridSize = 10;
    this.offset = ((this.gridSize - 1) * this.tileSize) / 2;

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x07101f);
    this.scene.fog = new THREE.FogExp2(0x07101f, 0.022);

    const w = canvas.clientWidth || 720;
    const h = canvas.clientHeight || 500;
    this.camera = new THREE.PerspectiveCamera(44, w / h, 0.1, 120);

    try {
      this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: "high-performance" });
    } catch (e) {
      this.available = false;
      return;
    }
    this.renderer.setSize(w, h, false);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

    // Orbit camera state
    this.orbit = { theta: 0.58, phi: 0.86, radius: 15.8, targetY: 0.4 };
    this.dragging = false;
    this.dragMoved = false;
    this.lastMouse = { x: 0, y: 0 };

    // Lights
    const hemi = new THREE.HemisphereLight(0x93c5fd, 0x0f172a, 0.95);
    this.scene.add(hemi);
    const dir = new THREE.DirectionalLight(0xfffbeb, 1.15);
    dir.position.set(10, 18, 12);
    this.scene.add(dir);
    this.fireLight = new THREE.PointLight(0xf97316, 1.8, 18);
    this.fireLight.position.set(0, 3.2, 0);
    this.scene.add(this.fireLight);

    // Base grid platform
    const baseGeo = new THREE.BoxGeometry(12.2, 0.35, 12.2);
    const baseMat = new THREE.MeshStandardMaterial({ color: 0x0b1526, roughness: 0.9, metalness: 0.15 });
    const baseMesh = new THREE.Mesh(baseGeo, baseMat);
    baseMesh.position.set(0, -0.25, 0);
    this.scene.add(baseMesh);

    const gridHelper = new THREE.GridHelper(12.2, 12, 0x1e3a5f, 0x132540);
    gridHelper.position.y = -0.06;
    this.scene.add(gridHelper);

    // Dynamic groups
    this.tilesGroup = new THREE.Group();
    this.pathsGroup = new THREE.Group();
    this.effectsGroup = new THREE.Group();
    this.exploredGroup = new THREE.Group();
    this.scene.add(this.tilesGroup, this.exploredGroup, this.pathsGroup, this.effectsGroup);

    this.tileMeshes = [];
    this.flameMeshes = [];
    this.beaconRings = [];
    this.drone = this._createDrone();
    this.scene.add(this.drone);

    // Selection cursor ring
    const selGeo = new THREE.BoxGeometry(1.04, 0.14, 1.04);
    const selMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8, wireframe: true });
    this.selectionRing = new THREE.Mesh(selGeo, selMat);
    this.scene.add(this.selectionRing);

    // Wind streak particles
    this.windParticles = this._createWindParticles();
    this.scene.add(this.windParticles);

    // Ember particles
    this.emberParticles = this._createEmberParticles();
    this.scene.add(this.emberParticles);

    this.raycaster = new THREE.Raycaster();
    this.pointer = new THREE.Vector2();
    this.clock = new THREE.Clock();

    this._bindEvents();
    this._updateCamera();
    this._animate();
  }

  gridToWorld(r, c, y = 0) {
    return new THREE.Vector3(
      c * this.tileSize - this.offset,
      y,
      r * this.tileSize - this.offset
    );
  }

  _createDrone() {
    const group = new THREE.Group();
    const body = new THREE.Mesh(
      new THREE.OctahedronGeometry(0.26, 0),
      new THREE.MeshStandardMaterial({ color: 0x38bdf8, emissive: 0x0284c7, emissiveIntensity: 0.7, metalness: 0.6, roughness: 0.25 })
    );
    body.scale.set(1.2, 0.55, 1.2);
    group.add(body);

    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(0.36, 0.035, 8, 24),
      new THREE.MeshBasicMaterial({ color: 0x4ade80 })
    );
    ring.rotation.x = Math.PI / 2;
    group.add(ring);

    this.rotors = [];
    const offsets = [[0.28, 0.28], [-0.28, 0.28], [0.28, -0.28], [-0.28, -0.28]];
    for (const [ox, oz] of offsets) {
      const rotor = new THREE.Mesh(
        new THREE.BoxGeometry(0.24, 0.02, 0.05),
        new THREE.MeshBasicMaterial({ color: 0xe0f2fe })
      );
      rotor.position.set(ox, 0.14, oz);
      group.add(rotor);
      this.rotors.push(rotor);
    }
    group.position.set(0, 2.2, 0);
    return group;
  }

  _createWindParticles() {
    const count = 140;
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 13;
      positions[i * 3 + 1] = 0.8 + Math.random() * 3.8;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 12;
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    const mat = new THREE.PointsMaterial({ color: 0x7dd3fc, size: 0.09, transparent: true, opacity: 0.55 });
    return new THREE.Points(geo, mat);
  }

  _createEmberParticles() {
    const count = 90;
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      positions[i * 3] = 0;
      positions[i * 3 + 1] = -10;
      positions[i * 3 + 2] = 0;
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    const mat = new THREE.PointsMaterial({ color: 0xfb923c, size: 0.13, transparent: true, opacity: 0.88 });
    this.emberSeeds = Array.from({ length: count }, () => ({
      x: 0, z: 0, speed: 0.7 + Math.random() * 1.1, phase: Math.random() * 6.28, active: false
    }));
    return new THREE.Points(geo, mat);
  }

  _bindEvents() {
    this.canvas.addEventListener("pointerdown", (e) => {
      this.dragging = true;
      this.dragMoved = false;
      this.lastMouse = { x: e.clientX, y: e.clientY };
    });
    window.addEventListener("pointerup", () => { this.dragging = false; });
    window.addEventListener("pointermove", (e) => {
      if (!this.dragging) return;
      const dx = e.clientX - this.lastMouse.x;
      const dy = e.clientY - this.lastMouse.y;
      if (Math.abs(dx) + Math.abs(dy) > 3) this.dragMoved = true;
      this.lastMouse = { x: e.clientX, y: e.clientY };
      this.orbit.theta -= dx * 0.007;
      this.orbit.phi = Math.max(0.32, Math.min(1.42, this.orbit.phi - dy * 0.006));
      this._updateCamera();
    });
    this.canvas.addEventListener("wheel", (e) => {
      e.preventDefault();
      this.orbit.radius = Math.max(8.5, Math.min(26, this.orbit.radius + e.deltaY * 0.01));
      this._updateCamera();
    }, { passive: false });
    this.canvas.addEventListener("click", (e) => {
      if (this.dragMoved) return;
      const rect = this.canvas.getBoundingClientRect();
      this.pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      this.pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      this.raycaster.setFromCamera(this.pointer, this.camera);
      const hits = this.raycaster.intersectObjects(this.tileMeshes, false);
      if (hits.length > 0 && hits[0].object.userData) {
        const { row, col } = hits[0].object.userData;
        this.onSelectCell(row, col);
      }
    });
    window.addEventListener("resize", () => this.resize());
  }

  resize() {
    if (!this.available) return;
    const parent = this.canvas.parentElement;
    if (!parent) return;
    const w = parent.clientWidth || 720;
    const h = parent.clientHeight || 500;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h, false);
  }

  resetCamera() {
    this.orbit = { theta: 0.58, phi: 0.86, radius: 15.8, targetY: 0.4 };
    this._updateCamera();
  }

  _updateCamera() {
    const { theta, phi, radius, targetY } = this.orbit;
    this.camera.position.set(
      radius * Math.sin(phi) * Math.sin(theta),
      radius * Math.cos(phi) + targetY,
      radius * Math.sin(phi) * Math.cos(theta)
    );
    this.camera.lookAt(0, targetY, 0);
  }

  _clearGroup(grp) {
    while (grp.children.length > 0) {
      const obj = grp.children[0];
      grp.remove(obj);
      if (obj.geometry) obj.geometry.dispose();
      if (obj.material) {
        if (Array.isArray(obj.material)) obj.material.forEach((m) => m.dispose());
        else obj.material.dispose();
      }
    }
  }

  updateScene(data, selectedCell, exploredLimit = null) {
    if (!this.available || !data) return;
    this._clearGroup(this.tilesGroup);
    this._clearGroup(this.pathsGroup);
    this._clearGroup(this.effectsGroup);
    this._clearGroup(this.exploredGroup);
    this.tileMeshes = [];
    this.flameMeshes = [];
    this.beaconRings = [];

    const grid = data.grid;
    const hotCoords = [];

    for (let r = 0; r < grid.length; r++) {
      for (let c = 0; c < grid[r].length; c++) {
        const cell = grid[r][c];
        const height = cell.obstacle
          ? 1.55
          : 0.22 + cell.elevation * 0.42 + cell.risk * 1.15;

        const colorHex = riskToColorHex(cell.risk, cell.obstacle);
        const geo = new THREE.BoxGeometry(0.95, height, 0.95);
        const mat = new THREE.MeshStandardMaterial({
          color: colorHex,
          roughness: cell.obstacle ? 0.85 : 0.48,
          metalness: cell.obstacle ? 0.2 : 0.12,
          emissive: cell.risk > 0.55 && !cell.obstacle ? colorHex : 0x000000,
          emissiveIntensity: cell.risk > 0.55 && !cell.obstacle ? (cell.risk - 0.45) * 0.85 : 0.0,
        });
        const mesh = new THREE.Mesh(geo, mat);
        const pos = this.gridToWorld(r, c, height / 2);
        mesh.position.copy(pos);
        mesh.userData = { row: r, col: c, topY: height };
        this.tilesGroup.add(mesh);
        this.tileMeshes.push(mesh);

        // Glowing flame cone on high-risk wildfire cells
        if (!cell.obstacle && cell.risk >= Math.max(0.50, data.meta.tau + 0.12)) {
          const coneGeo = new THREE.ConeGeometry(0.24 * cell.risk + 0.10, 0.72 * cell.risk, 6);
          const coneMat = new THREE.MeshBasicMaterial({
            color: cell.risk > 0.78 ? 0xf97316 : 0xfacc15,
            transparent: true,
            opacity: 0.82,
          });
          const flame = new THREE.Mesh(coneGeo, coneMat);
          flame.position.set(pos.x, height + 0.32 * cell.risk, pos.z);
          flame.userData = { baseY: flame.position.y, phase: (r * 7 + c * 13) * 0.4 };
          this.effectsGroup.add(flame);
          this.flameMeshes.push(flame);
          hotCoords.push({ x: pos.x, z: pos.z, y: height });
        }
      }
    }

    // Bind ember particles to actual burning sectors
    for (let i = 0; i < this.emberSeeds.length; i++) {
      if (hotCoords.length > 0) {
        const hc = hotCoords[i % hotCoords.length];
        this.emberSeeds[i].x = hc.x + (Math.random() - 0.5) * 0.55;
        this.emberSeeds[i].z = hc.z + (Math.random() - 0.5) * 0.55;
        this.emberSeeds[i].baseY = hc.y;
        this.emberSeeds[i].active = true;
      } else {
        this.emberSeeds[i].active = false;
      }
    }

    // Watchtower Sensor markers (if any Bayesian updates active)
    for (const ev of (data.ml.bayes_sensor_updates || [])) {
      const cell = grid[ev.row][ev.col];
      const topY = 0.22 + cell.elevation * 0.42 + cell.risk * 1.15;
      const towerPos = this.gridToWorld(ev.row, ev.col, topY + 0.45);
      const tower = new THREE.Mesh(
        new THREE.CylinderGeometry(0.08, 0.14, 0.9, 8),
        new THREE.MeshStandardMaterial({ color: ev.alert ? 0xfacc15 : 0x38bdf8, emissive: ev.alert ? 0xf59e0b : 0x0284c7, emissiveIntensity: 0.7 })
      );
      tower.position.copy(towerPos);
      this.effectsGroup.add(tower);
    }

    // Start (Base) & Goal (Settlement) beacons
    this._addBeacon(data.meta.start[0], data.meta.start[1], grid, 0x38bdf8);
    this._addBeacon(data.meta.goal[0], data.meta.goal[1], grid, 0x22c55e);

    // Explored nodes overlay (A* expanded order)
    if (state.showExplored && data.search.astar.expanded_order) {
      const exp = data.search.astar.expanded_order;
      const limit = exploredLimit === null ? exp.length : Math.min(exploredLimit, exp.length);
      for (let i = 0; i < limit; i++) {
        const [er, ec] = exp[i];
        const cell = grid[er][ec];
        const topY = 0.22 + cell.elevation * 0.42 + cell.risk * 1.15;
        const pad = new THREE.Mesh(
          new THREE.BoxGeometry(0.76, 0.05, 0.76),
          new THREE.MeshBasicMaterial({ color: 0xa78bfa, transparent: true, opacity: 0.42 })
        );
        pad.position.copy(this.gridToWorld(er, ec, topY + 0.04));
        this.exploredGroup.add(pad);
      }
    }

    // Draw Paths (BFS red, UCS cyan, A* bright emerald)
    if (state.showBfs && data.search.bfs.found) {
      this._addPathRibbon(data.search.bfs.path, grid, 0xf43f5e, 0.36, 0.065);
    }
    if (state.showUcs && data.search.ucs.found) {
      this._addPathRibbon(data.search.ucs.path, grid, 0x38bdf8, 0.56, 0.055);
    }
    if (state.showAstar && data.search.astar.found) {
      this._addPathRibbon(data.search.astar.path, grid, 0x22c55e, 0.48, 0.095);
    }

    // Update selection ring
    if (selectedCell) {
      const [sr, sc] = selectedCell;
      const cell = grid[sr][sc];
      const topY = cell.obstacle ? 1.55 : 0.22 + cell.elevation * 0.42 + cell.risk * 1.15;
      this.selectionRing.position.copy(this.gridToWorld(sr, sc, topY + 0.1));
    }
  }

  _addBeacon(r, c, grid, colorHex) {
    const cell = grid[r][c];
    const topY = 0.22 + cell.elevation * 0.42 + cell.risk * 1.15;
    const pos = this.gridToWorld(r, c, topY);

    const beam = new THREE.Mesh(
      new THREE.CylinderGeometry(0.11, 0.16, 1.85, 12),
      new THREE.MeshBasicMaterial({ color: colorHex, transparent: true, opacity: 0.65 })
    );
    beam.position.set(pos.x, topY + 0.92, pos.z);
    this.effectsGroup.add(beam);

    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(0.46, 0.045, 8, 28),
      new THREE.MeshBasicMaterial({ color: colorHex })
    );
    ring.rotation.x = Math.PI / 2;
    ring.position.set(pos.x, topY + 0.18, pos.z);
    this.effectsGroup.add(ring);
    this.beaconRings.push(ring);
  }

  _addPathRibbon(path, grid, colorHex, yOffset, radius) {
    if (!path || path.length < 2) return;
    const pts = path.map(([r, c]) => {
      const cell = grid[r][c];
      const topY = 0.22 + cell.elevation * 0.42 + cell.risk * 1.15;
      return this.gridToWorld(r, c, topY + yOffset);
    });
    const curve = new THREE.CatmullRomCurve3(pts, false, "catmullrom", 0.25);
    const tubeGeo = new THREE.TubeGeometry(curve, path.length * 6, radius, 8, false);
    const tubeMat = new THREE.MeshStandardMaterial({
      color: colorHex,
      emissive: colorHex,
      emissiveIntensity: 0.65,
      roughness: 0.3,
    });
    this.pathsGroup.add(new THREE.Mesh(tubeGeo, tubeMat));
  }

  _animate() {
    if (!this.available) return;
    requestAnimationFrame(() => this._animate());
    if (state.renderMode !== "3d" || state.activeTab !== "mission") return;
    const dt = Math.min(this.clock.getDelta(), 0.05);
    const t = this.clock.elapsedTime;

    // Flicker wildfire flame cones
    for (const flame of this.flameMeshes) {
      const ph = flame.userData.phase;
      const s = 0.88 + 0.24 * Math.sin(t * 7.5 + ph);
      flame.scale.set(0.95, s, 0.95);
      flame.position.y = flame.userData.baseY + 0.06 * Math.sin(t * 6.0 + ph);
    }

    // Pulse beacon rings
    for (const ring of this.beaconRings) {
      const sc = 0.92 + 0.14 * Math.sin(t * 3.2);
      ring.scale.set(sc, sc, 1);
    }

    // Spin rescue drone rotors & fly smoothly along A* path
    for (const rot of this.rotors) rot.rotation.y += dt * 18.0;
    if (state.data && state.data.search.astar.found && state.data.search.astar.path.length >= 2) {
      this.drone.visible = true;
      const path = state.data.search.astar.path;
      const grid = state.data.grid;
      state.droneProgress = (state.droneProgress + dt * 0.22) % 1.0;
      const fIdx = state.droneProgress * (path.length - 1);
      const i0 = Math.floor(fIdx);
      const i1 = Math.min(path.length - 1, i0 + 1);
      const frac = fIdx - i0;
      const [r0, c0] = path[i0];
      const [r1, c1] = path[i1];
      const y0 = 0.22 + grid[r0][c0].elevation * 0.42 + grid[r0][c0].risk * 1.15 + 1.05;
      const y1 = 0.22 + grid[r1][c1].elevation * 0.42 + grid[r1][c1].risk * 1.15 + 1.05;
      const p0 = this.gridToWorld(r0, c0, y0);
      const p1 = this.gridToWorld(r1, c1, y1);
      this.drone.position.lerpVectors(p0, p1, frac);
      this.drone.position.y += 0.10 * Math.sin(t * 5.0);
    } else {
      this.drone.visible = false;
    }

    // Animate wind particles eastward scaled by wind_level
    const windSpeed = state.data ? 1.2 + state.data.meta.wind_level * 6.5 : 2.5;
    const wPos = this.windParticles.geometry.attributes.position;
    for (let i = 0; i < wPos.count; i++) {
      let x = wPos.getX(i) + dt * windSpeed;
      if (x > 6.5) x = -6.5;
      wPos.setX(i, x);
    }
    wPos.needsUpdate = true;

    // Animate rising fire embers
    const ePos = this.emberParticles.geometry.attributes.position;
    for (let i = 0; i < this.emberSeeds.length; i++) {
      const s = this.emberSeeds[i];
      if (!s.active) {
        ePos.setXYZ(i, 0, -10, 0);
      } else {
        const life = ((t * s.speed + s.phase) % 2.4);
        ePos.setXYZ(i, s.x + life * 0.35 * (state.data ? state.data.meta.wind_level : 0.5), s.baseY + life * 1.15, s.z);
      }
    }
    ePos.needsUpdate = true;

    this.fireLight.intensity = 1.4 + 0.5 * Math.sin(t * 8.0);
    this.renderer.render(this.scene, this.camera);
  }
}

/* ============================================================================
   2D CANVAS FALLBACK RENDERER (Guaranteed reliability on weak GPUs / Rule #9)
   ============================================================================ */
function draw2DGrid(data, selectedCell, exploredLimit = null) {
  const canvas = document.getElementById("canvas-2d");
  if (!canvas || !data) return;
  const parent = canvas.parentElement;
  const w = parent.clientWidth || 700;
  const h = parent.clientHeight || 480;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(w * dpr);
  canvas.height = Math.round(h * dpr);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.fillStyle = "#07101f";
  ctx.fillRect(0, 0, w, h);

  const grid = data.grid;
  const rows = grid.length;
  const cols = grid[0].length;
  const pad = 54;
  const cellPx = Math.min((w - pad * 2) / cols, (h - pad * 2 - 20) / rows);
  const ox = (w - cellPx * cols) / 2;
  const oy = (h - cellPx * rows) / 2;

  canvas._gridMetrics = { ox, oy, cellPx, rows, cols };

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const cell = grid[r][c];
      const x = ox + c * cellPx;
      const y = oy + r * cellPx;
      ctx.fillStyle = riskToCss(cell.risk, cell.obstacle);
      ctx.fillRect(x + 1.5, y + 1.5, cellPx - 3, cellPx - 3);

      ctx.fillStyle = "rgba(248,250,252,0.88)";
      ctx.font = "10px Consolas, monospace";
      ctx.textAlign = "center";
      ctx.fillText(cell.obstacle ? "OBS" : `${Math.round(cell.risk * 100)}%`, x + cellPx / 2, y + cellPx / 2 + 3);
    }
  }

  // Explored overlay
  if (state.showExplored && data.search.astar.expanded_order) {
    const exp = data.search.astar.expanded_order;
    const lim = exploredLimit === null ? exp.length : Math.min(exploredLimit, exp.length);
    ctx.strokeStyle = "rgba(167,139,250,0.75)";
    ctx.lineWidth = 2;
    for (let i = 0; i < lim; i++) {
      const [r, c] = exp[i];
      ctx.strokeRect(ox + c * cellPx + 3, oy + r * cellPx + 3, cellPx - 6, cellPx - 6);
    }
  }

  const drawPath2D = (path, color, width, dash = []) => {
    if (!path || path.length < 2) return;
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.setLineDash(dash);
    ctx.beginPath();
    path.forEach(([r, c], idx) => {
      const x = ox + (c + 0.5) * cellPx;
      const y = oy + (r + 0.5) * cellPx;
      if (idx === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();
    ctx.restore();
  };

  if (state.showBfs && data.search.bfs.found) drawPath2D(data.search.bfs.path, "#f43f5e", 4, [6, 4]);
  if (state.showUcs && data.search.ucs.found) drawPath2D(data.search.ucs.path, "#38bdf8", 3, [2, 3]);
  if (state.showAstar && data.search.astar.found) drawPath2D(data.search.astar.path, "#22c55e", 5);

  // Base (S) & Settlement (G) markers in 2D mode
  const drawMarker = ([mr, mc], label, col) => {
    const cx = ox + (mc + 0.5) * cellPx;
    const cy = oy + (mr + 0.5) * cellPx;
    ctx.fillStyle = col;
    ctx.beginPath();
    ctx.arc(cx, cy, cellPx * 0.28, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#07101f";
    ctx.font = "bold 11px Segoe UI, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(label, cx, cy + 4);
  };
  drawMarker(data.meta.start, "S", "#38bdf8");
  drawMarker(data.meta.goal, "G", "#22c55e");

  if (selectedCell) {
    const [sr, sc] = selectedCell;
    ctx.strokeStyle = "#38bdf8";
    ctx.lineWidth = 3;
    ctx.strokeRect(ox + sc * cellPx + 1, oy + sr * cellPx + 1, cellPx - 2, cellPx - 2);
  }
}

/* ============================================================================
   UI RENDERING & API INTEGRATION
   ============================================================================ */
let scene3D = null;

function stopSearchAnimation() {
  if (state.animTimer) {
    clearInterval(state.animTimer);
    state.animTimer = null;
  }
}

function showApiError(msg) {
  const el = document.getElementById("api-error-banner");
  if (!el) return;
  if (!msg) {
    el.classList.add("hidden");
    el.textContent = "";
    return;
  }
  el.textContent = `⚠ ${msg}`;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 4500);
}

function debouncedFetch(endpoint = "/api/run") {
  if (state.debounceTimer) clearTimeout(state.debounceTimer);
  state.debounceTimer = setTimeout(() => fetchSimulation(endpoint), 80);
}

async function fetchSimulation(endpoint = "/api/run", rollbackFn = null) {
  stopSearchAnimation();
  if (state.fetchAbort) state.fetchAbort.abort();
  state.fetchAbort = new AbortController();

  const payload = {
    preset_id: state.preset_id,
    seed: state.seed,
    risk_lambda: state.risk_lambda,
    gamma: state.gamma,
    tau: state.tau,
    wind_override: state.wind_override,
    resource_level: state.resource_level,
    model_choice: state.model_choice,
    sensor_events: state.sensor_events,
    extra_obstacles: state.extra_obstacles,
    inspect_cell: state.inspect_cell,
  };

  try {
    const resp = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: state.fetchAbort.signal,
    });
    if (!resp.ok) {
      if (rollbackFn) rollbackFn();
      const errTxt = await resp.text();
      showApiError(`Request failed (${resp.status}): ${errTxt.slice(0, 120)}`);
      return;
    }
    showApiError("");
    const data = await resp.json();
    state.data = data;
    renderAll(data);
  } catch (err) {
    if (err && err.name === "AbortError") return;
    if (rollbackFn) rollbackFn();
    showApiError("Cannot reach local SteppeGuard AI server. Ensure python app.py is running.");
  }
}

function renderAll(data) {
  // Sync preset active button cleanly (fixes Visual QA highlight lag)
  document.querySelectorAll(".preset-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.preset === data.meta.preset_id);
  });

  // Sync HUD & sliders
  document.getElementById("hud-scenario-title").textContent = data.meta.title;
  const viewHint = state.renderMode === "3d"
    ? "Drag to orbit · Click sector to inspect"
    : "2D Fallback View · Click sector to inspect";
  document.getElementById("hud-scenario-region").textContent =
    `${data.meta.region} · Wind ${(data.meta.wind_level * 100).toFixed(0)}% · ${viewHint}`;

  document.getElementById("slider-wind").value = data.meta.wind_level.toFixed(2);
  document.getElementById("val-wind").textContent = data.meta.wind_level.toFixed(2);
  document.getElementById("val-tau").textContent = data.meta.tau.toFixed(2);
  document.getElementById("slider-tau").value = data.meta.tau.toFixed(2);

  const [ir, ic] = data.math_inspector.inspected_cell;
  state.inspect_cell = [ir, ic];
  document.getElementById("selected-cell-chip").textContent = `Selected Sector: (${ir}, ${ic})`;
  document.getElementById("math-cell-label").textContent = `Sector (${ir}, ${ic})`;

  // Route blocked banner
  const noPath = document.getElementById("no-path-banner");
  noPath.classList.toggle("hidden", data.search.astar.found);

  // Render 3D or 2D
  if (state.renderMode === "3d" && scene3D && scene3D.available) {
    scene3D.updateScene(data, state.inspect_cell, null);
  } else {
    draw2DGrid(data, state.inspect_cell, null);
  }

  renderMdpPanel(data);
  renderSearchPanel(data);
  renderCellPreview(data);
  renderMathTab(data);
}

function renderMdpPanel(data) {
  const mdp = data.mdp;
  document.getElementById("mdp-iters-badge").textContent = `${mdp.iterations} sweeps`;
  document.getElementById("mdp-rec-action").textContent = mdp.recommended_action;
  document.getElementById("mdp-active-state").textContent =
    `State: ${mdp.active_state_name} · V*(s) = ${mdp.active_v_star.toFixed(2)}`;

  const activeRow = mdp.states[mdp.active_state_index];
  const entries = Object.entries(activeRow.q_values);
  const vals = entries.map(([, v]) => v);
  const minV = Math.min(...vals, -40);
  const maxV = Math.max(...vals, 10);
  const span = Math.max(1, maxV - minV);

  const barsEl = document.getElementById("mdp-q-bars");
  barsEl.innerHTML = entries.map(([action, qv]) => {
    const isBest = action === mdp.recommended_action;
    const pct = Math.max(5, Math.min(100, ((qv - minV) / span) * 100));
    const col = isBest ? "#22c55e" : "#38bdf8";
    return `
      <div class="q-row ${isBest ? "best" : ""}">
        <span>${action}</span>
        <div class="q-track"><div class="q-fill" style="width:${pct}%;background:${col}"></div></div>
        <span class="mono" style="text-align:right">${qv.toFixed(1)}</span>
      </div>`;
  }).join("");

  const decisionKey = `${data.meta.preset_id}:${mdp.active_state_name}:${mdp.recommended_action}`;
  const saved = state.hitlDecisions[decisionKey];
  if (saved) {
    document.getElementById("hitl-status").innerHTML = saved;
  } else {
    document.getElementById("hitl-status").textContent =
      `Status: Awaiting dispatcher approval for "${mdp.recommended_action}"`;
  }
}

function renderSearchPanel(data) {
  const s = data.search;
  const badge = document.getElementById("search-savings-badge");
  const redPct = s.summary.exposure_reduction_vs_bfs_pct;
  badge.textContent = redPct > 0 ? `-${redPct}% fire risk` : "Same corridor";

  const rows = [
    { key: "astar", cls: "row-astar", label: "A* (Ours)", d: s.astar },
    { key: "ucs", cls: "", label: "UCS (h=0)", d: s.ucs },
    { key: "bfs", cls: "row-bfs", label: "BFS", d: s.bfs },
  ];
  document.getElementById("search-table-body").innerHTML = rows.map((r) => `
    <tr class="${r.cls}">
      <td>${r.label}</td>
      <td>${r.d.expanded_count}</td>
      <td>${r.d.found ? r.d.total_cost.toFixed(2) : "—"}</td>
      <td>${r.d.found ? r.d.total_exposure.toFixed(2) : "—"}</td>
    </tr>
  `).join("");

  document.getElementById("search-insight").textContent = s.astar.found
    ? `A* matched UCS's exact optimal cost while expanding ${s.summary.nodes_saved_vs_ucs} fewer nodes.`
    : "No ground corridor available under current obstacle placement.";
}

function renderCellPreview(data) {
  const [r, c] = data.math_inspector.inspected_cell;
  const cell = data.grid[r][c];
  const badge = document.getElementById("cell-risk-badge");
  badge.textContent = `P = ${(cell.risk * 100).toFixed(1)}%`;
  badge.className = `badge ${cell.risk >= data.meta.tau ? "badge-red" : "badge-green"}`;

  const f = cell.features;
  const trace = data.math_inspector.search_step.astar_trace;
  const traceStr = trace
    ? `g=${trace.g.toFixed(2)}, h=${trace.h.toFixed(2)}, f=${trace.f.toFixed(2)}`
    : "Not expanded by A*";

  document.getElementById("cell-preview-body").innerHTML = `
    <div><strong>Sector (${r},${c})</strong> · ${cell.terrain_name}</div>
    <div class="mono" style="font-size:10.8px;color:#94a3b8;">
      Temp ${f.temperature_c.toFixed(1)}°C · Hum ${f.humidity_pct.toFixed(0)}% · Wind ${f.wind_kmh.toFixed(0)} km/h · Dry ${f.dryness_index.toFixed(2)}
    </div>
    <div class="preview-formula">${data.math_inspector.ml_step.formula}</div>
    <div class="preview-formula">${data.math_inspector.search_step.formula}<br/>A* node: ${traceStr}</div>
  `;

  const bBox = document.getElementById("bayes-live-box");
  const updates = data.ml.bayes_sensor_updates || [];
  if (updates.length > 0) {
    const last = updates[updates.length - 1];
    bBox.classList.remove("hidden");
    bBox.innerHTML = `<strong>📡 Live Bayes Update at (${last.row},${last.col}):</strong><br/><span class="mono">${last.formula}</span>`;
  } else {
    bBox.classList.add("hidden");
  }
}

function renderMathTab(data) {
  const ml = data.math_inspector.ml_step;
  document.getElementById("math-ml-model-badge").textContent = ml.model || "Logistic Regression";
  document.getElementById("math-ml-formula").textContent = ml.formula;
  document.getElementById("math-ml-terms").innerHTML = ml.terms.map((t) => `
    <tr>
      <td>${t.feature}</td>
      <td>${t.raw_value.toFixed(2)}</td>
      <td>${t.standardized.toFixed(2)}</td>
      <td>${t.weight.toFixed(3)}</td>
      <td>${t.contribution >= 0 ? "+" : ""}${t.contribution.toFixed(3)}</td>
    </tr>
  `).join("");
  document.getElementById("math-ml-explain").textContent = ml.explanation;

  const mb = document.getElementById("math-bayes-section");
  const updates = data.ml.bayes_sensor_updates || [];
  if (updates.length > 0) {
    const last = updates[updates.length - 1];
    mb.classList.remove("hidden");
    mb.innerHTML = `<strong>Week 6 Bayesian Watchtower Sensor Update at (${last.row},${last.col}):</strong><br/>${last.formula}<br/><em>${last.explanation}</em>`;
  } else {
    mb.classList.add("hidden");
  }

  // Topic 2
  const ss = data.math_inspector.search_step;
  document.getElementById("math-search-formula").textContent = ss.formula;
  document.getElementById("math-cmin").textContent = `c_min = ${data.search.astar.c_min_used.toFixed(3)}`;
  const tr = ss.astar_trace;
  document.getElementById("math-search-node").innerHTML = `
    <div class="kv-item"><div class="k">g(n) · Cost So Far</div><div class="v">${tr ? tr.g.toFixed(2) : "—"}</div></div>
    <div class="kv-item"><div class="k">h(n) · Admissible Heuristic</div><div class="v">${tr ? tr.h.toFixed(2) : "—"}</div></div>
    <div class="kv-item"><div class="k">f(n) = g(n) + h(n)</div><div class="v">${tr ? tr.f.toFixed(2) : "—"}</div></div>
  `;

  // Topic 3
  const mdp = data.mdp;
  document.getElementById("math-mdp-badge").textContent = `γ = ${mdp.gamma.toFixed(2)} · ${mdp.iterations} sweeps`;
  document.getElementById("math-mdp-formula").textContent = data.math_inspector.mdp_step.formula;

  document.getElementById("math-mdp-table").innerHTML = mdp.states.map((st) => `
    <tr class="${st.is_active ? "active-state-row" : ""}">
      <td>${st.short_name}${st.is_active ? " ★" : ""}</td>
      <td>${st.v_star.toFixed(1)}</td>
      <td style="color:${st.is_terminal ? "#94a3b8" : "#86efac"}">${st.best_action}</td>
      <td>${st.is_terminal ? "—" : st.q_values["Monitor"].toFixed(1)}</td>
      <td>${st.is_terminal ? "—" : st.q_values["Direct Dispatch"].toFixed(1)}</td>
      <td>${st.is_terminal ? "—" : st.q_values["Safe Detour"].toFixed(1)}</td>
      <td>${st.is_terminal ? "—" : st.q_values["Aerial Retardant"].toFixed(1)}</td>
      <td>${st.is_terminal ? "—" : st.q_values["Evacuate / Hold"].toFixed(1)}</td>
    </tr>
  `).join("");

  document.getElementById("math-bellman-body").innerHTML = mdp.active_bellman_breakdown.map((b) => `
    <tr>
      <td>${b.next_state}</td>
      <td>${b.prob.toFixed(3)}</td>
      <td>${b.reward.toFixed(1)}</td>
      <td>${b.v_next.toFixed(1)}</td>
      <td>${b.contribution >= 0 ? "+" : ""}${b.contribution.toFixed(2)}</td>
    </tr>
  `).join("");

  const sens = mdp.gamma_sensitivity || [];
  const baseMed = sens.length ? sens[0].policies["Med / HighRes"] : "";
  document.getElementById("math-gamma-body").innerHTML = sens.map((row) => {
    const flipped = row.policies["Med / HighRes"] !== baseMed;
    return `
      <tr class="${flipped ? "flip-row" : ""}">
        <td>${row.gamma.toFixed(2)}</td>
        <td>${row.iterations}</td>
        <td>${row.policies["Low / HighRes"]}</td>
        <td>${row.policies["Med / HighRes"]}</td>
        <td>${row.policies["High / HighRes"]}</td>
        <td>${row.policies["High / LowRes"]}</td>
      </tr>
    `;
  }).join("");
}

async function loadBenchmarks() {
  if (state.benchmarksLoaded) return;
  const kpiEl = document.getElementById("benchmark-kpis");
  try {
    const resp = await fetch("/api/benchmarks");
    if (!resp.ok) {
      kpiEl.innerHTML = `<div class="kpi-card"><div class="kpi-label">Benchmarks Unavailable</div><div class="kpi-sub">Run <code>python scripts/benchmark.py</code> to generate 30-seed results.</div></div>`;
      return;
    }
    const bm = await resp.json();
    state.benchmarksLoaded = true;

    const lr = bm.ml.logistic_regression_tuned;
    const ab = bm.search.abai_high_wind;
    const bfsExp = ab.bfs.exposure.mean || 1e-9;
    const ucsExp = ab.ucs.expanded.mean || 1e-9;
    const riskCut = ((ab.bfs.exposure.mean - ab.astar.exposure.mean) / bfsExp) * 100;
    const nodeCut = ((ab.ucs.expanded.mean - ab.astar.expanded.mean) / ucsExp) * 100;

    kpiEl.innerHTML = `
      <div class="kpi-card">
        <div class="kpi-label">ML Wildfire Recall (30 Seeds)</div>
        <div class="kpi-val">${(lr.recall.mean * 100).toFixed(1)}%</div>
        <div class="kpi-sub">F1 ${(lr.f1.mean * 100).toFixed(1)}% · Brier ${lr.brier_score.mean.toFixed(3)} (base ~0.22)</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">A* Fire Exposure Cut vs BFS</div>
        <div class="kpi-val">-${riskCut.toFixed(1)}%</div>
        <div class="kpi-sub">Abai: ${ab.astar.exposure.mean.toFixed(2)} vs BFS ${ab.bfs.exposure.mean.toFixed(2)}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">A* Nodes Saved vs UCS</div>
        <div class="kpi-val">-${nodeCut.toFixed(1)}%</div>
        <div class="kpi-sub">${ab.astar.expanded.mean.toFixed(1)} vs ${ab.ucs.expanded.mean.toFixed(1)} nodes (exact same cost)</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">MDP Bellman Convergence</div>
        <div class="kpi-val">${bm.mdp.iterations} sweeps</div>
        <div class="kpi-sub">Tolerance θ = 10⁻⁶ · γ policy flip verified</div>
      </div>
    `;
  } catch (err) {
    kpiEl.innerHTML = `<div class="kpi-card"><div class="kpi-label">Error Loading Benchmarks</div><div class="kpi-sub">Could not reach /api/benchmarks.</div></div>`;
  }
}

function startSearchAnimation() {
  if (!state.data || !state.data.search.astar.expanded_order) return;
  if (state.animTimer) clearInterval(state.animTimer);
  const total = state.data.search.astar.expanded_order.length;
  let step = 1;
  state.showExplored = true;
  document.getElementById("chk-explored").checked = true;
  state.droneProgress = 0;

  state.animTimer = setInterval(() => {
    if (state.renderMode === "3d" && scene3D && scene3D.available) {
      scene3D.updateScene(state.data, state.inspect_cell, step);
    } else {
      draw2DGrid(state.data, state.inspect_cell, step);
    }
    step += Math.max(1, Math.ceil(total / 24));
    if (step >= total) {
      clearInterval(state.animTimer);
      state.animTimer = null;
      if (state.renderMode === "3d" && scene3D && scene3D.available) {
        scene3D.updateScene(state.data, state.inspect_cell, null);
      } else {
        draw2DGrid(state.data, state.inspect_cell, null);
      }
    }
  }, 55);
}

/* ============================================================================
   EVENT WIRING & INITIALIZATION
   ============================================================================ */
document.addEventListener("DOMContentLoaded", () => {
  const onSelectCell = (row, col) => {
    state.inspect_cell = [row, col];
    fetchSimulation();
  };

  scene3D = new Steppe3DScene(document.getElementById("canvas-3d"), onSelectCell);
  if (!scene3D.available) {
    state.renderMode = "2d";
    document.getElementById("canvas-3d").classList.add("hidden");
    document.getElementById("canvas-2d").classList.remove("hidden");
    document.getElementById("btn-render-mode").textContent = "2D Mode (No WebGL)";
  }

  // 2D click support
  document.getElementById("canvas-2d").addEventListener("click", (e) => {
    const c2d = e.currentTarget;
    if (!c2d._gridMetrics) return;
    const rect = c2d.getBoundingClientRect();
    const { ox, oy, cellPx, rows, cols } = c2d._gridMetrics;
    const col = Math.floor((e.clientX - rect.left - ox) / cellPx);
    const row = Math.floor((e.clientY - rect.top - oy) / cellPx);
    if (row >= 0 && row < rows && col >= 0 && col < cols) onSelectCell(row, col);
  });

  // Tabs
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      stopSearchAnimation();
      document.querySelectorAll(".tab-btn").forEach((b) => { b.classList.remove("active"); b.setAttribute("aria-selected", "false"); });
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
      state.activeTab = btn.dataset.tab;
      document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
      if (btn.dataset.tab === "benchmarks") loadBenchmarks();
      if (btn.dataset.tab === "mission" && scene3D) setTimeout(() => scene3D.resize(), 40);
    });
  });

  // Helper to sync toggles & sliders to clean preset defaults
  const syncControlsUI = () => {
    document.querySelectorAll("#model-toggle .seg-btn").forEach((b) => b.classList.toggle("active", b.dataset.value === state.model_choice));
    document.querySelectorAll("#resource-toggle .seg-btn").forEach((b) => b.classList.toggle("active", b.dataset.value === state.resource_level));
    document.getElementById("slider-lambda").value = state.risk_lambda.toFixed(1);
    document.getElementById("val-lambda").textContent = state.risk_lambda.toFixed(1);
    document.getElementById("slider-gamma").value = state.gamma.toFixed(2);
    document.getElementById("val-gamma").textContent = state.gamma.toFixed(2);
    document.getElementById("input-seed").value = String(state.seed);
  };

  // Presets (clean reset so each preset matches its card description reliably!)
  document.querySelectorAll(".preset-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.preset_id = btn.dataset.preset;
      state.wind_override = null;
      state.risk_lambda = 3.5;
      state.gamma = 0.90;
      state.tau = null;
      state.resource_level = "High";
      state.model_choice = "logistic_regression";
      state.sensor_events = [];
      state.extra_obstacles = [];
      state.inspect_cell = null;
      syncControlsUI();
      fetchSimulation();
    });
  });

  // Segmented toggles
  document.querySelectorAll("#model-toggle .seg-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#model-toggle .seg-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state.model_choice = btn.dataset.value;
      state.tau = null;
      fetchSimulation();
    });
  });

  document.querySelectorAll("#resource-toggle .seg-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#resource-toggle .seg-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state.resource_level = btn.dataset.value;
      fetchSimulation();
    });
  });

  // Sliders (debounced + AbortController prevents out-of-order stale updates)
  document.getElementById("slider-wind").addEventListener("input", (e) => {
    state.wind_override = parseFloat(e.target.value);
    document.getElementById("val-wind").textContent = state.wind_override.toFixed(2);
    debouncedFetch();
  });
  document.getElementById("slider-lambda").addEventListener("input", (e) => {
    state.risk_lambda = parseFloat(e.target.value);
    document.getElementById("val-lambda").textContent = state.risk_lambda.toFixed(1);
    debouncedFetch();
  });
  document.getElementById("slider-gamma").addEventListener("input", (e) => {
    state.gamma = parseFloat(e.target.value);
    document.getElementById("val-gamma").textContent = state.gamma.toFixed(2);
    debouncedFetch();
  });
  document.getElementById("slider-tau").addEventListener("input", (e) => {
    state.tau = parseFloat(e.target.value);
    document.getElementById("val-tau").textContent = state.tau.toFixed(2);
    debouncedFetch();
  });
  document.getElementById("input-seed").addEventListener("change", (e) => {
    state.seed = Math.max(0, Math.min(9999, parseInt(e.target.value || "42", 10)));
    fetchSimulation();
  });

  document.getElementById("btn-reset-all").addEventListener("click", () => {
    state.seed = 42; state.risk_lambda = 3.5; state.gamma = 0.90; state.tau = null;
    state.wind_override = null; state.resource_level = "High"; state.model_choice = "logistic_regression";
    state.sensor_events = []; state.extra_obstacles = [];
    syncControlsUI();
    fetchSimulation();
  });

  // Sector interactive actions (with safe rollback on failure + sensor list cap)
  document.getElementById("btn-sensor-alert").addEventListener("click", () => {
    const [r, c] = state.inspect_cell || [5, 5];
    if (state.sensor_events.length >= 25) state.sensor_events.shift();
    state.sensor_events.push({ row: r, col: c, alert: true });
    fetchSimulation("/api/sensor", () => state.sensor_events.pop());
  });
  document.getElementById("btn-sensor-clear").addEventListener("click", () => {
    const [r, c] = state.inspect_cell || [5, 5];
    if (state.sensor_events.length >= 25) state.sensor_events.shift();
    state.sensor_events.push({ row: r, col: c, alert: false });
    fetchSimulation("/api/sensor", () => state.sensor_events.pop());
  });
  document.getElementById("btn-toggle-obs").addEventListener("click", () => {
    const [r, c] = state.inspect_cell || [5, 5];
    const start = state.data ? state.data.meta.start : [5, 0];
    const goal = state.data ? state.data.meta.goal : [5, 9];
    if ((r === start[0] && c === start[1]) || (r === goal[0] && c === goal[1])) {
      showApiError("Cannot place an obstacle on Base or Settlement.");
      return;
    }
    const idx = state.extra_obstacles.findIndex(([er, ec]) => er === r && ec === c);
    if (idx >= 0) {
      const removed = state.extra_obstacles.splice(idx, 1)[0];
      fetchSimulation("/api/run", () => state.extra_obstacles.push(removed));
    } else {
      state.extra_obstacles.push([r, c]);
      fetchSimulation("/api/run", () => state.extra_obstacles.pop());
    }
  });
  document.getElementById("btn-clear-edits").addEventListener("click", () => {
    state.sensor_events = [];
    state.extra_obstacles = [];
    fetchSimulation();
  });

  // Viewport controls
  document.getElementById("btn-play-anim").addEventListener("click", startSearchAnimation);
  document.getElementById("btn-reset-cam").addEventListener("click", () => scene3D && scene3D.resetCamera());
  document.getElementById("btn-render-mode").addEventListener("click", (e) => {
    stopSearchAnimation();
    if (state.renderMode === "3d") {
      state.renderMode = "2d";
      document.getElementById("canvas-3d").classList.add("hidden");
      document.getElementById("canvas-2d").classList.remove("hidden");
      e.target.textContent = "Switch to 3D";
      if (state.data) renderAll(state.data);
    } else if (scene3D && scene3D.available) {
      state.renderMode = "3d";
      document.getElementById("canvas-2d").classList.add("hidden");
      document.getElementById("canvas-3d").classList.remove("hidden");
      e.target.textContent = "Switch to 2D";
      scene3D.resize();
      if (state.data) renderAll(state.data);
    }
  });

  // Path visibility checkboxes
  for (const [id, key] of [["chk-astar", "showAstar"], ["chk-bfs", "showBfs"], ["chk-ucs", "showUcs"], ["chk-explored", "showExplored"]]) {
    document.getElementById(id).addEventListener("change", (e) => {
      state[key] = e.target.checked;
      if (state.data) renderAll(state.data);
    });
  }

  // Human-in-the-loop buttons (persisted per state+action in session)
  document.getElementById("btn-hitl-confirm").addEventListener("click", () => {
    if (!state.data) return;
    const mdp = state.data.mdp;
    const key = `${state.data.meta.preset_id}:${mdp.active_state_name}:${mdp.recommended_action}`;
    const msg = `<span style="color:#86efac;font-weight:700;">✓ Approved by Dispatcher:</span> Executing "${mdp.recommended_action}"`;
    state.hitlDecisions[key] = msg;
    document.getElementById("hitl-status").innerHTML = msg;
  });
  document.getElementById("btn-hitl-override").addEventListener("click", () => {
    if (!state.data) return;
    const mdp = state.data.mdp;
    const key = `${state.data.meta.preset_id}:${mdp.active_state_name}:${mdp.recommended_action}`;
    const msg = `<span style="color:#fcd34d;font-weight:700;">✋ Human Override Active:</span> AI "${mdp.recommended_action}" held for manual dispatch`;
    state.hitlDecisions[key] = msg;
    document.getElementById("hitl-status").innerHTML = msg;
  });

  // Initial load
  fetchSimulation();
});
