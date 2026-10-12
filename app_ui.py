import os
import json
import math
from flask import Flask, render_template_string, jsonify
from src.metrica_parser import MetricaTrackingParser
from src.pipeline import FullPossessionPipeline

app = Flask(__name__)

# Initialize parser and pipeline
parser = MetricaTrackingParser()
pipeline = FullPossessionPipeline()

MATCH_CATALOG = {
    "MATCH_EL_CLASICO": {
        "id": "MATCH_EL_CLASICO",
        "title": "⚽ Match 1: FC Barcelona vs Real Madrid (90' Full Match Timeline & 89' Winner)",
        "file": "data/match_el_clasico.json"
    },
    "MATCH_UCL_TACTICAL": {
        "id": "MATCH_UCL_TACTICAL",
        "title": "🏆 Match 2: Man City vs Inter Milan (90' UCL Tactical Clash & Counter)",
        "file": "data/match_ucl_tactical.json"
    },
    "MATCH_WORLD_CUP": {
        "id": "MATCH_WORLD_CUP",
        "title": "🌍 Match 3: Argentina vs France (90' World Cup Final Showdown & Thrills)",
        "file": "data/match_world_cup.json"
    }
}

MATCH_CACHE = {}

def process_match_file(filepath):
    if not os.path.exists(filepath):
        filepath = "data/sample_match_tracking.json"

    metadata = {}
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw_json = json.load(f)
                metadata = raw_json.get("metadata", {})
        except Exception as e:
            print(f"Error reading metadata from {filepath}: {e}")

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
            "match_time": f.get("match_time", "00:00"),
            "ball": f["ball"],
            "players": f["players"],
            "possession": res
        })

    t_frames = max(1, len(frames))
    return {
        "metadata": metadata,
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
  <title>Barça Innovation Hub · 3D Tactical Pitch Control & Kinematics Engine</title>
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
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
      --away: #eab308;
      --text: #f3f4f6;
      --text-muted: #9ca3af;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      color: var(--text);
      font-family: 'Plus Jakarta Sans', sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      padding: 16px 24px;
      overflow-x: hidden;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border);
      flex-wrap: wrap;
      gap: 12px;
    }
    .badge {
      background: rgba(16, 185, 129, 0.12);
      color: var(--accent);
      padding: 4px 10px;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 700;
      border: 1px solid rgba(16, 185, 129, 0.3);
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .view-toggle {
      display: flex;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 8px;
      padding: 3px;
      border: 1px solid var(--border);
    }
    .view-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 6px 14px;
      border-radius: 6px;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }
    .view-btn.active {
      background: var(--accent);
      color: #000;
      font-weight: 700;
    }

    /* BROADCAST SCOREBOARD (Papan Skor) */
    .scoreboard-wrap {
      display: flex;
      flex-direction: column;
      align-items: center;
      margin-bottom: 12px;
      gap: 8px;
      width: 100%;
    }
    .scoreboard-card {
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: linear-gradient(135deg, rgba(17, 24, 39, 0.94), rgba(15, 23, 42, 0.98));
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 12px;
      padding: 10px 22px;
      box-shadow: 0 10px 28px rgba(0, 0, 0, 0.6), 0 0 1px rgba(255, 255, 255, 0.2);
      width: 100%;
      max-width: 860px;
      backdrop-filter: blur(12px);
    }
    .sb-team {
      display: flex;
      align-items: center;
      gap: 12px;
      flex: 1;
    }
    .sb-team.home { justify-content: flex-start; }
    .sb-team.away { justify-content: flex-end; }
    .sb-badge {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.92rem;
      font-weight: 800;
      padding: 5px 11px;
      border-radius: 7px;
      letter-spacing: 0.05em;
      box-shadow: 0 2px 6px rgba(0,0,0,0.4);
    }
    .home-badge {
      background: #ef4444;
      color: #ffffff;
      border: 1px solid rgba(239, 68, 68, 0.4);
    }
    .away-badge {
      background: #eab308;
      color: #0f172a;
      border: 1px solid rgba(234, 179, 8, 0.4);
    }
    .sb-name {
      font-weight: 700;
      font-size: 1.02rem;
      letter-spacing: -0.01em;
      white-space: nowrap;
    }
    .sb-center {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-width: 170px;
    }
    .sb-score-box {
      display: flex;
      align-items: center;
      gap: 12px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 2.1rem;
      font-weight: 800;
      line-height: 1;
    }
    .sb-score {
      min-width: 26px;
      text-align: center;
      color: #f8fafc;
      text-shadow: 0 0 12px rgba(255, 255, 255, 0.3);
    }
    .sb-divider {
      color: rgba(255, 255, 255, 0.35);
      font-size: 1.5rem;
    }
    .sb-clock-box {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 4px;
    }
    .sb-period {
      font-size: 0.70rem;
      font-weight: 700;
      color: #94a3b8;
      background: rgba(255, 255, 255, 0.06);
      padding: 2px 7px;
      border-radius: 4px;
      letter-spacing: 0.05em;
    }
    .sb-time {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.88rem;
      font-weight: 700;
      color: #38bdf8;
    }
    .goal-alert-banner {
      background: linear-gradient(90deg, #ef4444, #f59e0b, #ef4444);
      color: #ffffff;
      padding: 6px 20px;
      border-radius: 20px;
      font-size: 0.86rem;
      font-weight: 800;
      letter-spacing: 0.02em;
      box-shadow: 0 4px 20px rgba(239, 68, 68, 0.5);
      animation: pulseGlow 1.4s infinite alternate;
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }
    @keyframes pulseGlow {
      from { transform: scale(1); filter: drop-shadow(0 0 4px rgba(245, 158, 11, 0.6)); }
      to { transform: scale(1.02); filter: drop-shadow(0 0 12px rgba(239, 68, 68, 0.9)); }
    }

    /* STADIUM RUMBLE VIBRATION EFFECT */
    @keyframes stadiumRumble {
      0% { transform: translate(0, 0) rotate(0deg); }
      15% { transform: translate(-3px, 2px) rotate(-0.25deg); }
      30% { transform: translate(3px, -2px) rotate(0.25deg); }
      45% { transform: translate(-2px, -3px) rotate(-0.2deg); }
      60% { transform: translate(3px, 2px) rotate(0.2deg); }
      75% { transform: translate(-2px, 1px) rotate(-0.1deg); }
      90% { transform: translate(2px, -1px) rotate(0.1deg); }
      100% { transform: translate(0, 0) rotate(0deg); }
    }
    .stadium-rumble {
      animation: stadiumRumble 0.12s ease-in-out infinite !important;
      border: 2px solid #ef4444 !important;
      box-shadow: 0 0 40px rgba(239, 68, 68, 0.7), inset 0 0 25px rgba(239, 68, 68, 0.4) !important;
    }

    /* CELEBRATION GOAL POPUP MODAL */
    .goal-popup-overlay {
      position: absolute;
      top: 0; left: 0; right: 0; bottom: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, 0.55);
      backdrop-filter: blur(5px);
      z-index: 100;
      pointer-events: auto;
      cursor: pointer;
      animation: fadeIn 0.25s ease-out;
    }
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    .goal-popup-card {
      background: linear-gradient(135deg, rgba(239, 68, 68, 0.96), rgba(185, 28, 28, 0.98), rgba(245, 158, 11, 0.96));
      border: 2px solid rgba(255, 255, 255, 0.6);
      border-radius: 20px;
      padding: 22px 38px;
      text-align: center;
      box-shadow: 0 0 50px rgba(239, 68, 68, 0.8), 0 20px 40px rgba(0, 0, 0, 0.8);
      animation: popBounce 0.45s cubic-bezier(0.175, 0.885, 0.32, 1.275);
      color: #ffffff;
      max-width: 480px;
      user-select: none;
    }
    @keyframes popBounce {
      0% { transform: scale(0.3) rotate(-4deg); opacity: 0; }
      65% { transform: scale(1.08) rotate(1.5deg); opacity: 1; }
      100% { transform: scale(1) rotate(0deg); opacity: 1; }
    }
    .goal-popup-burst {
      font-size: 2.2rem;
      margin-bottom: 2px;
      animation: pulseBurst 0.6s infinite alternate;
    }
    @keyframes pulseBurst {
      from { transform: scale(0.9); }
      to { transform: scale(1.15); }
    }
    .goal-popup-title {
      font-family: 'JetBrains Mono', monospace;
      font-size: 2.6rem;
      font-weight: 900;
      letter-spacing: 0.08em;
      text-shadow: 0 0 20px rgba(255, 255, 255, 0.8), 0 4px 10px rgba(0, 0, 0, 0.5);
      line-height: 1;
      margin: 4px 0;
    }
    .goal-popup-scorer {
      font-size: 1.35rem;
      font-weight: 800;
      letter-spacing: 0.02em;
      margin: 6px 0;
      color: #fef08a;
      text-shadow: 0 2px 8px rgba(0,0,0,0.5);
    }
    .goal-popup-details {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      margin: 10px 0;
    }
    .popup-badge {
      background: #ffffff;
      color: #b91c1c;
      padding: 4px 12px;
      border-radius: 9999px;
      font-weight: 800;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.9rem;
    }
    .popup-stat {
      font-weight: 600;
      font-size: 0.92rem;
    }
    .popup-speed {
      background: rgba(0, 0, 0, 0.45);
      padding: 4px 10px;
      border-radius: 6px;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 800;
      color: #fbbf24;
      font-size: 0.92rem;
    }
    .goal-popup-score {
      font-family: 'JetBrains Mono', monospace;
      font-size: 1.7rem;
      font-weight: 900;
      margin-top: 6px;
      letter-spacing: 0.06em;
      text-shadow: 0 0 10px rgba(255,255,255,0.4);
    }

    /* TACTICAL CHAPTERS BAR */
    .chapters-wrap::-webkit-scrollbar,
    .chapters-bar::-webkit-scrollbar {
      height: 4px;
    }
    .chapters-wrap::-webkit-scrollbar-thumb,
    .chapters-bar::-webkit-scrollbar-thumb {
      background: rgba(255, 255, 255, 0.18);
      border-radius: 4px;
    }
    .chapters-wrap {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 12px;
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 6px 14px;
      overflow-x: auto;
    }
    .chapters-title {
      font-size: 0.78rem;
      font-weight: 700;
      color: var(--text-muted);
      white-space: nowrap;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .chapters-bar {
      display: flex;
      align-items: center;
      gap: 8px;
      overflow-x: auto;
      flex: 1;
    }
    .chapter-btn {
      background: rgba(255, 255, 255, 0.05);
      color: var(--text-muted);
      border: 1px solid var(--border);
      padding: 5px 12px;
      border-radius: 7px;
      font-size: 0.77rem;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.15s ease;
    }
    .chapter-btn:hover {
      background: rgba(255, 255, 255, 0.12);
      color: #ffffff;
      border-color: rgba(255, 255, 255, 0.3);
      transform: translateY(-1px);
    }
    .chapter-btn.active {
      background: rgba(16, 185, 129, 0.2);
      color: #10b981;
      border-color: rgba(16, 185, 129, 0.6);
      font-weight: 700;
    }
    .chapter-btn.goal-chapter {
      background: rgba(239, 68, 68, 0.18);
      color: #f87171;
      border-color: rgba(239, 68, 68, 0.5);
      font-weight: 700;
    }
    .chapter-btn.goal-chapter:hover {
      background: rgba(239, 68, 68, 0.35);
      color: #ffffff;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin-bottom: 14px;
    }
    .stat-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 10px 14px;
    }
    .stat-label {
      font-size: 0.74rem;
      color: var(--text-muted);
      text-transform: uppercase;
      font-weight: 700;
      letter-spacing: 0.04em;
    }
    .stat-val {
      font-family: 'JetBrains Mono', monospace;
      font-size: 1.25rem;
      font-weight: 700;
      margin-top: 3px;
    }
    .main-grid {
      display: grid;
      grid-template-columns: 1fr 340px;
      gap: 18px;
      flex: 1;
    }
    @media (max-width: 1080px) {
      .main-grid { grid-template-columns: 1fr; }
    }
    .viewport-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      position: relative;
    }
    .view-stage {
      position: relative;
      width: 100%;
      height: 520px;
      background: #030508;
      border-radius: 10px;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.05);
    }
    #three-canvas-container {
      width: 100%;
      height: 100%;
      display: block;
    }
    #pitch-2d-canvas {
      width: 100%;
      height: 100%;
      display: none;
    }
    .hud-overlay {
      position: absolute;
      top: 10px;
      left: 12px;
      background: rgba(0, 0, 0, 0.65);
      border: 1px solid var(--border);
      padding: 7px 12px;
      border-radius: 8px;
      backdrop-filter: blur(8px);
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.78rem;
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
      <h2 style="letter-spacing: -0.02em;">⚽ 3D Tactical Pitch Control & Kinematics Engine</h2>
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
      <div class="badge">● 90' BROADCAST SYNC</div>
    </div>
  </div>

  <!-- BROADCAST SCOREBOARD (Papan Skor) -->
  <div class="scoreboard-wrap">
    <div class="scoreboard-card">
      <div class="sb-team home">
        <span class="sb-badge home-badge" id="sb-home-badge">{{ metadata.home_team.badge|default('BAR') }}</span>
        <span class="sb-name" id="sb-home-name">{{ metadata.home_team.name|default('FC Barcelona') }}</span>
      </div>
      <div class="sb-center">
        <div class="sb-score-box">
          <span class="sb-score" id="sb-score-home">0</span>
          <span class="sb-divider">:</span>
          <span class="sb-score" id="sb-score-away">0</span>
        </div>
        <div class="sb-clock-box">
          <span class="sb-period" id="sb-period">1ST HALF</span>
          <span class="sb-time" id="sb-time">00:00</span>
        </div>
      </div>
      <div class="sb-team away">
        <span class="sb-name" id="sb-away-name">{{ metadata.away_team.name|default('Real Madrid') }}</span>
        <span class="sb-badge away-badge" id="sb-away-badge">{{ metadata.away_team.badge|default('RMA') }}</span>
      </div>
    </div>
    <div id="goal-alert-banner" class="goal-alert-banner" style="display: none;">
      ⚽ <span id="goal-alert-text">GOAL! R. Lewandowski (89') · Bullet Strike (112.5 km/h)</span>
    </div>
  </div>

  <!-- TACTICAL CHAPTERS BAR (Full 90-Minute Quick Navigator) -->
  <div class="chapters-wrap">
    <div class="chapters-title">⚡ 90' Chapters:</div>
    <div class="chapters-bar" id="chapters-bar">
      {% for ch in metadata.chapters|default([]) %}
        <button class="chapter-btn {% if 'GOAL' in ch.label %}goal-chapter{% endif %}" data-min="{{ ch.min }}" onclick="jumpToMinute({{ ch.min }})">{{ ch.label }}</button>
      {% endfor %}
    </div>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-label">Match Clock</div>
      <div class="stat-val" style="color: #60a5fa;" id="stat-clock">00:00</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Home Territory Control</div>
      <div class="stat-val" style="color: var(--home);" id="stat-pc-home">{{ "%.1f"|format(home_pct) }}%</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Away Territory Control</div>
      <div class="stat-val" style="color: var(--away);" id="stat-pc-away">{{ "%.1f"|format(away_pct) }}%</div>
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
      <div class="view-stage" id="main-view-stage">
        <div class="hud-overlay" id="hud-camera-info">
          🎥 3D Orbit Camera: Left Click to Rotate | Right Click to Pan | Scroll to Zoom
        </div>
        <div id="three-canvas-container"></div>
        <canvas id="pitch-2d-canvas" width="1050" height="680"></canvas>

        <!-- CELEBRATION GOAL POPUP MODAL -->
        <div id="goal-popup-modal" class="goal-popup-overlay" style="display: none;" onclick="this.style.display='none'">
          <div class="goal-popup-card">
            <div class="goal-popup-burst">💥 ⚽ 💥</div>
            <div class="goal-popup-title">GOAAALLL!</div>
            <div class="goal-popup-scorer" id="popup-scorer-name">ROBERT LEWANDOWSKI</div>
            <div class="goal-popup-details">
              <span class="popup-badge" id="popup-minute-badge">89'</span>
              <span class="popup-stat" id="popup-type-stat">Top-Corner Bullet Strike</span>
              <span class="popup-speed" id="popup-speed-stat">112.5 km/h</span>
            </div>
            <div class="goal-popup-score" id="popup-score-display">FC BARCELONA 1 - 0 REAL MADRID</div>
            <div style="font-size: 0.72rem; color: rgba(255,255,255,0.7); margin-top: 8px;">(Click anywhere to dismiss)</div>
          </div>
        </div>
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
        💡 <strong>Broadcast-Grade Kinematics & 90-Minute Simulation:</strong> Trajektori bola mengikuti hukum fisika riil (dekselerasi gesekan rumput alami, umpan akurat kaki-ke-kaki, <em>cross</em> parabolik melengkung Z hingga 5.4m, & <em>power strike</em> roket 112+ km/h). Gunakan <strong>Papan Skor</strong> dan <strong>90' Chapters</strong> di atas untuk berpindah momen taktis instan!
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
        <div class="info-row" style="margin-top: 4px;">
          <span style="color: var(--text-muted);">Flight Elevation (Z)</span>
          <span id="lbl-z-val" class="info-val">0.00 m</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Ball State</span>
          <span id="lbl-ball-state" class="info-val" style="color: #facc15;">GROUND TIKI-TAKA</span>
        </div>
      </div>

      <div class="frame-info">
        <h4 style="margin-bottom: 2px;">Possession State</h4>
        <div class="info-row">
          <span style="color: var(--text-muted);">Controlling Team</span>
          <span id="lbl-team" class="info-val" style="color: var(--home);">Home</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Primary Player</span>
          <span id="lbl-player" class="info-val">H10 (Lewandowski)</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Ball Proximity</span>
          <span id="lbl-dist" class="info-val">0.42 m</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Markov Filter Stability</span>
          <span id="lbl-status" class="info-val" style="color: var(--accent);">STABLE</span>
        </div>
      </div>

      <div class="frame-info">
        <h4 style="margin-bottom: 2px;">Pitch Control (Voronoi/Spearman)</h4>
        <div class="info-row">
          <span style="color: var(--text-muted);">Home Domination</span>
          <span id="lbl-pc-home" class="info-val" style="color: var(--home);">{{ "%.1f"|format(home_pct) }}%</span>
        </div>
        <div class="info-row">
          <span style="color: var(--text-muted);">Away Domination</span>
          <span id="lbl-pc-away" class="info-val" style="color: var(--away);">{{ "%.1f"|format(away_pct) }}%</span>
        </div>
      </div>
    </div>
  </div>

  <script>
    const initialFrame = {{ initial_frame_json|safe }};
    let currentMetadata = {{ initial_meta_json|safe }};
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

      function addGoal(x, yMin, yMax, dir) {
        const postMat = new THREE.LineBasicMaterial({ color: 0xffffff, linewidth: 3 });
        const postH = 2.44;
        const depth = dir * 2.5;

        // Front Goal Mouth
        const gPts = [
          new THREE.Vector3(x, yMin, 0),
          new THREE.Vector3(x, yMin, postH),
          new THREE.Vector3(x, yMax, postH),
          new THREE.Vector3(x, yMax, 0)
        ];
        scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(gPts), postMat));

        // Back Netting Box
        const netMat = new THREE.LineBasicMaterial({ color: 0x94a3b8, transparent: true, opacity: 0.5 });
        const netPts = [
          new THREE.Vector3(x, yMin, postH),
          new THREE.Vector3(x + depth, yMin, postH * 0.8),
          new THREE.Vector3(x + depth, yMax, postH * 0.8),
          new THREE.Vector3(x, yMax, postH),
          new THREE.Vector3(x + depth, yMax, postH * 0.8),
          new THREE.Vector3(x + depth, yMax, 0),
          new THREE.Vector3(x + depth, yMin, 0),
          new THREE.Vector3(x + depth, yMin, postH * 0.8)
        ];
        scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(netPts), netMat));
      }
      addGoal(0, 30.34, 37.66, -1);
      addGoal(105, 30.34, 37.66, 1);
    }
    if (threeInitialized) create3DPitchLines();

    if (threeInitialized) {
      ballMesh = new THREE.Mesh(
        new THREE.SphereGeometry(0.55, 16, 16),
        new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3, metalness: 0.1 })
      );
      ballMesh.castShadow = true;
      scene.add(ballMesh);

      ballShadow = new THREE.Mesh(
        new THREE.CircleGeometry(0.55, 16),
        new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.55 })
      );
      ballShadow.position.set(0, 0, 0.03);
      scene.add(ballShadow);

      // Continuous Animation Loop for smooth 3D OrbitControls and rendering
      function animateThree() {
        requestAnimationFrame(animateThree);
        if (controls) controls.update();
        if (activeView === '3d' && renderer && scene && camera) {
          renderer.render(scene, camera);
        }
      }
      animateThree();
    }

    function getOrCreatePlayerMesh(id, team) {
      if (!threeInitialized) return null;
      if (playerMeshes[id]) return playerMeshes[id];

      const pGroup = new THREE.Group();
      const color = team === 'Home' ? 0xef4444 : 0xeab308;
      
      const body = new THREE.Mesh(
        new THREE.CylinderGeometry(0.42, 0.42, 1.7, 16),
        new THREE.MeshStandardMaterial({ color: color, roughness: 0.5 })
      );
      body.rotation.x = Math.PI / 2;
      body.position.z = 0.85;
      body.castShadow = true;
      pGroup.add(body);

      const head = new THREE.Mesh(
        new THREE.SphereGeometry(0.3, 16, 16),
        new THREE.MeshStandardMaterial({ color: 0xffedd5, roughness: 0.6 })
      );
      head.position.z = 1.95;
      pGroup.add(head);

      scene.add(pGroup);
      playerMeshes[id] = pGroup;
      return pGroup;
    }

    // ---------------- UNIVERSAL 3D CANVAS PERSPECTIVE PROJECTION ENGINE ----------------
    const canvas2D = document.getElementById('pitch-2d-canvas');
    const ctx2D = canvas2D.getContext('2d');

    let camYaw = 0.0;
    let camPitch = 0.52;
    let isDragging = false;
    let lastMouseX = 0;
    let lastMouseY = 0;

    canvas2D.addEventListener('mousedown', (e) => {
      isDragging = true;
      lastMouseX = e.clientX;
      lastMouseY = e.clientY;
    });

    window.addEventListener('mousemove', (e) => {
      if (!isDragging || activeView !== '3d') return;
      const dx = e.clientX - lastMouseX;
      const dy = e.clientY - lastMouseY;
      lastMouseX = e.clientX;
      lastMouseY = e.clientY;

      camYaw += dx * 0.005;
      camPitch = Math.max(0.18, Math.min(1.25, camPitch + dy * 0.005));
      render(currentFrame);
    });

    window.addEventListener('mouseup', () => { isDragging = false; });

    function resizeCanvas() {
      const stage = document.querySelector('.view-stage');
      if (stage && canvas2D) {
        canvas2D.width = stage.clientWidth || 1050;
        canvas2D.height = stage.clientHeight || 520;
      }
    }

    function project3D(x, y, z, W, H) {
      const cx = x - 52.5;
      const cy = y - 34.0;
      const cz = z;

      const cosY = Math.cos(camYaw);
      const sinY = Math.sin(camYaw);
      const rx = cx * cosY - cy * sinY;
      const ry = cx * sinY + cy * cosY;

      const cosP = Math.cos(camPitch);
      const sinP = Math.sin(camPitch);
      const rz = cz * cosP - ry * sinP;
      const camDist = 135.0;
      const depth = camDist + (ry * cosP + cz * sinP);

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

      const b = frameData.ball;
      const bShadowPr = project3D(b.x, b.y, 0, W, H);
      const bBallPr = project3D(b.x, b.y, b.z || 0, W, H);
      renderList.push({
        type: 'ball',
        depth: bBallPr.depth,
        data: b,
        shadow: bShadowPr,
        ball: bBallPr
      });

      renderList.sort((a, b) => b.depth - a.depth);

      // 6. Draw Sorted 3D Entities
      renderList.forEach(item => {
        if (item.type === 'player') {
          const p = item.data;
          const base = item.base;
          const head = item.head;
          const rad = Math.max(3.5, 6.5 * base.scale);

          // Player Ground Contact Shadow
          ctx2D.fillStyle = 'rgba(0, 0, 0, 0.45)';
          ctx2D.beginPath();
          ctx2D.ellipse(base.x, base.y, rad * 1.2, rad * 0.45, 0, 0, Math.PI * 2);
          ctx2D.fill();

          // 3D Standing Player Cylinder
          const pColor = p.team === 'Home' ? '#ef4444' : '#eab308';
          const grad = ctx2D.createLinearGradient(base.x - rad, 0, base.x + rad, 0);
          grad.addColorStop(0, p.team === 'Home' ? '#991b1b' : '#ca8a04');
          grad.addColorStop(0.5, pColor);
          grad.addColorStop(1, '#ffffff');

          ctx2D.fillStyle = grad;
          ctx2D.beginPath();
          ctx2D.moveTo(base.x - rad * 0.7, base.y);
          ctx2D.lineTo(head.x - rad * 0.6, head.y);
          ctx2D.lineTo(head.x + rad * 0.6, head.y);
          ctx2D.lineTo(base.x + rad * 0.7, base.y);
          ctx2D.closePath();
          ctx2D.fill();

          // Player Head
          ctx2D.fillStyle = '#ffedd5';
          ctx2D.beginPath();
          ctx2D.arc(head.x, head.y - rad * 0.3, rad * 0.55, 0, Math.PI * 2);
          ctx2D.fill();

          // Player Squad Number on Torso
          const isHome = (p.team === 'Home');
          const isGK = (p.role === 'GK' || p.id === 'H1' || p.id === 'A1');
          const num = p.num !== undefined ? p.num : (p.id.replace(/[^\d]/g, '') || '');
          const name = p.name || p.id;

          ctx2D.fillStyle = (!isHome && !isGK) ? '#0f172a' : '#ffffff';
          ctx2D.font = `bold ${Math.max(7, Math.round(9 * base.scale))}px 'JetBrains Mono', monospace`;
          ctx2D.textAlign = 'center';
          ctx2D.textBaseline = 'middle';
          ctx2D.fillText(num, (base.x + head.x) / 2, (base.y + head.y) / 2);

          // Player Name Label Pill above head
          ctx2D.font = `bold ${Math.max(8, Math.round(10 * base.scale))}px 'JetBrains Mono', monospace`;
          const pNameW = ctx2D.measureText(name).width;
          const pLabelY = head.y - rad * 1.0;

          ctx2D.fillStyle = 'rgba(15, 23, 42, 0.85)';
          ctx2D.beginPath();
          ctx2D.roundRect(head.x - pNameW / 2 - 3, pLabelY - 6, pNameW + 6, 12, 3);
          ctx2D.fill();

          ctx2D.strokeStyle = 'rgba(255, 255, 255, 0.25)';
          ctx2D.lineWidth = 0.8;
          ctx2D.stroke();

          ctx2D.fillStyle = '#ffffff';
          ctx2D.fillText(name, head.x, pLabelY);

        } else if (item.type === 'ball') {
          const bData = item.data;
          const sPr = item.shadow;
          const bPr = item.ball;
          const bElev = bData.z || 0;
          const rad = Math.max(3.0, 5.0 * bPr.scale);

          // Ground Shadow
          const sAlpha = Math.max(0.15, 0.65 - (bElev * 0.08));
          const sScale = Math.max(0.4, 1.0 - (bElev * 0.07));
          ctx2D.fillStyle = `rgba(0, 0, 0, ${sAlpha})`;
          ctx2D.beginPath();
          ctx2D.ellipse(sPr.x, sPr.y, rad * 1.3 * sScale, rad * 0.55 * sScale, 0, 0, Math.PI * 2);
          ctx2D.fill();

          // Elevation Tether Line
          if (bElev > 0.4) {
            ctx2D.strokeStyle = 'rgba(255, 255, 255, 0.4)';
            ctx2D.lineWidth = 1;
            ctx2D.setLineDash([3, 3]);
            ctx2D.beginPath();
            ctx2D.moveTo(sPr.x, sPr.y);
            ctx2D.lineTo(bPr.x, bPr.y);
            ctx2D.stroke();
            ctx2D.setLineDash([]);
          }

          // 3D Sphere Shading
          const ballGrad = ctx2D.createRadialGradient(
            bPr.x - rad * 0.35, bPr.y - rad * 0.35, rad * 0.1,
            bPr.x, bPr.y, rad
          );
          ballGrad.addColorStop(0, '#ffffff');
          ballGrad.addColorStop(0.7, '#f3f4f6');
          ballGrad.addColorStop(1, '#9ca3af');

          ctx2D.fillStyle = ballGrad;
          ctx2D.beginPath();
          ctx2D.arc(bPr.x, bPr.y, rad, 0, Math.PI * 2);
          ctx2D.fill();

          // Halo Glow if Shot/High Speed
          if ((bData.speed_kmh || 0) > 75) {
            ctx2D.strokeStyle = '#ef4444';
            ctx2D.lineWidth = 2.0;
            ctx2D.beginPath();
            ctx2D.arc(bPr.x, bPr.y, rad + 3, 0, Math.PI * 2);
            ctx2D.stroke();
          }
        }
      });
    }

    // ---------------- 2D PLANAR BROADCAST RENDERER ----------------
    function render2D(frameData) {
      if (!canvas2D.width || !canvas2D.height) resizeCanvas();
      const W = canvas2D.width;
      const H = canvas2D.height;
      const padX = 42; // Padding to allow protruding goals to fit cleanly
      const padY = 26;
      const pitchW = W - padX * 2;
      const pitchH = H - padY * 2;

      // Coordinate Transform: Metrica metric meters (105m x 68m) -> Screen Pixels
      function toScreen2D(x, y) {
        return {
          sx: padX + (x / 105.0) * pitchW,
          sy: padY + (y / 68.0) * pitchH
        };
      }

      // 1. Dark Broadcast Background
      ctx2D.fillStyle = "#030712";
      ctx2D.fillRect(0, 0, W, H);

      // 2. Outer Technical Turf / Apron
      ctx2D.fillStyle = "#0c2817";
      ctx2D.beginPath();
      ctx2D.roundRect(padX - 22, padY - 14, pitchW + 44, pitchH + 28, 8);
      ctx2D.fill();

      // 3. Alternating FIFA Mowing Grass Stripes (10 Distinct Green Bands)
      const numStripes = 10;
      const stripeW = pitchW / numStripes;
      for (let i = 0; i < numStripes; i++) {
        ctx2D.fillStyle = (i % 2 === 0) ? "#15803d" : "#166534";
        ctx2D.fillRect(padX + i * stripeW, padY, stripeW, pitchH);
      }

      // 4. Protruding Realistic Goals with Cross-Hatched Net Mesh
      // Goal dimensions: 7.32m wide (y: 30.34 to 37.66), 2.5m depth behind touchline
      function drawGoal2D(isHomeGoal) {
        const topY = toScreen2D(0, 30.34).sy;
        const botY = toScreen2D(0, 37.66).sy;
        const goalH = botY - topY;
        const goalDepthPx = (2.5 / 105.0) * pitchW;

        const gx0 = isHomeGoal ? padX : padX + pitchW;
        const gxBack = isHomeGoal ? padX - goalDepthPx : padX + pitchW + goalDepthPx;
        const netLeft = Math.min(gx0, gxBack);

        // Goal Net Area Background
        ctx2D.fillStyle = "rgba(15, 23, 42, 0.7)";
        ctx2D.fillRect(netLeft, topY, goalDepthPx, goalH);

        // Cross-hatched Netting Pattern
        ctx2D.strokeStyle = "rgba(255, 255, 255, 0.4)";
        ctx2D.lineWidth = 1;
        ctx2D.beginPath();
        const step = 5;
        for (let x = netLeft; x <= netLeft + goalDepthPx; x += step) {
          ctx2D.moveTo(x, topY);
          ctx2D.lineTo(x, botY);
        }
        for (let y = topY; y <= botY; y += step) {
          ctx2D.moveTo(netLeft, y);
          ctx2D.lineTo(netLeft + goalDepthPx, y);
        }
        ctx2D.stroke();

        // Goal Frame (Posts & Back Stanchion)
        ctx2D.strokeStyle = "#ffffff";
        ctx2D.lineWidth = 2.5;
        ctx2D.strokeRect(netLeft, topY, goalDepthPx, goalH);

        // Bright White Goal Line Mouth
        ctx2D.strokeStyle = "rgba(255, 255, 255, 0.95)";
        ctx2D.lineWidth = 3;
        ctx2D.beginPath();
        ctx2D.moveTo(gx0, topY);
        ctx2D.lineTo(gx0, botY);
        ctx2D.stroke();
      }
      drawGoal2D(true);  // Home Goal (Left)
      drawGoal2D(false); // Away Goal (Right)

      // 5. Crisp FIFA Regulation Pitch Markings
      ctx2D.strokeStyle = "rgba(255, 255, 255, 0.9)";
      ctx2D.lineWidth = 2;

      // Outer Pitch Boundary
      ctx2D.strokeRect(padX, padY, pitchW, pitchH);

      // Halfway Line
      const midX = padX + pitchW / 2;
      ctx2D.beginPath();
      ctx2D.moveTo(midX, padY);
      ctx2D.lineTo(midX, padY + pitchH);
      ctx2D.stroke();

      // Center Circle (Radius = 9.15m)
      const centerR = (9.15 / 105.0) * pitchW;
      const centerY = padY + pitchH / 2;
      ctx2D.beginPath();
      ctx2D.arc(midX, centerY, centerR, 0, Math.PI * 2);
      ctx2D.stroke();

      // Center Spot
      ctx2D.fillStyle = "#ffffff";
      ctx2D.beginPath();
      ctx2D.arc(midX, centerY, 3, 0, Math.PI * 2);
      ctx2D.fill();

      // Corner Arcs (Radius = 1m)
      const cornerR = (1.5 / 105.0) * pitchW;
      // Top-Left, Bottom-Left, Top-Right, Bottom-Right
      ctx2D.beginPath(); ctx2D.arc(padX, padY, cornerR, 0, Math.PI * 0.5); ctx2D.stroke();
      ctx2D.beginPath(); ctx2D.arc(padX, padY + pitchH, cornerR, Math.PI * 1.5, 0); ctx2D.stroke();
      ctx2D.beginPath(); ctx2D.arc(padX + pitchW, padY, cornerR, Math.PI * 0.5, Math.PI); ctx2D.stroke();
      ctx2D.beginPath(); ctx2D.arc(padX + pitchW, padY + pitchH, cornerR, Math.PI, Math.PI * 1.5); ctx2D.stroke();

      // 18-Yard Penalty Boxes (16.5m depth, 40.32m width -> y: 13.84 to 54.16)
      const pBoxW = (16.5 / 105.0) * pitchW;
      const pBoxTopY = toScreen2D(0, 13.84).sy;
      const pBoxH = toScreen2D(0, 54.16).sy - pBoxTopY;
      ctx2D.strokeRect(padX, pBoxTopY, pBoxW, pBoxH);
      ctx2D.strokeRect(padX + pitchW - pBoxW, pBoxTopY, pBoxW, pBoxH);

      // 6-Yard Goal Areas (5.5m depth, 18.32m width -> y: 24.84 to 43.16)
      const gAreaW = (5.5 / 105.0) * pitchW;
      const gAreaTopY = toScreen2D(0, 24.84).sy;
      const gAreaH = toScreen2D(0, 43.16).sy - gAreaTopY;
      ctx2D.strokeRect(padX, gAreaTopY, gAreaW, gAreaH);
      ctx2D.strokeRect(padX + pitchW - gAreaW, gAreaTopY, gAreaW, gAreaH);

      // Penalty Spots (11.0m from goal line)
      const penSpotLX = toScreen2D(11.0, 34.0).sx;
      const penSpotRX = toScreen2D(105.0 - 11.0, 34.0).sx;
      ctx2D.beginPath(); ctx2D.arc(penSpotLX, centerY, 3, 0, Math.PI * 2); ctx2D.fill();
      ctx2D.beginPath(); ctx2D.arc(penSpotRX, centerY, 3, 0, Math.PI * 2); ctx2D.fill();

      // Penalty D-Arcs (9.15m radius centered at penalty spot, outside box)
      ctx2D.beginPath();
      ctx2D.arc(penSpotLX, centerY, centerR, -0.93, 0.93);
      ctx2D.stroke();
      ctx2D.beginPath();
      ctx2D.arc(penSpotRX, centerY, centerR, Math.PI - 0.93, Math.PI + 0.93);
      ctx2D.stroke();

      // 6. Draw Player Jersey Kits & Squad Numbers
      function drawJerseyKit(sx, sy, p) {
        const isHome = (p.team === 'Home');
        const isGK = (p.role === 'GK' || p.id === 'H1' || p.id === 'A1');
        const num = p.num !== undefined ? p.num : (p.id.replace(/[^\d]/g, '') || '');
        const name = p.name || p.id;

        // Colors
        let kitPrimary = isHome ? '#ef4444' : '#eab308';
        let kitSec = isHome ? '#2563eb' : '#ffffff';
        let numColor = '#ffffff';

        if (isGK) {
          kitPrimary = isHome ? '#10b981' : '#f97316'; // Neon green or orange for GK
          kitSec = '#064e3b';
          numColor = '#ffffff';
        } else if (!isHome) {
          numColor = '#0f172a'; // Dark number on bright yellow/white away kit
        }

        // Drop shadow for depth
        ctx2D.fillStyle = "rgba(0, 0, 0, 0.4)";
        ctx2D.beginPath();
        ctx2D.ellipse(sx, sy + 3, 10, 5, 0, 0, Math.PI * 2);
        ctx2D.fill();

        // Jersey Sleeves (Left & Right Angled Shoulders)
        ctx2D.fillStyle = kitSec;
        ctx2D.beginPath();
        ctx2D.arc(sx - 7, sy - 1, 4, 0, Math.PI * 2);
        ctx2D.arc(sx + 7, sy - 1, 4, 0, Math.PI * 2);
        ctx2D.fill();

        // Jersey Torso Body (Circle Badge with Team Color)
        ctx2D.fillStyle = kitPrimary;
        ctx2D.beginPath();
        ctx2D.arc(sx, sy, 8.5, 0, Math.PI * 2);
        ctx2D.fill();

        // Collar Trim
        ctx2D.strokeStyle = kitSec;
        ctx2D.lineWidth = 1.5;
        ctx2D.stroke();

        // Squad Number (Centered in Jersey)
        ctx2D.fillStyle = numColor;
        ctx2D.font = "bold 8px 'JetBrains Mono', monospace";
        ctx2D.textAlign = "center";
        ctx2D.textBaseline = "middle";
        ctx2D.fillText(num, sx, sy + 0.5);

        // Player Name Pill below/above kit
        ctx2D.font = "bold 9px 'JetBrains Mono', monospace";
        const textW = ctx2D.measureText(name).width;
        const pillY = sy - 14;

        ctx2D.fillStyle = "rgba(15, 23, 42, 0.85)";
        ctx2D.beginPath();
        ctx2D.roundRect(sx - textW / 2 - 4, pillY - 7, textW + 8, 13, 3);
        ctx2D.fill();

        ctx2D.strokeStyle = "rgba(255, 255, 255, 0.25)";
        ctx2D.lineWidth = 0.8;
        ctx2D.stroke();

        ctx2D.fillStyle = "#ffffff";
        ctx2D.textBaseline = "middle";
        ctx2D.fillText(name, sx, pillY - 0.5);
      }

      // Draw all players
      frameData.players.forEach(p => {
        const { sx, sy } = toScreen2D(p.x, p.y);
        drawJerseyKit(sx, sy, p);
      });

      // 7. Draw Ball with Telstar Pattern, Elevation Shadow & Strike Fire Glow
      const b = frameData.ball;
      const { sx: bx, sy: by } = toScreen2D(b.x, b.y);
      const bElev = b.z || 0;
      const speed = b.speed_kmh || 0;

      // Ball Ground Shadow (Expands and fades with elevation)
      const shadowAlpha = Math.max(0.12, 0.55 - bElev * 0.08);
      const shadowR = Math.max(2.5, 5.0 - bElev * 0.4);
      ctx2D.fillStyle = `rgba(0, 0, 0, ${shadowAlpha})`;
      ctx2D.beginPath();
      ctx2D.ellipse(bx, by, shadowR * 1.3, shadowR * 0.7, 0, 0, Math.PI * 2);
      ctx2D.fill();

      // Ball Elevation Offset (Draw ball slightly higher if in air)
      const ballVisualY = by - (bElev * 3.5);

      // Tether line if in flight
      if (bElev > 0.4) {
        ctx2D.strokeStyle = "rgba(255, 255, 255, 0.45)";
        ctx2D.lineWidth = 1;
        ctx2D.setLineDash([2, 2]);
        ctx2D.beginPath();
        ctx2D.moveTo(bx, by);
        ctx2D.lineTo(bx, ballVisualY);
        ctx2D.stroke();
        ctx2D.setLineDash([]);
      }

      // High-speed Strike Halo / Flame Trail
      if (speed > 75) {
        ctx2D.fillStyle = "rgba(239, 68, 68, 0.45)";
        ctx2D.beginPath();
        ctx2D.arc(bx, ballVisualY, 14, 0, Math.PI * 2);
        ctx2D.fill();

        ctx2D.strokeStyle = "#ef4444";
        ctx2D.lineWidth = 2.5;
        ctx2D.beginPath();
        ctx2D.arc(bx, ballVisualY, 15, 0, Math.PI * 2);
        ctx2D.stroke();
      }

      // Ball Outer High-Contrast Glow Ring (Ensures high visibility across green stripes)
      ctx2D.strokeStyle = "rgba(255, 255, 255, 0.85)";
      ctx2D.lineWidth = 1.5;
      ctx2D.beginPath();
      ctx2D.arc(bx, ballVisualY, 9.8, 0, Math.PI * 2);
      ctx2D.stroke();

      // Ball Sphere with Radial Shading (Radius enlarged to 8.5px for clear broadcast visibility)
      const ballGrad = ctx2D.createRadialGradient(bx - 2.5, ballVisualY - 2.5, 1.2, bx, ballVisualY, 8.5);
      ballGrad.addColorStop(0, "#ffffff");
      ballGrad.addColorStop(0.65, "#f1f5f9");
      ballGrad.addColorStop(1, "#94a3b8");

      ctx2D.fillStyle = ballGrad;
      ctx2D.beginPath();
      ctx2D.arc(bx, ballVisualY, 8.5, 0, Math.PI * 2);
      ctx2D.fill();

      // Crisp Ball Outline
      ctx2D.strokeStyle = "#0f172a";
      ctx2D.lineWidth = 1.6;
      ctx2D.stroke();

      // Authentic Telstar Black Pentagons & Seams (Proportional to 8.5px radius)
      ctx2D.fillStyle = "#0f172a";
      // Center pentagon
      ctx2D.beginPath();
      ctx2D.arc(bx, ballVisualY, 2.8, 0, Math.PI * 2);
      ctx2D.fill();

      // Surrounding mini patches
      ctx2D.beginPath();
      ctx2D.arc(bx - 4.5, ballVisualY - 3.2, 1.6, 0, Math.PI * 2);
      ctx2D.arc(bx + 4.5, ballVisualY - 2.8, 1.6, 0, Math.PI * 2);
      ctx2D.arc(bx, ballVisualY + 4.8, 1.6, 0, Math.PI * 2);
      ctx2D.fill();
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

        if (ballMesh && ballShadow) {
          const bz = Math.max(0.28, f.ball.z || 0);
          ballMesh.position.set(f.ball.x, f.ball.y, bz);
          ballShadow.position.set(f.ball.x, f.ball.y, 0.03);
          ballShadow.scale.setScalar(Math.max(0.4, 1.0 - (bz * 0.08)));
        }
      }

      // Render Active Viewport on Canvas
      if (activeView === '3d') {
        if (threeInitialized) {
          if (renderer && scene && camera) {
            renderer.render(scene, camera);
          }
        } else {
          render3DStadium(f);
        }
      } else {
        render2D(f);
      }

      // Update Slider and Controls
      document.getElementById('frame-slider').value = frameIdx;
      document.getElementById('frame-label').textContent = `${frameIdx} / ${maxFrames}`;

      // Update Match Clock across 90 minutes
      const clockStr = f.match_time || "00:00";
      document.getElementById('stat-clock').textContent = clockStr;
      document.getElementById('sb-time').textContent = clockStr;

      // Parse current match minute and second
      let curMin = 0, curSec = 0;
      if (clockStr.includes(':')) {
        const parts = clockStr.split(':');
        curMin = parseInt(parts[0]) || 0;
        curSec = parseInt(parts[1]) || 0;
      }
      const totalSec = curMin * 60 + curSec;

      // Update Match Period Badge (1st Half / 2nd Half / Halftime / Full Time)
      const periodEl = document.getElementById('sb-period');
      if (curMin < 45) {
        periodEl.textContent = "1ST HALF";
        periodEl.style.color = "#94a3b8";
      } else if (curMin === 45 && totalSec <= 45 * 60 + 15) {
        periodEl.textContent = "HALFTIME (HT)";
        periodEl.style.color = "#f59e0b";
      } else if (curMin >= 45 && curMin < 90) {
        periodEl.textContent = "2ND HALF";
        periodEl.style.color = "#94a3b8";
      } else if (curMin >= 90 && frameIdx >= maxFrames - 25) {
        periodEl.textContent = "FULL TIME (FT)";
        periodEl.style.color = "#10b981";
      } else {
        periodEl.textContent = "STOPPAGE TIME";
        periodEl.style.color = "#ef4444";
      }

      // Live Scoreboard Calculation based on match key events
      let hScore = 0;
      let aScore = 0;
      let activeGoal = null;

      // Exact Goal Line Entrance: ball enters net
      const bx = f.ball.x;
      const by = f.ball.y;
      const inNet = (bx >= 104.90 && by >= 29.5 && by <= 38.5) || (bx <= 0.10 && by >= 29.5 && by <= 38.5);

      if (currentMetadata && currentMetadata.goals) {
        currentMetadata.goals.forEach(g => {
          const gSec = g.minute * 60 + g.second;
          // Only increment score once ball has crossed goal line (inNet) or past goal entrance second
          if (totalSec > gSec || (totalSec >= gSec && inNet)) {
            if (g.score_after) {
              hScore = g.score_after[0];
              aScore = g.score_after[1];
            } else {
              if (g.team === 'Home') hScore++;
              else if (g.team === 'Away') aScore++;
            }
          }
          if (Math.abs(totalSec - gSec) <= 100) {
            activeGoal = g;
          }
        });
      }

      document.getElementById('sb-score-home').textContent = hScore;
      document.getElementById('sb-score-away').textContent = aScore;

      // Dynamic Goal Banner Celebration & Vibration Rumble + Popup Modal
      const goalBanner = document.getElementById('goal-alert-banner');
      const stageEl = document.getElementById('main-view-stage');
      const goalModal = document.getElementById('goal-popup-modal');

      // Track if current frame is during or after goal moment
      let isGoalMoment = false;
      if (activeGoal) {
        const gSec = activeGoal.minute * 60 + activeGoal.second;
        // Trigger strictly when ball hits the net OR during the post-goal celebration window
        if (inNet && Math.abs(totalSec - gSec) <= 15) {
          isGoalMoment = true;
        } else if (totalSec > gSec && totalSec <= gSec + 30) {
          isGoalMoment = true;
        }
      }

      if (isGoalMoment && activeGoal) {
        goalBanner.style.display = 'inline-flex';
        document.getElementById('goal-alert-text').textContent = 
          `GOAL! ${activeGoal.scorer} (${activeGoal.minute}') · ${activeGoal.type} (${activeGoal.speed_kmh} km/h) 🔥`;

        // Trigger Screen Rumble & Vibration Effect
        if (stageEl) stageEl.classList.add('stadium-rumble');

        // Populate and display Goal Popup Celebration Modal
        if (goalModal) {
          document.getElementById('popup-scorer-name').textContent = activeGoal.scorer.toUpperCase();
          document.getElementById('popup-minute-badge').textContent = `${activeGoal.minute}'`;
          document.getElementById('popup-type-stat').textContent = activeGoal.type;
          document.getElementById('popup-speed-stat').textContent = `${activeGoal.speed_kmh} km/h`;

          const hTeamName = currentMetadata?.home_team?.name || 'HOME';
          const aTeamName = currentMetadata?.away_team?.name || 'AWAY';
          document.getElementById('popup-score-display').textContent = `${hTeamName} ${hScore} - ${aScore} ${aTeamName}`;
          goalModal.style.display = 'flex';
        }
      } else {
        goalBanner.style.display = 'none';
        if (stageEl) stageEl.classList.remove('stadium-rumble');
        if (goalModal) goalModal.style.display = 'none';
      }

      // Active Chapter Button Highlight
      updateActiveChapterButton(curMin);

      // Ball Telemetry
      document.getElementById('stat-z').textContent = (f.ball.z || 0).toFixed(2) + " m";
      document.getElementById('lbl-z-val').textContent = (f.ball.z || 0).toFixed(2) + " m";

      const speed = f.ball.speed_kmh || 0;
      document.getElementById('stat-speed').textContent = speed.toFixed(1) + " km/h";
      document.getElementById('lbl-speed-val').textContent = speed.toFixed(1) + " km/h";

      // Shot Power Gauge (0 to 120 km/h)
      const pct = Math.min(100, (speed / 120) * 100);
      document.getElementById('shot-meter').style.width = pct + "%";

      // Ball State (Dynamic real-time kinematic classification)
      const bStateEl = document.getElementById('lbl-ball-state');
      const bz = f.ball.z || 0;
      if (speed > 75 || (bz > 1.4 && speed > 55)) {
        bStateEl.textContent = "POWER STRIKE / SHOT 🔥";
        bStateEl.style.color = "#ef4444";
      } else if (bz > 1.2) {
        bStateEl.textContent = "AERIAL FLIGHT / CROSS ✈️";
        bStateEl.style.color = "#a78bfa";
      } else if (speed > 25) {
        bStateEl.textContent = "THREADED GROUND PASS ⚡";
        bStateEl.style.color = "#38bdf8";
      } else if (speed > 8) {
        bStateEl.textContent = "GROUND PASS / TIKI-TAKA 🟢";
        bStateEl.style.color = "var(--accent)";
      } else {
        bStateEl.textContent = "BALL CONTROL & DRIBBLE ⚽";
        bStateEl.style.color = "#facc15";
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
        document.getElementById('stat-pc-home').textContent = poss.home_pitch_control_pct.toFixed(1) + '%';
        document.getElementById('stat-pc-away').textContent = poss.away_pitch_control_pct.toFixed(1) + '%';
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
          cont3d.style.display = 'none';
          cvs2d.style.display = 'block';
          if (hudCam) {
            hudCam.style.display = 'block';
            hudCam.textContent = '🎥 3D Stadium View (Universal Perspective): Drag mouse to rotate angle';
          }
          resizeCanvas();
        }
      } else {
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

    // Jump smoothly to target match minute
    function jumpToMinute(targetMin) {
      if (!matchData || matchData.length === 0) return;
      let targetIdx = 1;
      for (let i = 0; i < matchData.length; i++) {
        const parts = (matchData[i].match_time || "00:00").split(':');
        const m = parseInt(parts[0]) || 0;
        if (m >= targetMin) {
          targetIdx = i + 1;
          break;
        }
      }
      currentFrame = targetIdx;
      render(currentFrame);
      updateActiveChapterButton(targetMin);
    }

    function updateActiveChapterButton(activeMin) {
      const btns = document.querySelectorAll('.chapter-btn');
      btns.forEach(btn => {
        const minAttr = btn.getAttribute('data-min');
        if (minAttr && parseInt(minAttr) === activeMin) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
    }

    function onMatchChange(matchId) {
      if (isPlaying) togglePlay();
      document.getElementById('frame-label').textContent = "Loading match...";
      fetch(`/api/match/${matchId}`)
        .then(res => res.json())
        .then(data => {
          matchData = data.frames;
          currentMetadata = data.metadata || {};
          maxFrames = matchData.length;
          currentFrame = 1;

          // Update Scoreboard Team Names, Crest Badges & Colors
          if (currentMetadata.home_team) {
            document.getElementById('sb-home-name').textContent = currentMetadata.home_team.name;
            const hBadge = document.getElementById('sb-home-badge');
            hBadge.textContent = currentMetadata.home_team.badge;
            hBadge.style.background = currentMetadata.home_team.color;
          }
          if (currentMetadata.away_team) {
            document.getElementById('sb-away-name').textContent = currentMetadata.away_team.name;
            const aBadge = document.getElementById('sb-away-badge');
            aBadge.textContent = currentMetadata.away_team.badge;
            aBadge.style.background = currentMetadata.away_team.color;
          }

          // Re-render Chapter Buttons for New Match
          const chBar = document.getElementById('chapters-bar');
          if (chBar && currentMetadata.chapters) {
            chBar.innerHTML = currentMetadata.chapters.map(ch => `
              <button class="chapter-btn ${ch.label.includes('GOAL') ? 'goal-chapter' : ''}" data-min="${ch.min}" onclick="jumpToMinute(${ch.min})">${ch.label}</button>
            `).join('');
          }

          document.getElementById('frame-slider').max = maxFrames;
          document.getElementById('frame-slider').value = 1;
          document.getElementById('frame-label').textContent = `1 / ${maxFrames}`;
          render(1);
        })
        .catch(err => {
          console.error("Failed to switch match dataset:", err);
        });
    }

    // Default to 3D Stadium
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

    // Render frame 1 immediately from initial embedded payload
    render(1);

    // Initial async fetch for default match
    fetch('/api/match/{{ selected_match_id }}')
      .then(res => res.json())
      .then(data => {
        matchData = data.frames;
        currentMetadata = data.metadata || currentMetadata;
        maxFrames = matchData.length;
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

@app.route("/api/match")
@app.route("/api/match/<match_id>")
def get_match_full(match_id=None):
    m_id = match_id or DEFAULT_MATCH_ID
    if m_id not in MATCH_CACHE:
        m_id = DEFAULT_MATCH_ID
    data = MATCH_CACHE[m_id]
    return jsonify({
        "match_id": m_id,
        "metadata": data.get("metadata", {}),
        "total_frames": data["total_frames"],
        "home_pct": data["home_pct"],
        "away_pct": data["away_pct"],
        "turnovers": data["turnovers"],
        "frames": data["frames"]
    })

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
        metadata=initial_match.get("metadata", {}),
        total_frames=initial_match["total_frames"],
        home_pct=initial_match["home_pct"],
        away_pct=initial_match["away_pct"],
        turnovers=initial_match["turnovers"],
        initial_frame_json=json.dumps(initial_frame),
        initial_meta_json=json.dumps(initial_match.get("metadata", {}))
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
