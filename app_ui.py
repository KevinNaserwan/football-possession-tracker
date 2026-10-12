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

DATASET_FILE = "data/sample_match_tracking.json"
frames = parser.load_json_match(DATASET_FILE) if os.path.exists(DATASET_FILE) else []

processed_frames = []
home_count = 0
away_count = 0
contested_count = 0
turnovers = []
last_team = None

print(f"Pre-calculating telemetry & pitch control metrics for {len(frames)} frames...")

for f in frames:
    res = pipeline.process_frame(f)
    team = res.get("smoothed_team")
    if team == "Home":
        home_count += 1
    elif team == "Away":
        away_count += 1
    else:
        contested_count += 1

    if last_team and team and team != last_team and team != "Contested":
        turnovers.append({
            "frame_id": f["frame_id"],
            "match_time": f.get("match_time", "14:00"),
            "from": last_team,
            "to": team
        })
    if team and team != "Contested":
        last_team = team

    # Downsampled pitch control grid
    pc_surface = pipeline.pitch_control_engine.calculate_pitch_control_surface(
        [p for p in f['players'] if p['team'] == 'Home'],
        [p for p in f['players'] if p['team'] == 'Away']
    )['home_surface']
    
    h_down = pc_surface[::2, ::2]
    surface_grid = [[round(float(v), 2) for v in row] for row in h_down]

    processed_frames.append({
        "frame_id": f["frame_id"],
        "match_time": f.get("match_time", "14:00"),
        "ball": f["ball"],
        "players": f["players"],
        "possession": res
    })

