import os
import json
import math
from flask import Flask, render_template_string, jsonify
from src.metrica_parser import MetricaTrackingParser
from src.pipeline import FullPossessionPipeline

app = Flask(__name__)

# Initialize pipeline and parse match data
parser = MetricaTrackingParser()
pipeline = FullPossessionPipeline()

MATCH_CATALOG = {
    "MATCH_EL_CLASICO": {
        "id": "MATCH_EL_CLASICO",
        "title": "⚽ Match 1: FC Barcelona vs Real Madrid CF (Camp Nou - 32' Wing Overload & Top Corner Goal)",
        "file": "data/match_el_clasico.json"
    },
    "MATCH_UCL_TACTICAL": {
        "id": "MATCH_UCL_TACTICAL",
        "title": "🏆 Match 2: Manchester City vs Inter Milan (UCL Final - 67' Midfield Press & Counter)",
        "file": "data/match_ucl_tactical.json"
    },
    "MATCH_WORLD_CUP": {
        "id": "MATCH_WORLD_CUP",
        "title": "🌍 Match 3: Argentina vs France (World Cup Final - 88' Rapid Counter & Bullet Strike)",
        "file": "data/match_world_cup.json"
    }
}

MATCH_CACHE = {}

def process_match_file(filepath):
    if not os.path.exists(filepath):
        filepath = "data/sample_match_tracking.json"
    frames = parser.load_json_match(filepath) if os.path.exists(filepath) else []
    
    pipe = FullPossessionPipeline()
    p_frames = []
    h_cnt = 0
    a_cnt = 0
    t_overs = []
    l_team = None

    for f in frames:
        res = pipe.process_frame(f)
        team = res.get("smoothed_team")
        if team == "Home":
            h_cnt += 1
        elif team == "Away":
            a_cnt += 1

        if l_team and team and team != l_team and team != "Contested":
            t_overs.append({
                "frame_id": f["frame_id"],
                "match_time": f.get("match_time", "14:00"),
                "from": l_team,
                "to": team
            })
        if team and team != "Contested":
            l_team = team

        p_frames.append({
            "frame_id": f["frame_id"],
            "match_time": f.get("match_time", "14:00"),
            "ball": f["ball"],
            "players": f["players"],
            "possession": res
        })

    t_frames = max(1, len(frames))
    return {
        "frames": p_frames,
        "total_frames": t_frames,
        "home_pct": (h_cnt / t_frames) * 100.0,
        "away_pct": (a_cnt / t_frames) * 100.0,
        "turnovers": t_overs
    }

print("Pre-calculating telemetry for official match catalog...")
for m_key, m_info in MATCH_CATALOG.items():
    MATCH_CACHE[m_key] = process_match_file(m_info["file"])
    print(f"Loaded {m_info['title']}: {MATCH_CACHE[m_key]['total_frames']} frames")

