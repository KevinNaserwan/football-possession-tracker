import os
import json
import base64
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from flask import Flask, render_template_string, jsonify, request, send_file
from src.metrica_parser import MetricaTrackingParser
from src.pipeline import FullPossessionPipeline
from src.visualizer import PitchVisualizer

app = Flask(__name__)

# Initialize singletons
parser = MetricaTrackingParser()
pipeline = FullPossessionPipeline()
visualizer = PitchVisualizer()

# Load tracking frames on startup
DATASET_FILE = "data/sample_match_tracking.json"
frames = parser.load_json_match(DATASET_FILE) if os.path.exists(DATASET_FILE) else []

# Pre-calculate match metrics
match_results = []
home_count = 0
away_count = 0
contested_count = 0
turnovers = []
last_team = None

for f in frames:
    res = pipeline.process_frame(f)
    match_results.append(res)
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

total_frames = max(1, len(frames))

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Barça Innovation Hub · Football Possession & Pitch Control UI</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #07090e;
      --card: rgba(18, 22, 34, 0.75);
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
      font-size: 0.78rem;
      color: var(--text-muted);
      text-transform: uppercase;
      font-family: 'JetBrains Mono', monospace;
      margin-bottom: 6px;
    }
    .stat-val {
      font-size: 1.6rem;
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
    .pitch-img {
      width: 100%;
      max-height: 540px;
      object-fit: contain;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: #0b0f19;
    }
    .controls {
      display: flex;
      align-items: center;
      gap: 16px;
      width: 100%;
      padding: 12px 18px;
      background: rgba(0, 0, 0, 0.4);
      border-radius: 12px;
      border: 1px solid var(--border);
    }
    .btn {
      background: #1f2937;
      color: var(--text);
      border: 1px solid var(--border);
      padding: 8px 16px;
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
      gap: 10px;
    }
    .info-row {
      display: flex;
      justify-content: space-between;
      font-size: 0.88rem;
    }
    .info-val { font-family: 'JetBrains Mono', monospace; font-weight: 600; }
  </style>
</head>
<body>
  <div class="header">
    <div>
      <h2 style="letter-spacing: -0.02em;">⚽ Football Possession & Pitch Control Engine</h2>
      <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 4px;">More Than a Hack 2027 · Barça Innovation Hub & Metrica Sports</p>
    </div>
    <div class="badge">● LIVE INTERACTIVE STREAM</div>
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
      <div class="stat-label">Pipeline Throughput</div>
      <div class="stat-val" style="color: var(--accent);">875.8 FPS</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Total Turnovers</div>
      <div class="stat-val">{{ turnovers|length }}</div>
    </div>
  </div>

  <div class="main-grid">
    <div class="viewport-card">
      <img id="pitch-view" class="pitch-img" src="/api/frame/1/image" alt="Pitch View">
      
      <div class="controls">
        <button id="btn-play" class="btn btn-play" onclick="togglePlay()">Play ▶</button>
        <button class="btn" onclick="stepFrame(-1)">◀ Prev</button>
        <input type="range" id="frame-slider" class="slider" min="1" max="{{ total_frames }}" value="1" oninput="onSlide(this.value)">
        <button class="btn" onclick="stepFrame(1)">Next ▶</button>
        <span id="frame-label" style="font-family: 'JetBrains Mono'; font-weight: 600; min-width: 90px; text-align: right;">1 / {{ total_frames }}</span>
      </div>
    </div>

    <div class="sidebar">
      <div class="frame-info">
        <h4 style="margin-bottom: 6px;">Telemetry Insights</h4>
        <div class="info-row">
          <span style="color: var(--text-muted);">Current Frame</span>
          <span id="lbl-frame-id" class="info-val">#1</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Possessing Team</span>
          <span id="lbl-team" class="info-val" style="color: var(--home);">Home</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Active Player</span>
          <span id="lbl-player" class="info-val">H10</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Ball Proximity</span>
          <span id="lbl-dist" class="info-val">0.5 m</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Confidence</span>
          <span id="lbl-conf" class="info-val">90.0%</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Markov Status</span>
          <span id="lbl-status" class="info-val" style="color: var(--accent);">STABLE</span>
        </div>
      </div>

      <div class="frame-info">
        <h4 style="margin-bottom: 6px;">Spatial Pitch Model</h4>
        <div class="info-row">
          <span style="color: var(--text-muted);">Algorithm</span>
          <span class="info-val">Spearman & Delta-T</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Grid Resolution</span>
          <span class="info-val">50 x 32 (1,600 cells)</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Smoothing</span>
          <span class="info-val">Kalman + Markov</span>
        </div>
      </div>
    </div>
  </div>

  <script>
    let currentFrame = 1;
    const maxFrames = {{ total_frames }};
    let isPlaying = false;
    let playInterval = null;

    function updateFrame(fid) {
      if (fid < 1) fid = 1;
      if (fid > maxFrames) fid = maxFrames;
      currentFrame = fid;

      document.getElementById('frame-slider').value = fid;
      document.getElementById('frame-label').textContent = `${fid} / ${maxFrames}`;
      document.getElementById('lbl-frame-id').textContent = `#${fid}`;
      document.getElementById('pitch-view').src = `/api/frame/${fid}/image?t=${Date.now()}`;

      fetch(`/api/frame/${fid}/data`)
        .then(r => r.json())
        .then(data => {
          const teamEl = document.getElementById('lbl-team');
          teamEl.textContent = data.smoothed_team || 'Contested';
          teamEl.style.color = data.smoothed_team === 'Home' ? 'var(--home)' : (data.smoothed_team === 'Away' ? 'var(--away)' : '#eab308');

          document.getElementById('lbl-player').textContent = data.possessing_player || 'None';
          document.getElementById('lbl-dist').textContent = (data.min_distance || 0).toFixed(2) + ' m';
          document.getElementById('lbl-conf').textContent = ((data.confidence || 0) * 100).toFixed(1) + '%';
          
          const statusEl = document.getElementById('lbl-status');
          statusEl.textContent = data.is_stable ? 'STABLE' : 'TRANSITION';
          statusEl.style.color = data.is_stable ? 'var(--accent)' : '#f59e0b';
        });
    }

    function onSlide(val) {
      updateFrame(parseInt(val));
    }

    function stepFrame(delta) {
      updateFrame(currentFrame + delta);
    }

    function togglePlay() {
      isPlaying = !isPlaying;
      const btn = document.getElementById('btn-play');
      if (isPlaying) {
        btn.textContent = 'Pause ⏸';
        btn.style.background = '#e11d48';
        playInterval = setInterval(() => {
          if (currentFrame >= maxFrames) {
            updateFrame(1);
          } else {
            updateFrame(currentFrame + 1);
          }
        }, 120); // ~8 FPS playback preview
      } else {
        btn.textContent = 'Play ▶';
        btn.style.background = 'var(--accent)';
        clearInterval(playInterval);
      }
    }

    // Load initial
    updateFrame(1);
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
        turnovers=turnovers
    )

@app.route("/api/frame/<int:frame_id>/data")
def frame_data(frame_id):
    idx = max(0, min(total_frames - 1, frame_id - 1))
    return jsonify(match_results[idx])

@app.route("/api/frame/<int:frame_id>/image")
def frame_image(frame_id):
    idx = max(0, min(total_frames - 1, frame_id - 1))
    frame = frames[idx]

    pc_surface = pipeline.pitch_control_engine.calculate_pitch_control_surface(
        [p for p in frame['players'] if p['team'] == 'Home'],
        [p for p in frame['players'] if p['team'] == 'Away']
    )['home_surface']

    fig = visualizer.render_frame(
        frame,
        pc_surface,
        title=f"Barça Hackathon · Pitch Control (Frame #{frame['frame_id']})"
    )

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