total_frames = max(1, len(frames))
print("Pre-computation finished! Ready for high-speed streaming.")

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
    <div style="display: flex; align-items: center; gap: 14px;">
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
        💡 <strong>Continuous Match Playback:</strong> Tidak looping! Simulasi merepresentasikan rangkaian fase taktikal riil: <em>Buildup kiper $\rightarrow$ Umpan sayap $\rightarrow$ Duel perebutan lini tengah $\rightarrow$ Counter-attack cepat $\rightarrow$ Aerial Cross $\rightarrow$ Tendangan keras ke gawang</em>.
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

    try {
      if (typeof THREE !== 'undefined') {
        scene = new THREE.Scene();
        scene.background = new THREE.Color(0x06090e);

        const aspect = (container.clientWidth && container.clientHeight) ? (container.clientWidth / container.clientHeight) : (105 / 68);
        camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 1000);
        camera.position.set(52.5, -60, 65); // Angled stadium broadcast view
        camera.up.set(0, 0, 1); // Z is vertical height!

        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(container.clientWidth || 1050, container.clientHeight || 680);
        renderer.shadowMap.enabled = true;
        container.appendChild(renderer.domElement);

        if (THREE.OrbitControls) {
          controls = new THREE.OrbitControls(camera, renderer.domElement);
          controls.target.set(52.5, 34, 0); // Pitch center
          controls.enableDamping = true;
          controls.dampingFactor = 0.05;
          controls.maxPolarAngle = Math.PI / 2.05; // Prevent camera clipping below ground
        }

        // Lighting: Stadium floodlights
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xffffff, 0.9);
        dirLight.position.set(52.5, -40, 90);
        dirLight.castShadow = true;
        scene.add(dirLight);

        // Secondary floodlight for stadium ambience
        const dirLight2 = new THREE.DirectionalLight(0xa7f3d0, 0.4);
        dirLight2.position.set(52.5, 110, 80);
        scene.add(dirLight2);

        // 3D Pitch Turf Mesh (105m x 68m) - Vibrant Pitch Grass
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

        // Stadium Pitch Surrounding Border / Sidewalk Turf
        const outerGeo = new THREE.PlaneGeometry(125, 84);
        const outerMat = new THREE.MeshStandardMaterial({ color: 0x0f2918, roughness: 0.9, side: THREE.DoubleSide });
        const outerMesh = new THREE.Mesh(outerGeo, outerMat);
        outerMesh.position.set(52.5, 34, -0.05);
        scene.add(outerMesh);
        threeInitialized = true;
      } else {
        console.warn("THREE is not defined, falling back to 2D canvas");
      }
    } catch (e) {
      console.error("Three.js initialization failed:", e);
      threeInitialized = false;
    }

    // 3D Pitch Lines Wireframe
    function create3DPitchLines() {
      if (!threeInitialized) return;
      const lineMat = new THREE.LineBasicMaterial({ color: 0xffffff, linewidth: 2 });
      
      // Perimeter
      const points = [
        new THREE.Vector3(0, 0, 0.02),
        new THREE.Vector3(105, 0, 0.02),
        new THREE.Vector3(105, 68, 0.02),
        new THREE.Vector3(0, 68, 0.02),
        new THREE.Vector3(0, 0, 0.02)
      ];
      scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), lineMat));

      // Halfway
      const halfPts = [new THREE.Vector3(52.5, 0, 0.02), new THREE.Vector3(52.5, 68, 0.02)];
      scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(halfPts), lineMat));

      // Center circle
      const circlePts = [];
      for (let i = 0; i <= 64; i++) {
        const theta = (i / 64) * Math.PI * 2;
        circlePts.push(new THREE.Vector3(52.5 + Math.cos(theta) * 9.15, 34 + Math.sin(theta) * 9.15, 0.02));
      }
      scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(circlePts), lineMat));

      // Goal nets (3D Goals!)
      function addGoal(x, yMin, yMax) {
        const goalMat = new THREE.LineBasicMaterial({ color: 0xe5e7eb, linewidth: 2 });
        const postH = 2.44; // 2.44m standard goal height
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
        
        // 3D Player Capsule/Cylinder Body
        const bodyGeo = new THREE.CylinderGeometry(0.4, 0.4, 1.75, 12);
        bodyGeo.rotateX(Math.PI / 2); // Orient upright along Z
        const bodyMat = new THREE.MeshStandardMaterial({
          color: team === 'Home' ? 0xef4444 : 0x3b82f6,
          roughness: 0.4
        });
        const body = new THREE.Mesh(bodyGeo, bodyMat);
        body.position.z = 0.88;
        group.add(body);

        // Head
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

    // ---------------- 2D CANVAS FALLBACK ----------------
    const canvas2D = document.getElementById('pitch-2d-canvas');
    const ctx2D = canvas2D.getContext('2d');
    const SCALE_X = canvas2D.width / 105;
    const SCALE_Y = canvas2D.height / 68;

    function render2D(frameData) {
      ctx2D.fillStyle = "#0c381a";
      ctx2D.fillRect(0, 0, canvas2D.width, canvas2D.height);

      // Lines
      ctx2D.strokeStyle = "rgba(255, 255, 255, 0.8)";
      ctx2D.lineWidth = 2;
      ctx2D.strokeRect(0, 0, canvas2D.width, canvas2D.height);
      ctx2D.beginPath();
      ctx2D.moveTo(canvas2D.width / 2, 0);
      ctx2D.lineTo(canvas2D.width / 2, canvas2D.height);
      ctx2D.stroke();
      ctx2D.beginPath();
      ctx2D.arc(canvas2D.width / 2, canvas2D.height / 2, 9.15 * SCALE_X, 0, Math.PI * 2);
      ctx2D.stroke();

      // Players
      frameData.players.forEach(p => {
        const cx = p.x * SCALE_X;
        const cy = (68 - p.y) * SCALE_Y;
        ctx2D.fillStyle = p.team === 'Home' ? "#ef4444" : "#3b82f6";
        ctx2D.beginPath();
        ctx2D.arc(cx, cy, 8, 0, Math.PI * 2);
        ctx2D.fill();
        ctx2D.fillStyle = "#fff";
        ctx2D.font = "bold 9px 'JetBrains Mono'";
        ctx2D.fillText(p.id, cx - 6, cy - 10);
      });

      // Ball
      const bx = frameData.ball.x * SCALE_X;
      const by = (68 - frameData.ball.y) * SCALE_Y;
      ctx2D.fillStyle = "#ffffff";
      ctx2D.beginPath();
      ctx2D.arc(bx, by, 6, 0, Math.PI * 2);
      ctx2D.fill();
    }

    // ---------------- FRAME RENDERER CONTROLLER ----------------
    function render(frameIdx) {
      const f = matchData[frameIdx - 1];
      if (!f) return;

      // Update 3D Positions if Three.js is running
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

      // Always keep 2D canvas rendered or render when activeView is 2d / three not ready
      if (activeView === '2d' || !threeInitialized) {
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
      
      document.getElementById('three-canvas-container').style.display = view === '3d' ? 'block' : 'none';
      document.getElementById('pitch-2d-canvas').style.display = view === '2d' ? 'block' : 'none';
      document.getElementById('hud-camera-info').style.display = view === '3d' ? 'block' : 'none';
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

    // Auto check if Three.js initialized successfully, otherwise default to 2D
    if (!threeInitialized) {
      console.warn("Three.js not initialized; defaulting activeView to 2d");
      switchView('2d');
    }

    // Window Resize Handling
    window.addEventListener('resize', () => {
      if (threeInitialized && camera && renderer) {
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
      }
    });

    // Render frame 1 immediately from initial embedded payload!
    render(1);

    // Fetch full 1,500 match frames asynchronously
    fetch('/api/frames')
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

@app.route("/api/frames")
def get_frames():
    return jsonify(processed_frames)

@app.route("/")
def index():
    initial_frame = processed_frames[0] if processed_frames else {}
    return render_template_string(
        HTML_TEMPLATE,
        total_frames=total_frames,
        home_pct=(home_count / total_frames) * 100.0,
        away_pct=(away_count / total_frames) * 100.0,
        turnovers=turnovers,
        initial_frame_json=json.dumps(initial_frame)
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
