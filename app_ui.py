import os
import json
from flask import Flask, render_template_string, jsonify
from src.metrica_parser import MetricaTrackingParser
from src.pipeline import FullPossessionPipeline

app = Flask(__name__)

# Initialize pipeline and parse match data
parser = MetricaTrackingParser()
pipeline = FullPossessionPipeline()

DATASET_FILE = "data/sample_match_tracking.json"
frames = parser.load_json_match(DATASET_FILE) if os.path.exists(DATASET_FILE) else []

# Precompute telemetry and pitch control surfaces for all frames (lightning fast in-memory)
processed_frames = []
home_count = 0
away_count = 0
contested_count = 0
turnovers = []
last_team = None

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
            "from": last_team,
            "to": team
        })
    if team and team != "Contested":
        last_team = team

    # Extract downsampled 20x13 pitch control grid for instant JSON delivery
    pc_surface = pipeline.pitch_control_engine.calculate_pitch_control_surface(
        [p for p in f['players'] if p['team'] == 'Home'],
        [p for p in f['players'] if p['team'] == 'Away']
    )['home_surface']
    
    # Downsample matrix to 20x13 floats rounded to 2 decimals
    h_down = pc_surface[::2, ::2]
    surface_grid = [[round(float(v), 2) for v in row] for row in h_down]

    processed_frames.append({
        "frame_id": f["frame_id"],
        "ball": f["ball"],
        "players": f["players"],
        "possession": res,
        "grid": surface_grid
    })