DEFAULT_MATCH_ID = "MATCH_EL_CLASICO"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Barça Innovation Hub · 3D Interactive Tactical Pitch & Kinematics Engine</title>
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>⚽</text></svg>">
  <!-- Three.js & OrbitControls locally hosted with cache buster -->
  <script src="/static/js/three.min.js?v=2.0"></script>
  <script src="/static/js/OrbitControls.js?v=2.0"></script>
  <style>
    :root {
      --bg: #06080d;
      --card: rgba(15, 20, 32, 0.88);
      --border: rgba(255, 255, 255, 0.08);
      --accent: #10b981;
      --home: #ef4444;
      --away: #3b82f6;
      --ball: #ffffff;
      --text: #f3f4f6;
      --text-muted: #9ca3af;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: 'Plus Jakarta Sans', sans-serif;
      min-height: 100vh;
      padding: 20px 24px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 14px 22px;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      backdrop-filter: blur(12px);
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: var(--accent);
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 600;
    }
    .view-toggle {
      display: inline-flex;
      background: rgba(0, 0, 0, 0.4);
      padding: 3px;
      border-radius: 8px;
      border: 1px solid var(--border);
    }
    .view-btn {
      padding: 5px 14px;
      border-radius: 6px;
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }
    .view-btn.active {
      background: var(--accent);
      color: #000;
    }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 14px;
    }
    .stat-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px 16px;
    }
    .stat-label {
      font-size: 0.74rem;
      color: var(--text-muted);
      text-transform: uppercase;
      font-family: 'JetBrains Mono', monospace;
      margin-bottom: 4px;
    }
    .stat-val {
      font-size: 1.5rem;
      font-weight: 800;
      letter-spacing: -0.02em;
    }
    .main-grid {
      display: grid;
      grid-template-columns: 1fr 340px;
      gap: 16px;
    }
    .viewport-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      position: relative;
    }
    .view-stage {
      width: 100%;
      height: 520px;
      position: relative;
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid var(--border);
      background: #040608;
    }
    #three-canvas-container {
      width: 100%;
      height: 100%;
      position: absolute;
      top: 0;
      left: 0;
      display: block;
    }
    #pitch-2d-canvas {
      width: 100%;
      height: 100%;
      position: absolute;
      top: 0;
      left: 0;
      display: none;
    }
    .hud-overlay {
      position: absolute;
      top: 14px;
      left: 14px;
      background: rgba(7, 10, 16, 0.75);
      border: 1px solid var(--border);
      padding: 8px 14px;
      border-radius: 8px;
      backdrop-filter: blur(8px);
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.8rem;
      z-index: 10;
      pointer-events: none;
    }
    .controls {
      display: flex;
      align-items: center;
      gap: 12px;
      width: 100%;
      padding: 10px 16px;
      background: rgba(0, 0, 0, 0.5);
      border-radius: 10px;
      border: 1px solid var(--border);
    }
    .btn {
      background: #1f2937;
      color: var(--text);
      border: 1px solid var(--border);
      padding: 7px 16px;
      border-radius: 6px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }
    .btn:hover { background: #374151; }
    .btn-play { background: var(--accent); color: #000; font-weight: 700; border: none; }
    .btn-play:hover { background: #059669; color: #fff; }
    .slider {
      flex: 1;
      accent-color: var(--accent);
      cursor: pointer;
      height: 6px;
    }
    .sidebar {
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    .frame-info {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .info-row {
      display: flex;
      justify-content: space-between;
      font-size: 0.86rem;
    }
    .info-val { font-family: 'JetBrains Mono', monospace; font-weight: 600; }
    .shot-gauge {
      margin-top: 6px;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 6px;
      height: 10px;
      overflow: hidden;
      border: 1px solid var(--border);
    }
    .shot-fill {
      height: 100%;
      background: linear-gradient(90deg, #10b981, #f59e0b, #ef4444);
      width: 0%;
      transition: width 0.08s ease;
    }
    .hint-box {
      font-size: 0.75rem;
      color: var(--text-muted);
      line-height: 1.4;
      padding: 8px 12px;
      background: rgba(255, 255, 255, 0.03);
      border-radius: 8px;
    }
  </style>
</head>
<body>
  <div class="header">
    <div>
      <h2 style="letter-spacing: -0.02em;">⚽ 3D Tactical Pitch Control & Ball Kinematics</h2>
      <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 2px;">More Than a Hack 2027 · Barça Innovation Hub & Metrica Sports</p>
    </div>
    <div style="display: flex; align-items: center; gap: 14px; flex-wrap: wrap;">
      <!-- Match Selector Dropdown -->
      <select id="match-select" onchange="onMatchChange(this.value)" style="background: #111827; color: #f3f4f6; border: 1px solid var(--border); border-radius: 8px; padding: 7px 12px; font-size: 0.84rem; font-weight: 600; cursor: pointer; outline: none;">
        {% for m_id, m_data in matches.items() %}
          <option value="{{ m_id }}" {% if m_id == selected_match_id %}selected{% endif %}>{{ m_data.title }}</option>
        {% endfor %}
      </select>

      <div class="view-toggle">
        <button id="btn-view-3d" class="view-btn active" onclick="switchView('3d')">3D Stadium</button>
        <button id="btn-view-2d" class="view-btn" onclick="switchView('2d')">2D Planar</button>
      </div>
      <div class="badge">● MATCH CLOCK SYNC</div>
    </div>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-label">Match Clock</div>
      <div class="stat-val" style="color: #60a5fa;" id="stat-clock">14:00</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Home Territory Control</div>
      <div class="stat-val" style="color: var(--home);">{{ "%.1f"|format(home_pct) }}%</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Away Territory Control</div>
      <div class="stat-val" style="color: var(--away);">{{ "%.1f"|format(away_pct) }}%</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Ball Elevation (Z)</div>
      <div class="stat-val" style="color: #a78bfa;" id="stat-z">0.0 m</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Shot / Ball Speed</div>
      <div class="stat-val" style="color: #f59e0b;" id="stat-speed">0.0 km/h</div>
    </div>
  </div>

  <div class="main-grid">
    <div class="viewport-card">
      <div class="view-stage">
        <div class="hud-overlay" id="hud-camera-info">
          🎥 3D Orbit Camera: Left Click to Rotate | Right Click to Pan | Scroll to Zoom
        </div>
        <div id="three-canvas-container"></div>
        <canvas id="pitch-2d-canvas" width="1050" height="680"></canvas>
      </div>
      
      <div class="controls">
        <button id="btn-play" class="btn btn-play" onclick="togglePlay()">Play ▶</button>
        <button class="btn" onclick="stepFrame(-10)">-10s</button>
        <button class="btn" onclick="stepFrame(-1)">◀</button>
        <input type="range" id="frame-slider" class="slider" min="1" max="{{ total_frames }}" value="1" oninput="onSlide(this.value)">
        <button class="btn" onclick="stepFrame(1)">▶</button>
        <button class="btn" onclick="stepFrame(10)">+10s</button>
        <span id="frame-label" style="font-family: 'JetBrains Mono'; font-weight: 600; min-width: 100px; text-align: right;">1 / {{ total_frames }}</span>
      </div>

      <div class="hint-box">
        💡 <strong>Realistic Physics & Multi-Match Scenarios:</strong> Trajektori bola mengikuti fisika riil (umpan akurat dari pengumpan ke penerima, kontrol bola natural, *cross* parabolik melengkung, & tembakan keras hingga 115 km/h). Gunakan dropdown di atas untuk berpindah antara <strong>El Clásico (Camp Nou)</strong>, <strong>Final Liga Champions</strong>, dan <strong>Final Piala Dunia</strong>.
      </div>
    </div>

    <div class="sidebar">
      <div class="frame-info">
        <h4 style="margin-bottom: 2px;">Ball Kinematics & Power</h4>
        <div class="info-row">
          <span style="color: var(--text-muted);">Instantaneous Speed</span>
          <span id="lbl-speed-val" class="info-val">0.0 km/h</span>
        </div>
        <div class="shot-gauge">
          <div id="shot-meter" class="shot-fill"></div>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Flight Elevation (Z)</span>
          <span id="lbl-z-val" class="info-val">0.00 m</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Ball State</span>
          <span id="lbl-ball-state" class="info-val" style="color: var(--accent);">GROUND PASS</span>
        </div>
      </div>

      <div class="frame-info">
        <h4 style="margin-bottom: 2px;">Live Possession Telemetry</h4>
        <div class="info-row">
          <span style="color: var(--text-muted);">Possessing Team</span>
          <span id="lbl-team" class="info-val" style="color: var(--home);">Home</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Active Player</span>
          <span id="lbl-player" class="info-val">H1</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Ball Proximity</span>
          <span id="lbl-dist" class="info-val">0.2 m</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Possession Stability</span>
          <span id="lbl-status" class="info-val" style="color: var(--accent);">STABLE</span>
        </div>
      </div>

      <div class="frame-info">
        <h4 style="margin-bottom: 2px;">Spearman Spatial Territory</h4>
        <div class="info-row">
          <span style="color: var(--text-muted);">Home Control</span>
          <span id="lbl-pc-home" class="info-val" style="color: var(--home);">50.0%</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Away Control</span>
          <span id="lbl-pc-away" class="info-val" style="color: var(--away);">50.0%</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">3D Stadium Model</span>
          <span class="info-val">WebGL / Three.js</span>
        </div>
      </div>
    </div>
  </div>

  <script>
    const initialFrame = {{ initial_frame_json|safe }};
    let matchData = [initialFrame];
    let maxFrames = {{ total_frames }};
    let currentFrame = 1;
    let isPlaying = false;
    let playTimer = null;
    let activeView = '3d';

    // ---------------- THREE.JS 3D ENGINE INITIALIZATION ----------------
    const container = document.getElementById('three-canvas-container');
    let scene, camera, renderer, controls, pitchMesh, ballMesh, ballShadow;
    const playerMeshes = {};
    let threeInitialized = false;

    // Force 3D Stadium as primary default view
    activeView = '3d';

    function initThreeEngine() {
      if (typeof THREE === 'undefined') return false;

      try {
        scene = new THREE.Scene();
        scene.background = new THREE.Color(0x06090e);

        const stageEl = document.querySelector('.view-stage');
        const initW = (stageEl ? stageEl.clientWidth : 0) || container.clientWidth || 1050;
        const initH = (stageEl ? stageEl.clientHeight : 0) || container.clientHeight || 520;
        const aspect = initW / initH;
        camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 1000);
        camera.position.set(52.5, -60, 65);
        camera.up.set(0, 0, 1);

        // Try creating WebGL renderer with broad hardware/software compatibility
        let createdRenderer = null;
        const configCandidates = [
          { antialias: true, alpha: true, powerPreference: 'default' },
          { antialias: false, alpha: true, failIfMajorPerformanceCaveat: false },
          { antialias: false, alpha: false, preserveDrawingBuffer: true, failIfMajorPerformanceCaveat: false }
        ];

        for (const cfg of configCandidates) {
          try {
            createdRenderer = new THREE.WebGLRenderer(cfg);
            if (createdRenderer) break;
          } catch (cfgErr) {
            console.warn("Attempting next WebGL config candidate...", cfgErr);
          }
        }

        if (!createdRenderer) {
          console.warn("Could not create WebGLRenderer under candidate configurations.");
          return false;
        }

        renderer = createdRenderer;
        renderer.setSize(initW, initH);
        renderer.shadowMap.enabled = true;
        container.appendChild(renderer.domElement);

        if (THREE.OrbitControls) {
          controls = new THREE.OrbitControls(camera, renderer.domElement);
          controls.target.set(52.5, 34, 0);
          controls.enableDamping = true;
          controls.dampingFactor = 0.05;
          controls.maxPolarAngle = Math.PI / 2.05;
        }

        const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xffffff, 0.9);
        dirLight.position.set(52.5, -40, 90);
        dirLight.castShadow = true;
        scene.add(dirLight);

        const dirLight2 = new THREE.DirectionalLight(0xa7f3d0, 0.4);
        dirLight2.position.set(52.5, 110, 80);
        scene.add(dirLight2);

        const pitchGeometry = new THREE.PlaneGeometry(105, 68);
        const pitchMaterial = new THREE.MeshStandardMaterial({
          color: 0x1b4d2e,
          roughness: 0.6,
          metalness: 0.05,
          side: THREE.DoubleSide
        });
        pitchMesh = new THREE.Mesh(pitchGeometry, pitchMaterial);
        pitchMesh.position.set(52.5, 34, 0);
        scene.add(pitchMesh);

        const outerGeo = new THREE.PlaneGeometry(125, 84);
        const outerMat = new THREE.MeshStandardMaterial({ color: 0x0f2918, roughness: 0.9, side: THREE.DoubleSide });
        const outerMesh = new THREE.Mesh(outerGeo, outerMat);
        outerMesh.position.set(52.5, 34, -0.05);
        scene.add(outerMesh);

        return true;
      } catch (err) {
        console.error("Three.js setup encountered error:", err);
        return false;
      }
    }

    threeInitialized = initThreeEngine();
    console.log("Three.js 3D Stadium initialized:", threeInitialized);

    // 3D Pitch Lines Wireframe
    function create3DPitchLines() {
      if (!threeInitialized) return;
      const lineMat = new THREE.LineBasicMaterial({ color: 0xffffff, linewidth: 2 });
      
      const points = [
        new THREE.Vector3(0, 0, 0.02),
        new THREE.Vector3(105, 0, 0.02),
        new THREE.Vector3(105, 68, 0.02),
        new THREE.Vector3(0, 68, 0.02),
        new THREE.Vector3(0, 0, 0.02)
      ];
      scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), lineMat));

      const halfPts = [new THREE.Vector3(52.5, 0, 0.02), new THREE.Vector3(52.5, 68, 0.02)];
      scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(halfPts), lineMat));

      const circlePts = [];
      for (let i = 0; i <= 64; i++) {
        const theta = (i / 64) * Math.PI * 2;
        circlePts.push(new THREE.Vector3(52.5 + Math.cos(theta) * 9.15, 34 + Math.sin(theta) * 9.15, 0.02));
      }
      scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(circlePts), lineMat));

      function addGoal(x, yMin, yMax) {
        const goalMat = new THREE.LineBasicMaterial({ color: 0xe5e7eb, linewidth: 2 });
        const postH = 2.44;
        const gPts = [
          new THREE.Vector3(x, yMin, 0),
          new THREE.Vector3(x, yMin, postH),
          new THREE.Vector3(x, yMax, postH),
          new THREE.Vector3(x, yMax, 0)
        ];
        scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(gPts), goalMat));
      }
      addGoal(0, 30.34, 37.66);
      addGoal(105, 30.34, 37.66);
    }
    if (threeInitialized) create3DPitchLines();

    if (threeInitialized) {
      ballMesh = new THREE.Mesh(
        new THREE.SphereGeometry(0.55, 16, 16),
        new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2, metalness: 0.1 })
      );
      ballMesh.castShadow = true;
      scene.add(ballMesh);

      ballShadow = new THREE.Mesh(
        new THREE.RingGeometry(0.2, 0.7, 16),
        new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.5, side: THREE.DoubleSide })
      );
      ballShadow.position.z = 0.03;
      scene.add(ballShadow);
    }

    function getOrCreatePlayerMesh(id, team) {
      if (!threeInitialized) return null;
      if (!playerMeshes[id]) {
        const group = new THREE.Group();
        
        const bodyGeo = new THREE.CylinderGeometry(0.4, 0.4, 1.75, 12);
        bodyGeo.rotateX(Math.PI / 2);
        const bodyMat = new THREE.MeshStandardMaterial({
          color: team === 'Home' ? 0xef4444 : 0x3b82f6,
          roughness: 0.4
        });
        const body = new THREE.Mesh(bodyGeo, bodyMat);
        body.position.z = 0.88;
        group.add(body);

        const headGeo = new THREE.SphereGeometry(0.32, 12, 12);
        const headMat = new THREE.MeshStandardMaterial({ color: 0xfde047 });
        const head = new THREE.Mesh(headGeo, headMat);
        head.position.z = 1.95;
        group.add(head);

        scene.add(group);
        playerMeshes[id] = group;
      }
      return playerMeshes[id];
    }

    function animate3D() {
      if (!threeInitialized) return;
      requestAnimationFrame(animate3D);
      if (controls) controls.update();
      renderer.render(scene, camera);
    }
    if (threeInitialized) animate3D();

    // ---------------- CANVAS PROJECTION ENGINES (2D & UNIVERSAL 3D STADIUM) ----------------
    const canvas2D = document.getElementById('pitch-2d-canvas');
    const ctx2D = canvas2D.getContext('2d');

    // Interactive 3D Perspective controls (Mouse rotation & pitch)
    let camPitch = 0.52; // Elevation angle (~30 deg)
    let camYaw = 0.0;    // Azimuth angle
    let isDragging = false;
    let dragStartX = 0;
    let dragStartY = 0;

    canvas2D.addEventListener('mousedown', (e) => {
      if (activeView === '3d' && !threeInitialized) {
        isDragging = true;
        dragStartX = e.clientX;
        dragStartY = e.clientY;
      }
    });
    window.addEventListener('mousemove', (e) => {
      if (isDragging) {
        const dx = e.clientX - dragStartX;
        const dy = e.clientY - dragStartY;
        dragStartX = e.clientX;
        dragStartY = e.clientY;
        camYaw += dx * 0.005;
        camPitch = Math.max(0.18, Math.min(0.95, camPitch - dy * 0.005));
        render(currentFrame);
      }
    });
    window.addEventListener('mouseup', () => { isDragging = false; });

    function resizeCanvas() {
      const stageEl = document.querySelector('.view-stage');
      const rect = stageEl ? stageEl.getBoundingClientRect() : canvas2D.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas2D.width = Math.round((rect.width || 1050) * dpr);
      canvas2D.height = Math.round((rect.height || 520) * dpr);
    }
    resizeCanvas();

    // 3D Perspective Projection Mathematics (Universal Software 3D Viewport)
    function project3D(x, y, z, W, H) {
      // Coordinate shift to center of pitch (52.5, 34)
      const cx = x - 52.5;
      const cy = y - 34.0;
      const cz = z || 0;

      // Apply Yaw rotation
      const cosY = Math.cos(camYaw);
      const sinY = Math.sin(camYaw);
      const rx = cx * cosY - cy * sinY;
      const ry = cx * sinY + cy * cosY;

      // Apply Pitch tilt
      const cosP = Math.cos(camPitch);
      const sinP = Math.sin(camPitch);
      const rz = cz * cosP - ry * sinP;
      const camDist = 135.0;
      const depth = camDist + (ry * cosP + cz * sinP);

      // Perspective divide
      const fov = Math.min(W, H) * 1.55;
      const px = (W / 2) + (rx * fov) / depth;
      const py = (H / 2) - (rz * fov) / depth + (H * 0.08);
      const scale = fov / depth;

      return { x: px, y: py, scale: scale, depth: depth };
    }

    // High-Fidelity Universal 3D Stadium Projection Engine
    function render3DStadium(frameData) {
      if (!canvas2D.width || !canvas2D.height) resizeCanvas();
      const W = canvas2D.width;
      const H = canvas2D.height;

      // 1. Stadium Night Arena Background & Horizon Glow
      const bgGrad = ctx2D.createRadialGradient(W / 2, H * 0.35, 10, W / 2, H * 0.35, W * 0.7);
      bgGrad.addColorStop(0, '#0d1929');
      bgGrad.addColorStop(0.5, '#070c14');
      bgGrad.addColorStop(1, '#030508');
      ctx2D.fillStyle = bgGrad;
      ctx2D.fillRect(0, 0, W, H);

      // 2. Surrounding Outer Stadium Apron / Concrete Run-off (3D Polygon)
      const apronCorners = [
        project3D(-8, -8, -0.05, W, H),
        project3D(113, -8, -0.05, W, H),
        project3D(113, 76, -0.05, W, H),
        project3D(-8, 76, -0.05, W, H)
      ];
      ctx2D.fillStyle = '#0a1e12';
      ctx2D.beginPath();
      ctx2D.moveTo(apronCorners[0].x, apronCorners[0].y);
      for (let i = 1; i < apronCorners.length; i++) ctx2D.lineTo(apronCorners[i].x, apronCorners[i].y);
      ctx2D.closePath();
      ctx2D.fill();

      // 3. Realistic 3D Grass Mown Bands (10 Distinct Green Perspective Stripes)
      const numBands = 10;
      const bStep = 105.0 / numBands;
      for (let i = 0; i < numBands; i++) {
        const x0 = i * bStep;
        const x1 = (i + 1) * bStep;
        const p1 = project3D(x0, 0, 0, W, H);
        const p2 = project3D(x1, 0, 0, W, H);
        const p3 = project3D(x1, 68, 0, W, H);
        const p4 = project3D(x0, 68, 0, W, H);

        ctx2D.fillStyle = (i % 2 === 0) ? '#16532d' : '#146034';
        ctx2D.beginPath();
        ctx2D.moveTo(p1.x, p1.y);
        ctx2D.lineTo(p2.x, p2.y);
        ctx2D.lineTo(p3.x, p3.y);
        ctx2D.lineTo(p4.x, p4.y);
        ctx2D.closePath();
        ctx2D.fill();
      }

      // 4. White 3D Pitch Lines & Markings
      ctx2D.strokeStyle = 'rgba(255, 255, 255, 0.9)';
      ctx2D.lineWidth = Math.max(1.5, 2.0 * (W / 1200));

      function draw3DPoly(pts, close = false) {
        ctx2D.beginPath();
        pts.forEach((pt, idx) => {
          const pr = project3D(pt[0], pt[1], pt[2] || 0, W, H);
          if (idx === 0) ctx2D.moveTo(pr.x, pr.y);
          else ctx2D.lineTo(pr.x, pr.y);
        });
        if (close) ctx2D.closePath();
        ctx2D.stroke();
      }

      // Perimeter Boundary Lines
      draw3DPoly([[0, 0], [105, 0], [105, 68], [0, 68]], true);

      // Halfway Line
      draw3DPoly([[52.5, 0], [52.5, 68]]);

      // Center Circle in 3D (36-segment loop)
      const centerCirclePts = [];
      for (let a = 0; a <= 36; a++) {
        const theta = (a / 36) * Math.PI * 2;
        centerCirclePts.push([52.5 + Math.cos(theta) * 9.15, 34.0 + Math.sin(theta) * 9.15]);
      }
      draw3DPoly(centerCirclePts, true);

      // Center Spot
      const cSpot = project3D(52.5, 34, 0, W, H);
      ctx2D.fillStyle = '#ffffff';
      ctx2D.beginPath();
      ctx2D.arc(cSpot.x, cSpot.y, Math.max(2, 3.5 * cSpot.scale), 0, Math.PI * 2);
      ctx2D.fill();

      // Home Penalty Box (Left) & Away Penalty Box (Right)
      draw3DPoly([[0, 13.84], [16.5, 13.84], [16.5, 54.16], [0, 54.16]], true);
      draw3DPoly([[0, 24.84], [5.5, 24.84], [5.5, 43.16], [0, 43.16]], true);
      draw3DPoly([[105, 13.84], [105 - 16.5, 13.84], [105 - 16.5, 54.16], [105, 54.16]], true);
      draw3DPoly([[105, 24.84], [105 - 5.5, 24.84], [105 - 5.5, 43.16], [105, 43.16]], true);

      // 3D Goal Posts with Vertical Height (2.44m tall) & Crossbar
      function draw3DGoal(gx, gyMin, gyMax, depthDir) {
        ctx2D.strokeStyle = '#ffffff';
        ctx2D.lineWidth = 2.5;
        // Front uprights & crossbar
        const p1 = project3D(gx, gyMin, 0, W, H);
        const p2 = project3D(gx, gyMin, 2.44, W, H);
        const p3 = project3D(gx, gyMax, 2.44, W, H);
        const p4 = project3D(gx, gyMax, 0, W, H);
        ctx2D.beginPath();
        ctx2D.moveTo(p1.x, p1.y);
        ctx2D.lineTo(p2.x, p2.y);
        ctx2D.lineTo(p3.x, p3.y);
        ctx2D.lineTo(p4.x, p4.y);
        ctx2D.stroke();

        // 3D Net backing
        const nb1 = project3D(gx + depthDir * 2.2, gyMin, 0, W, H);
        const nb2 = project3D(gx + depthDir * 2.2, gyMin, 2.0, W, H);
        const nb3 = project3D(gx + depthDir * 2.2, gyMax, 2.0, W, H);
        const nb4 = project3D(gx + depthDir * 2.2, gyMax, 0, W, H);
        ctx2D.strokeStyle = 'rgba(255, 255, 255, 0.4)';
        ctx2D.lineWidth = 1.0;
        ctx2D.beginPath();
        ctx2D.moveTo(p2.x, p2.y); ctx2D.lineTo(nb2.x, nb2.y); ctx2D.lineTo(nb3.x, nb3.y); ctx2D.lineTo(p3.x, p3.y);
        ctx2D.moveTo(nb2.x, nb2.y); ctx2D.lineTo(nb1.x, nb1.y);
        ctx2D.moveTo(nb3.x, nb3.y); ctx2D.lineTo(nb4.x, nb4.y);
        ctx2D.stroke();
      }
      draw3DGoal(0, 30.34, 37.66, -1);
      draw3DGoal(105, 30.34, 37.66, 1);

      // 5. Sort Entities by Depth for Photorealistic 3D Occlusion (Z-Buffer Simulation)
      const renderList = [];

      // Add Players to Render List
      frameData.players.forEach(p => {
        const basePr = project3D(p.x, p.y, 0, W, H);
        const headPr = project3D(p.x, p.y, 1.85, W, H);
        renderList.push({
          type: 'player',
          depth: basePr.depth,
          data: p,
          base: basePr,
          head: headPr
        });
      });

      // Add Ball to Render List
      const ballZ = Math.max(0.1, frameData.ball.z || 0);
      const bShadowPr = project3D(frameData.ball.x, frameData.ball.y, 0, W, H);
      const bAirPr = project3D(frameData.ball.x, frameData.ball.y, ballZ, W, H);
      renderList.push({
        type: 'ball',
        depth: bAirPr.depth,
        data: frameData.ball,
        shadow: bShadowPr,
        ball: bAirPr,
        z: ballZ
      });

      // Sort Back to Front (Painters Algorithm)
      renderList.sort((a, b) => b.depth - a.depth);

      // 6. Draw 3D Entities
      renderList.forEach(item => {
        if (item.type === 'player') {
          const p = item.data;
          const base = item.base;
          const head = item.head;
          const isHome = (p.team === 'Home');
          const rBase = Math.max(3, 5.0 * base.scale);

          // Ground Contact Shadow
          ctx2D.fillStyle = 'rgba(0, 0, 0, 0.45)';
          ctx2D.beginPath();
          ctx2D.ellipse(base.x, base.y, rBase * 1.5, rBase * 0.7, 0, 0, Math.PI * 2);
          ctx2D.fill();

          // 3D Player Torso (Vertical Cylinder)
          ctx2D.fillStyle = isHome ? '#ef4444' : '#3b82f6';
          ctx2D.beginPath();
          ctx2D.arc(base.x, base.y - (rBase * 0.8), rBase * 1.2, 0, Math.PI * 2);
          ctx2D.fill();

          // Body connector
          ctx2D.strokeStyle = isHome ? '#b91c1c' : '#1d4ed8';
          ctx2D.lineWidth = rBase * 2.1;
          ctx2D.lineCap = 'round';
          ctx2D.beginPath();
          ctx2D.moveTo(base.x, base.y - 4);
          ctx2D.lineTo(head.x, head.y + 4);
          ctx2D.stroke();

          // 3D Player Head (Sphere with highlight)
          const rHead = Math.max(3.5, 4.5 * head.scale);
          ctx2D.fillStyle = '#fde047';
          ctx2D.beginPath();
          ctx2D.arc(head.x, head.y, rHead, 0, Math.PI * 2);
          ctx2D.fill();

          // ID Label Tag
          ctx2D.fillStyle = '#ffffff';
          ctx2D.font = `bold ${Math.max(8, Math.round(11 * head.scale))}px 'JetBrains Mono', sans-serif`;
          ctx2D.textAlign = 'center';
          ctx2D.textBaseline = 'bottom';
          ctx2D.fillText(p.id.replace('Home_', 'H').replace('Away_', 'A'), head.x, head.y - rHead - 2);
        } else if (item.type === 'ball') {
          const sh = item.shadow;
          const b = item.ball;
          const z = item.z;

          // Parabolic Ground Shadow (Scales down and fades as ball ascends)
          const shadowOpacity = Math.max(0.12, 0.55 - (z * 0.08));
          const shadowSize = Math.max(2, (6.5 * sh.scale) * Math.max(0.4, 1.0 - z * 0.1));
          ctx2D.fillStyle = `rgba(0, 0, 0, ${shadowOpacity})`;
          ctx2D.beginPath();
          ctx2D.ellipse(sh.x, sh.y, shadowSize * 1.4, shadowSize * 0.7, 0, 0, Math.PI * 2);
          ctx2D.fill();

          // Altitude guideline connector if aerial
          if (z > 0.6) {
            ctx2D.strokeStyle = 'rgba(255, 255, 255, 0.25)';
            ctx2D.lineWidth = 1;
            ctx2D.setLineDash([3, 3]);
            ctx2D.beginPath();
            ctx2D.moveTo(sh.x, sh.y);
            ctx2D.lineTo(b.x, b.y);
            ctx2D.stroke();
            ctx2D.setLineDash([]);
          }

          // 3D Elevated Ball Sphere
          const rBall = Math.max(4, 5.5 * b.scale);

          // Golden Power Aura if High-Speed Strike
          if (item.data.speed_kmh > 70) {
            ctx2D.fillStyle = 'rgba(245, 158, 11, 0.35)';
            ctx2D.beginPath();
            ctx2D.arc(b.x, b.y, rBall * 2.2, 0, Math.PI * 2);
            ctx2D.fill();
          }

          const ballGrad = ctx2D.createRadialGradient(b.x - (rBall * 0.3), b.y - (rBall * 0.3), rBall * 0.1, b.x, b.y, rBall);
          ballGrad.addColorStop(0, '#ffffff');
          ballGrad.addColorStop(0.8, '#e2e8f0');
          ballGrad.addColorStop(1, '#64748b');
          ctx2D.fillStyle = ballGrad;
          ctx2D.beginPath();
          ctx2D.arc(b.x, b.y, rBall, 0, Math.PI * 2);
          ctx2D.fill();

          ctx2D.strokeStyle = '#0f172a';
          ctx2D.lineWidth = 1.2;
          ctx2D.stroke();
        }
      });
    }

    // ---------------- 2D BROADCAST PITCH ENGINE (HIGH RESOLUTION) ----------------
    function render2D(frameData) {
      if (!canvas2D.width || !canvas2D.height) resizeCanvas();
      const W = canvas2D.width;
      const H = canvas2D.height;
      const PITCH_W = 105.0;
      const PITCH_H = 68.0;

      // Inner pitch margins
      const padX = W * 0.04;
      const padY = H * 0.05;
      const pW = W - (padX * 2);
      const pH = H - (padY * 2);

      const sx = (x) => padX + (x / PITCH_W) * pW;
      const sy = (y) => padY + ((PITCH_H - y) / PITCH_H) * pH;
      const scaleM = pW / PITCH_W;

      // 1. Surrounding Stadium Grass / Border
      ctx2D.fillStyle = "#0c2814";
      ctx2D.fillRect(0, 0, W, H);

      // 2. Main Pitch Turf with Camp Nou Striped Pattern (10 vertical grass bands)
      const numBands = 10;
      const bandWidth = pW / numBands;
      for (let i = 0; i < numBands; i++) {
        ctx2D.fillStyle = (i % 2 === 0) ? "#14532d" : "#166534";
        ctx2D.fillRect(padX + (i * bandWidth), padY, bandWidth, pH);
      }

      // 3. Pitch Boundary & Line Markings
      ctx2D.strokeStyle = "rgba(255, 255, 255, 0.88)";
      ctx2D.lineWidth = Math.max(2, 2.2 * (W / 1200));

      // Perimeter
      ctx2D.strokeRect(padX, padY, pW, pH);

      // Halfway Line
      ctx2D.beginPath();
      ctx2D.moveTo(sx(52.5), sy(0));
      ctx2D.lineTo(sx(52.5), sy(68));
      ctx2D.stroke();

      // Center Circle (9.15m radius) & Center Spot
      ctx2D.beginPath();
      ctx2D.arc(sx(52.5), sy(34), 9.15 * scaleM, 0, Math.PI * 2);
      ctx2D.stroke();

      ctx2D.fillStyle = "#ffffff";
      ctx2D.beginPath();
      ctx2D.arc(sx(52.5), sy(34), 3 * (W / 1200), 0, Math.PI * 2);
      ctx2D.fill();

      // Penalty Boxes (16.5m depth, 40.32m width -> y from 13.84 to 54.16)
      // Home Box (Left)
      ctx2D.strokeRect(sx(0), sy(54.16), 16.5 * scaleM, 40.32 * scaleM);
      // Home 6-yard Box (5.5m depth, 18.32m width -> y from 24.84 to 43.16)
      ctx2D.strokeRect(sx(0), sy(43.16), 5.5 * scaleM, 18.32 * scaleM);
      // Home Penalty Spot (11m) & Arc
      ctx2D.beginPath();
      ctx2D.arc(sx(11), sy(34), 2.5 * (W / 1200), 0, Math.PI * 2);
      ctx2D.fill();
      ctx2D.beginPath();
      ctx2D.arc(sx(11), sy(34), 9.15 * scaleM, -0.92, 0.92);
      ctx2D.stroke();

      // Away Box (Right)
      ctx2D.strokeRect(sx(105 - 16.5), sy(54.16), 16.5 * scaleM, 40.32 * scaleM);
      // Away 6-yard Box
      ctx2D.strokeRect(sx(105 - 5.5), sy(43.16), 5.5 * scaleM, 18.32 * scaleM);
      // Away Penalty Spot & Arc
      ctx2D.beginPath();
      ctx2D.arc(sx(105 - 11), sy(34), 2.5 * (W / 1200), 0, Math.PI * 2);
      ctx2D.fill();
      ctx2D.beginPath();
      ctx2D.arc(sx(105 - 11), sy(34), 9.15 * scaleM, Math.PI - 0.92, Math.PI + 0.92);
      ctx2D.stroke();

      // Goal Nets (7.32m width -> y from 30.34 to 37.66)
      ctx2D.fillStyle = "rgba(255, 255, 255, 0.2)";
      ctx2D.fillRect(sx(0) - (2.4 * scaleM), sy(37.66), 2.4 * scaleM, 7.32 * scaleM);
      ctx2D.strokeRect(sx(0) - (2.4 * scaleM), sy(37.66), 2.4 * scaleM, 7.32 * scaleM);
      ctx2D.fillRect(sx(105), sy(37.66), 2.4 * scaleM, 7.32 * scaleM);
      ctx2D.strokeRect(sx(105), sy(37.66), 2.4 * scaleM, 7.32 * scaleM);

      // Corner Arcs (1m radius)
      const cR = 1.0 * scaleM;
      [[0, 0, 0, Math.PI / 2], [105, 0, Math.PI / 2, Math.PI], [105, 68, Math.PI, 1.5 * Math.PI], [0, 68, 1.5 * Math.PI, 2 * Math.PI]].forEach(([cx, cy, sA, eA]) => {
        ctx2D.beginPath();
        ctx2D.arc(sx(cx), sy(cy), cR, sA, eA);
        ctx2D.stroke();
      });

      // 4. Render Ball Shadow (Simulates 3D height in 2D view!)
      const ballZ = Math.max(0, frameData.ball.z || 0);
      const bpx = sx(frameData.ball.x);
      const bpy = sy(frameData.ball.y);
      const shadowOffset = ballZ * 5.0 * (W / 1200);

      ctx2D.fillStyle = "rgba(0, 0, 0, 0.45)";
      ctx2D.beginPath();
      ctx2D.ellipse(bpx + shadowOffset, bpy + shadowOffset, Math.max(4, 7 - ballZ * 0.8), Math.max(2.5, 4.5 - ballZ * 0.5), 0, 0, Math.PI * 2);
      ctx2D.fill();

      // 5. Render Players with Team Colors & ID Tags
      frameData.players.forEach(p => {
        const px = sx(p.x);
        const py = sy(p.y);
        const isHome = (p.team === 'Home');
        const radius = Math.max(7, 9 * (W / 1200));

        // Player Ring / Shadow
        ctx2D.fillStyle = "rgba(0, 0, 0, 0.35)";
        ctx2D.beginPath();
        ctx2D.arc(px + 2, py + 2, radius, 0, Math.PI * 2);
        ctx2D.fill();

        // Player Circle
        ctx2D.fillStyle = isHome ? "#ef4444" : "#3b82f6";
        ctx2D.beginPath();
        ctx2D.arc(px, py, radius, 0, Math.PI * 2);
        ctx2D.fill();

        // Highlighting Border
        ctx2D.strokeStyle = isHome ? "#fca5a5" : "#93c5fd";
        ctx2D.lineWidth = 1.8;
        ctx2D.stroke();

        // Player Number / ID
        ctx2D.fillStyle = "#ffffff";
        ctx2D.font = `bold ${Math.max(8, 10 * (W / 1200))}px 'JetBrains Mono', sans-serif`;
        ctx2D.textAlign = "center";
        ctx2D.textBaseline = "middle";
        ctx2D.fillText(p.id.replace('Home_', 'H').replace('Away_', 'A'), px, py);
      });

      // 6. Render Ball (Sphere with highlight & velocity trail)
      const ballRadius = Math.max(5, (6 + Math.min(6, ballZ * 1.5)) * (W / 1200));
      
      // Ball glow if aerial strike
      if (ballZ > 1.5) {
        ctx2D.fillStyle = "rgba(250, 204, 21, 0.3)";
        ctx2D.beginPath();
        ctx2D.arc(bpx, bpy, ballRadius * 1.8, 0, Math.PI * 2);
        ctx2D.fill();
      }

      ctx2D.fillStyle = "#ffffff";
      ctx2D.beginPath();
      ctx2D.arc(bpx, bpy, ballRadius, 0, Math.PI * 2);
      ctx2D.fill();

      ctx2D.strokeStyle = "#111827";
      ctx2D.lineWidth = 1.5;
      ctx2D.stroke();
    }

    // ---------------- FRAME RENDERER CONTROLLER ----------------
    function render(frameIdx) {
      const f = matchData[frameIdx - 1];
      if (!f) return;

      // Update 3D Positions if Three.js WebGL is running
      if (threeInitialized) {
        f.players.forEach(p => {
          const mesh = getOrCreatePlayerMesh(p.id, p.team);
          if (mesh) mesh.position.set(p.x, p.y, p.z || 0);
        });

        // Update 3D Ball Position with Z elevation
        if (ballMesh && ballShadow) {
          const bz = Math.max(0.28, f.ball.z || 0);
          ballMesh.position.set(f.ball.x, f.ball.y, bz);
          ballShadow.position.set(f.ball.x, f.ball.y, 0.03);
          ballShadow.scale.setScalar(Math.max(0.4, 1.0 - (bz * 0.08)));
        }
      }

      // Render Active Viewport on Canvas
      if (activeView === '3d') {
        if (!threeInitialized) {
          // Universal 3D Stadium Projection Engine
          render3DStadium(f);
        }
      } else {
        // Planar 2D Broadcast View
        render2D(f);
      }

      // Update HUD & Telemetry
      document.getElementById('frame-slider').value = frameIdx;
      document.getElementById('frame-label').textContent = `${frameIdx} / ${maxFrames}`;
      document.getElementById('stat-clock').textContent = f.match_time || "14:00";
      document.getElementById('stat-z').textContent = (f.ball.z || 0).toFixed(2) + " m";
      document.getElementById('lbl-z-val').textContent = (f.ball.z || 0).toFixed(2) + " m";

      const speed = f.ball.speed_kmh || 0;
      document.getElementById('stat-speed').textContent = speed.toFixed(1) + " km/h";
      document.getElementById('lbl-speed-val').textContent = speed.toFixed(1) + " km/h";

      // Shot Power Gauge (0 to 120 km/h)
      const pct = Math.min(100, (speed / 120) * 100);
      document.getElementById('shot-meter').style.width = pct + "%";

      // Ball State (Ground pass vs Aerial flight vs Strike)
      const bStateEl = document.getElementById('lbl-ball-state');
      if (f.ball.z > 2.0 && speed > 60) {
        bStateEl.textContent = "POWER STRIKE 🔥";
        bStateEl.style.color = "#ef4444";
      } else if (f.ball.z > 1.2) {
        bStateEl.textContent = "AERIAL FLIGHT / CROSS ✈️";
        bStateEl.style.color = "#a78bfa";
      } else {
        bStateEl.textContent = "GROUND PASS / CONTROL";
        bStateEl.style.color = "var(--accent)";
      }

      // Possession Sidebar
      const poss = f.possession;
      const teamEl = document.getElementById('lbl-team');
      teamEl.textContent = poss.smoothed_team || 'Contested';
      teamEl.style.color = poss.smoothed_team === 'Home' ? 'var(--home)' : (poss.smoothed_team === 'Away' ? 'var(--away)' : '#eab308');

      document.getElementById('lbl-player').textContent = poss.possessing_player || 'Contested Ball';
      document.getElementById('lbl-dist').textContent = (poss.min_distance || 0).toFixed(2) + ' m';
      
      const statusEl = document.getElementById('lbl-status');
      statusEl.textContent = poss.is_stable ? 'STABLE' : 'TRANSITION';
      statusEl.style.color = poss.is_stable ? 'var(--accent)' : '#f59e0b';

      if (poss.home_pitch_control_pct !== undefined) {
        document.getElementById('lbl-pc-home').textContent = poss.home_pitch_control_pct.toFixed(1) + '%';
        document.getElementById('lbl-pc-away').textContent = poss.away_pitch_control_pct.toFixed(1) + '%';
      }
    }

    function switchView(view) {
      activeView = view;
      document.getElementById('btn-view-3d').classList.toggle('active', view === '3d');
      document.getElementById('btn-view-2d').classList.toggle('active', view === '2d');
      
      const cont3d = document.getElementById('three-canvas-container');
      const cvs2d = document.getElementById('pitch-2d-canvas');
      const hudCam = document.getElementById('hud-camera-info');

      if (view === '3d') {
        if (threeInitialized) {
          cont3d.style.display = 'block';
          cvs2d.style.display = 'none';
          if (hudCam) {
            hudCam.style.display = 'block';
            hudCam.textContent = '🎥 3D Orbit Camera: Left Click to Rotate | Right Click to Pan | Scroll to Zoom';
          }
          if (renderer && camera) {
            const stage = document.querySelector('.view-stage');
            const w = (stage ? stage.clientWidth : 0) || cont3d.clientWidth || 1050;
            const h = (stage ? stage.clientHeight : 0) || cont3d.clientHeight || 520;
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
            renderer.setSize(w, h);
            renderer.render(scene, camera);
          }
        } else {
          // Hardware WebGL unavailable: Use Universal 3D Stadium on Canvas
          cont3d.style.display = 'none';
          cvs2d.style.display = 'block';
          if (hudCam) {
            hudCam.style.display = 'block';
            hudCam.textContent = '🎥 3D Stadium View (Universal Perspective): Drag mouse to rotate angle';
          }
          resizeCanvas();
        }
      } else {
        // 2D Planar
        cont3d.style.display = 'none';
        cvs2d.style.display = 'block';
        if (hudCam) hudCam.style.display = 'none';
        resizeCanvas();
      }

      render(currentFrame);
    }

    function onSlide(val) {
      currentFrame = parseInt(val);
      render(currentFrame);
    }

    function stepFrame(delta) {
      currentFrame = Math.max(1, Math.min(maxFrames, currentFrame + delta));
      render(currentFrame);
    }

    function togglePlay() {
      isPlaying = !isPlaying;
      const btn = document.getElementById('btn-play');
      if (isPlaying) {
        btn.textContent = 'Pause ⏸';
        btn.style.background = '#e11d48';
        playTimer = setInterval(() => {
          if (currentFrame >= maxFrames) {
            // STOP at end instead of infinite repeating loop!
            togglePlay();
            return;
          }
          currentFrame += 1;
          render(currentFrame);
        }, 40); // 25 FPS match velocity
      } else {
        btn.textContent = 'Play ▶';
        btn.style.background = 'var(--accent)';
        clearInterval(playTimer);
      }
    }

    // Default unconditionally to 3D Stadium
    switchView('3d');

    // Window Resize Handling
    window.addEventListener('resize', () => {
      if (threeInitialized && camera && renderer) {
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
      }
      resizeCanvas();
      render(currentFrame);
    });

    // Render frame 1 immediately from initial embedded payload!
    render(1);

    function onMatchChange(matchId) {
      if (isPlaying) togglePlay(); // Pause current playback
      document.getElementById('frame-label').textContent = "Loading match...";
      fetch(`/api/frames/${matchId}`)
        .then(res => res.json())
        .then(data => {
          matchData = data;
          maxFrames = data.length;
          currentFrame = 1;
          document.getElementById('frame-slider').max = maxFrames;
          document.getElementById('frame-slider').value = 1;
          document.getElementById('frame-label').textContent = `1 / ${maxFrames}`;
          render(1);
        })
        .catch(err => {
          console.error("Failed to switch match dataset:", err);
        });
    }

    // Initial async fetch for default match
    fetch('/api/frames/{{ selected_match_id }}')
      .then(res => res.json())
      .then(data => {
        matchData = data;
        maxFrames = data.length;
        document.getElementById('frame-slider').max = maxFrames;
        document.getElementById('frame-label').textContent = `${currentFrame} / ${maxFrames}`;
        render(currentFrame);
      })
      .catch(err => {
        console.error("Failed to load match tracking frames:", err);
      });
  </script>
</body>
</html>
"""

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route("/api/matches")
def get_matches():
    return jsonify([
        {"id": m_key, "title": m_val["title"]}
        for m_key, m_val in MATCH_CATALOG.items()
    ])

@app.route("/api/frames")
@app.route("/api/frames/<match_id>")
def get_frames(match_id=None):
    m_id = match_id or DEFAULT_MATCH_ID
    if m_id not in MATCH_CACHE:
        m_id = DEFAULT_MATCH_ID
    return jsonify(MATCH_CACHE[m_id]["frames"])

@app.route("/")
def index():
    initial_match = MATCH_CACHE[DEFAULT_MATCH_ID]
    initial_frame = initial_match["frames"][0] if initial_match["frames"] else {}
    return render_template_string(
        HTML_TEMPLATE,
        matches=MATCH_CATALOG,
        selected_match_id=DEFAULT_MATCH_ID,
        total_frames=initial_match["total_frames"],
        home_pct=initial_match["home_pct"],
        away_pct=initial_match["away_pct"],
        turnovers=initial_match["turnovers"],
        initial_frame_json=json.dumps(initial_frame)
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