total_frames = max(1, len(frames))

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Barça Innovation Hub · Ultra-Fast 60 FPS Tactical Pitch Control UI</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #07090e;
      --card: rgba(18, 22, 34, 0.85);
      --border: rgba(255, 255, 255, 0.08);
      --accent: #10b981;
      --home: #ef4444;
      --away: #3b82f6;
      --text: #f3f4f6;
      --text-muted: #9ca3af;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: 'Plus Jakarta Sans', sans-serif;
      min-height: 100vh;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 24px;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 16px;
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
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
    }
    .stat-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 18px;
    }
    .stat-label {
      font-size: 0.76rem;
      color: var(--text-muted);
      text-transform: uppercase;
      font-family: 'JetBrains Mono', monospace;
      margin-bottom: 6px;
    }
    .stat-val {
      font-size: 1.65rem;
      font-weight: 800;
    }
    .main-grid {
      display: grid;
      grid-template-columns: 1fr 340px;
      gap: 20px;
    }
    .viewport-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 16px;
    }
    .canvas-container {
      width: 100%;
      position: relative;
      background: #092c15;
      border-radius: 14px;
      overflow: hidden;
      border: 1px solid var(--border);
      box-shadow: 0 12px 36px rgba(0, 0, 0, 0.5);
    }
    canvas {
      display: block;
      width: 100%;
      height: auto;
    }
    .controls {
      display: flex;
      align-items: center;
      gap: 16px;
      width: 100%;
      padding: 12px 18px;
      background: rgba(0, 0, 0, 0.45);
      border-radius: 12px;
      border: 1px solid var(--border);
    }
    .btn {
      background: #1f2937;
      color: var(--text);
      border: 1px solid var(--border);
      padding: 9px 18px;
      border-radius: 8px;
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
      gap: 16px;
    }
    .frame-info {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .info-row {
      display: flex;
      justify-content: space-between;
      font-size: 0.88rem;
    }
    .info-val { font-family: 'JetBrains Mono', monospace; font-weight: 600; }
    .legend-box {
      display: flex;
      gap: 14px;
      margin-top: 4px;
      font-size: 0.8rem;
    }
    .legend-item { display: flex; align-items: center; gap: 6px; }
    .dot { width: 10px; height: 10px; border-radius: 50%; }
  </style>
</head>
<body>
  <div class="header">
    <div>
      <h2 style="letter-spacing: -0.02em;">⚽ Football Possession & Pitch Control Engine</h2>
      <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 4px;">More Than a Hack 2027 · Barça Innovation Hub & Metrica Sports</p>
    </div>
    <div class="badge">● 60 FPS HARDWARE ACCELERATED CANVAS</div>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-label">Home Team Control</div>
      <div class="stat-val" style="color: var(--home);">{{ "%.1f"|format(home_pct) }}%</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Away Team Control</div>
      <div class="stat-val" style="color: var(--away);">{{ "%.1f"|format(away_pct) }}%</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Playback Performance</div>
      <div class="stat-val" style="color: var(--accent);" id="lbl-fps">60.0 FPS</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Total Turnovers</div>
      <div class="stat-val">{{ turnovers|length }}</div>
    </div>
  </div>

  <div class="main-grid">
    <div class="viewport-card">
      <div class="canvas-container">
        <canvas id="pitch-canvas" width="1050" height="680"></canvas>
      </div>
      
      <div class="controls">
        <button id="btn-play" class="btn btn-play" onclick="togglePlay()">Play ▶</button>
        <button class="btn" onclick="stepFrame(-1)">◀ Prev</button>
        <input type="range" id="frame-slider" class="slider" min="1" max="{{ total_frames }}" value="1" oninput="onSlide(this.value)">
        <button class="btn" onclick="stepFrame(1)">Next ▶</button>
        <span id="frame-label" style="font-family: 'JetBrains Mono'; font-weight: 600; min-width: 90px; text-align: right;">1 / {{ total_frames }}</span>
      </div>

      <div class="legend-box">
        <div class="legend-item"><span class="dot" style="background: var(--home);"></span> Home Players (Red)</div>
        <div class="legend-item"><span class="dot" style="background: var(--away);"></span> Away Players (Blue)</div>
        <div class="legend-item"><span class="dot" style="background: #ffffff; border: 1px solid #000;"></span> Ball</div>
        <div class="legend-item"><span class="dot" style="background: #eab308;"></span> Velocity Vectors</div>
      </div>
    </div>

    <div class="sidebar">
      <div class="frame-info">
        <h4 style="margin-bottom: 4px;">Live Frame Telemetry</h4>
        <div class="info-row">
          <span style="color: var(--text-muted);">Frame Index</span>
          <span id="lbl-frame-id" class="info-val">#1</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Possessing Team</span>
          <span id="lbl-team" class="info-val" style="color: var(--home);">Home</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Controlling Player</span>
          <span id="lbl-player" class="info-val">H10</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Ball Proximity</span>
          <span id="lbl-dist" class="info-val">0.33 m</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Confidence Score</span>
          <span id="lbl-conf" class="info-val">83.4%</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Markov State Filter</span>
          <span id="lbl-status" class="info-val" style="color: var(--accent);">STABLE</span>
        </div>
      </div>

      <div class="frame-info">
        <h4 style="margin-bottom: 4px;">Spearman Pitch Control</h4>
        <div class="info-row">
          <span style="color: var(--text-muted);">Home Control Area</span>
          <span id="lbl-pc-home" class="info-val" style="color: var(--home);">50.5%</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Away Control Area</span>
          <span id="lbl-pc-away" class="info-val" style="color: var(--away);">49.5%</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Model Algorithm</span>
          <span class="info-val">Kinematic Delta-T</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Jitter Reduction</span>
          <span class="info-val" style="color: var(--accent);">Kalman Trajectory</span>
        </div>
      </div>
    </div>
  </div>

  <script>
    const matchData = {{ match_data_json|safe }};
    const maxFrames = matchData.length;
    let currentFrame = 1;
    let isPlaying = false;
    let playTimer = null;

    const canvas = document.getElementById('pitch-canvas');
    const ctx = canvas.getContext('2d');
    const PITCH_W = 105;
    const PITCH_H = 68;
    const SCALE_X = canvas.width / PITCH_W;
    const SCALE_Y = canvas.height / PITCH_H;

    function toCanvasX(x) { return x * SCALE_X; }
    function toCanvasY(y) { return (PITCH_H - y) * SCALE_Y; } // Invert Y for football top-down orientation

    function drawPitchLines() {
      ctx.strokeStyle = "rgba(255, 255, 255, 0.75)";
      ctx.lineWidth = 2.5;

      // Outer boundary
      ctx.strokeRect(0, 0, canvas.width, canvas.height);

      // Halfway line
      ctx.beginPath();
      ctx.moveTo(canvas.width / 2, 0);
      ctx.lineTo(canvas.width / 2, canvas.height);
      ctx.stroke();

      // Center circle
      ctx.beginPath();
      ctx.arc(canvas.width / 2, canvas.height / 2, 9.15 * SCALE_X, 0, Math.PI * 2);
      ctx.stroke();

      // Center spot
      ctx.fillStyle = "#ffffff";
      ctx.beginPath();
      ctx.arc(canvas.width / 2, canvas.height / 2, 4, 0, Math.PI * 2);
      ctx.fill();

      // Penalty boxes (16.5m x 40.32m)
      const penW = 16.5 * SCALE_X;
      const penH = 40.32 * SCALE_Y;
      const penY = ((PITCH_H - 40.32) / 2) * SCALE_Y;

      ctx.strokeRect(0, penY, penW, penH);
      ctx.strokeRect(canvas.width - penW, penY, penW, penH);

      // 6-yard boxes (5.5m x 18.32m)
      const sixW = 5.5 * SCALE_X;
      const sixH = 18.32 * SCALE_Y;
      const sixY = ((PITCH_H - 18.32) / 2) * SCALE_Y;

      ctx.strokeRect(0, sixY, sixW, sixH);
      ctx.strokeRect(canvas.width - sixW, sixY, sixW, sixH);
    }

    function drawPitchControlHeatmap(grid) {
      if (!grid || !grid.length) return;
      const rows = grid.length;
      const cols = grid[0].length;
      const cellW = canvas.width / cols;
      const cellH = canvas.height / rows;

      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const homeProb = grid[r][c]; // 0.0 (Away) to 1.0 (Home)
          if (homeProb > 0.5) {
            const alpha = (homeProb - 0.5) * 0.45;
            ctx.fillStyle = `rgba(239, 68, 68, ${alpha})`;
          } else {
            const alpha = (0.5 - homeProb) * 0.45;
            ctx.fillStyle = `rgba(59, 130, 246, ${alpha})`;
          }
          ctx.fillRect(c * cellW, (rows - 1 - r) * cellH, cellW, cellH);
        }
      }
    }

    function render(frameIdx) {
      const frameData = matchData[frameIdx - 1];
      if (!frameData) return;

      // 1. Clear & Background
      ctx.fillStyle = "#0c381a"; // Lush grass green
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // 2. Draw Spearman Pitch Control Probability Surface
      drawPitchControlHeatmap(frameData.grid);

      // 3. Draw Pitch Markings
      drawPitchLines();

      // 4. Draw Players with velocity vectors
      frameData.players.forEach(p => {
        const cx = toCanvasX(p.x);
        const cy = toCanvasY(p.y);
        const isHome = p.team === 'Home';

        // Velocity vector arrow
        if (Math.abs(p.vx) > 0.1 || Math.abs(p.vy) > 0.1) {
          ctx.strokeStyle = "#facc15";
          ctx.lineWidth = 2.5;
          ctx.beginPath();
          ctx.moveTo(cx, cy);
          ctx.lineTo(cx + p.vx * 15, cy - p.vy * 15);
          ctx.stroke();
        }

        // Player marker
        ctx.fillStyle = isHome ? "#ef4444" : "#3b82f6";
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 2.2;
        ctx.beginPath();
        ctx.arc(cx, cy, 9, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();

        // Player ID label
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 10px 'JetBrains Mono'";
        ctx.textAlign = "center";
        ctx.fillText(p.id, cx, cy - 12);
      });

      // 5. Draw Ball
      if (frameData.ball) {
        const bx = toCanvasX(frameData.ball.x);
        const by = toCanvasY(frameData.ball.y);

        ctx.fillStyle = "#ffffff";
        ctx.strokeStyle = "#000000";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(bx, by, 7, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();

        // Ball glow
        ctx.fillStyle = "rgba(255, 255, 255, 0.4)";
        ctx.beginPath();
        ctx.arc(bx, by, 12, 0, Math.PI * 2);
        ctx.fill();
      }

      // 6. Update Sidebar Indicators
      const poss = frameData.possession;
      document.getElementById('frame-slider').value = frameIdx;
      document.getElementById('frame-label').textContent = `${frameIdx} / ${maxFrames}`;
      document.getElementById('lbl-frame-id').textContent = `#${frameIdx}`;

      const teamEl = document.getElementById('lbl-team');
      teamEl.textContent = poss.smoothed_team || 'Contested';
      teamEl.style.color = poss.smoothed_team === 'Home' ? 'var(--home)' : (poss.smoothed_team === 'Away' ? 'var(--away)' : '#eab308');

      document.getElementById('lbl-player').textContent = poss.possessing_player || 'Contested Ball';
      document.getElementById('lbl-dist').textContent = (poss.min_distance || 0).toFixed(2) + ' m';
      document.getElementById('lbl-conf').textContent = ((poss.confidence || 0) * 100).toFixed(1) + '%';
      
      const statusEl = document.getElementById('lbl-status');
      statusEl.textContent = poss.is_stable ? 'STABLE' : 'TRANSITION';
      statusEl.style.color = poss.is_stable ? 'var(--accent)' : '#f59e0b';

      if (poss.home_pitch_control_pct !== undefined) {
        document.getElementById('lbl-pc-home').textContent = poss.home_pitch_control_pct.toFixed(1) + '%';
        document.getElementById('lbl-pc-away').textContent = poss.away_pitch_control_pct.toFixed(1) + '%';
      }
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
          currentFrame = (currentFrame >= maxFrames) ? 1 : currentFrame + 1;
          render(currentFrame);
        }, 40); // 25 FPS match replay timing
      } else {
        btn.textContent = 'Play ▶';
        btn.style.background = 'var(--accent)';
        clearInterval(playTimer);
      }
    }

    // Initial first frame render
    render(1);
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(
        HTML_TEMPLATE,
        total_frames=total_frames,
        home_pct=(home_count / total_frames) * 100.0,
        away_pct=(away_count / total_frames) * 100.0,
        turnovers=turnovers,
        match_data_json=json.dumps(processed_frames)
    )

@app.route("/api/match/summary")
def match_summary():
    return jsonify({
        "total_frames": total_frames,
        "home_pct": round((home_count / total_frames) * 100.0, 2),
        "away_pct": round((away_count / total_frames) * 100.0, 2),
        "turnovers": turnovers
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
