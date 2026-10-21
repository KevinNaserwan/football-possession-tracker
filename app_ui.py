import os
import json
import math
from flask import Flask, render_template_string, jsonify
from src.metrica_parser import MetricaTrackingParser
from src.pipeline import FullPossessionPipeline

app = Flask(__name__)

# Initialize parser and pipeline
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
parser = MetricaTrackingParser()
pipeline = FullPossessionPipeline()

MATCH_CATALOG = {
    "MATCH_BARCA_ATHLETIC_2024": {
        "id": "MATCH_BARCA_ATHLETIC_2024",
        "title": "⚽ FC Barcelona 2 - 1 Athletic Club (La Liga 2024 · Montjuïc · Yamal 24' & Lewandowski 75')",
        "file": os.path.join(BASE_DIR, "data/match_barca_athletic_2024.json")
    },
    "MATCH_EL_CLASICO_2017": {
        "id": "MATCH_EL_CLASICO_2017",
        "title": "⚽ Real Madrid 2 - 3 Barcelona (La Liga 2017 · Messi 92' Iconic Winner & Ramos Red)",
        "file": os.path.join(BASE_DIR, "data/match_el_clasico_2017.json")
    },
    "MATCH_WORLD_CUP_2022": {
        "id": "MATCH_WORLD_CUP_2022",
        "title": "🌍 Argentina 3 - 3 France (World Cup 2022 Final · Lusail Epic 120' & 12 Goals)",
        "file": os.path.join(BASE_DIR, "data/match_world_cup_2022.json")
    },
    "MATCH_EL_CLASICO_5_0": {
        "id": "MATCH_EL_CLASICO_5_0",
        "title": "⚡ Barcelona 5 - 0 Real Madrid (La Liga 2010 · Pep's Camp Nou Manita & 5 Goals)",
        "file": os.path.join(BASE_DIR, "data/match_el_clasico_5_0.json")
    },
    "MATCH_UCL_WEMBLEY_2011": {
        "id": "MATCH_UCL_WEMBLEY_2011",
        "title": "🏆 Barcelona 3 - 1 Manchester United (UCL Final 2011 · Wembley Masterclass)",
        "file": os.path.join(BASE_DIR, "data/match_ucl_wembley_2011.json")
    },
    "MATCH_UCL_FINAL_2015": {
        "id": "MATCH_UCL_FINAL_2015",
        "title": "🏆 Juventus 1 - 3 Barcelona (UCL Final 2015 · Berlin Treble Triumph)",
        "file": os.path.join(BASE_DIR, "data/match_ucl_final_2015.json")
    }
}

MATCH_CACHE = {}

def process_match_file(filepath):
    if not os.path.isabs(filepath):
        filepath = os.path.join(BASE_DIR, filepath)
    if not os.path.exists(filepath):
        filepath = os.path.join(BASE_DIR, "data/sample_match_tracking.json")

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

DEFAULT_MATCH_ID = "MATCH_BARCA_ATHLETIC_2024"

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
      background-color: #030508;
      color: var(--text);
      font-family: 'Plus Jakarta Sans', sans-serif;
      width: 100vw;
      height: 100vh;
      overflow: hidden;
      margin: 0;
      padding: 0;
      position: relative;
    }
    #three-canvas-container, #pitch-2d-canvas {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      z-index: 1;
      display: block;
    }
    #pitch-2d-canvas {
      display: none;
    }

    /* FLOATING VIDEO-GAME HUD LAYER (100% Fullscreen Overlay) */
    .hud-layer {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      z-index: 10;
      pointer-events: none;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      padding: 12px 18px;
      box-sizing: border-box;
      transition: opacity 0.25s ease, transform 0.25s ease;
    }
    .hud-layer.hidden {
      opacity: 0;
      pointer-events: none !important;
      transform: scale(0.98);
    }
    .hud-interactive {
      pointer-events: auto;
    }

    /* TOP HUD SECTION */
    .hud-top-bar {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 14px;
      width: 100%;
    }
    .hud-group {
      display: flex;
      align-items: center;
      gap: 8px;
      pointer-events: auto;
    }
    .hud-brand {
      display: flex;
      align-items: center;
      gap: 8px;
      background: rgba(15, 23, 42, 0.88);
      backdrop-filter: blur(14px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 9px;
      padding: 6px 12px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
    }
    .hud-select {
      background: rgba(15, 23, 42, 0.92);
      color: #f3f4f6;
      border: 1px solid rgba(255, 255, 255, 0.16);
      border-radius: 8px;
      padding: 6px 10px;
      font-size: 0.80rem;
      font-weight: 600;
      cursor: pointer;
      outline: none;
      backdrop-filter: blur(14px);
      box-shadow: 0 4px 14px rgba(0,0,0,0.5);
    }
    .hud-btn {
      background: rgba(15, 23, 42, 0.88);
      color: #e2e8f0;
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: 8px;
      padding: 6px 11px;
      font-size: 0.76rem;
      font-weight: 700;
      cursor: pointer;
      backdrop-filter: blur(14px);
      box-shadow: 0 4px 14px rgba(0,0,0,0.5);
      transition: all 0.15s ease;
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }
    .hud-btn:hover {
      background: var(--accent);
      color: #000;
      border-color: var(--accent);
      transform: translateY(-1px);
    }

    .view-toggle {
      display: flex;
      background: rgba(15, 23, 42, 0.85);
      backdrop-filter: blur(12px);
      border-radius: 8px;
      padding: 2px;
      border: 1px solid rgba(255, 255, 255, 0.14);
    }
    .view-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 5px 11px;
      border-radius: 6px;
      font-size: 0.78rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }
    .view-btn.active {
      background: var(--accent);
      color: #000;
      font-weight: 700;
    }

    .hud-cam-bar {
      display: flex;
      align-items: center;
      gap: 5px;
      background: rgba(15, 23, 42, 0.85);
      backdrop-filter: blur(12px);
      padding: 3px 8px;
      border-radius: 8px;
      border: 1px solid rgba(255, 255, 255, 0.14);
      flex-wrap: wrap;
    }
    .cam-btn {
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.15);
      color: #94a3b8;
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 0.72rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .cam-btn:hover {
      background: rgba(255, 255, 255, 0.18);
      color: #ffffff;
      border-color: rgba(255, 255, 255, 0.35);
    }
    .cam-btn.active {
      background: #38bdf8;
      color: #030712;
      border-color: #38bdf8;
      font-weight: 800;
      box-shadow: 0 0 10px rgba(56, 189, 248, 0.4);
    }

    /* FLOATING BROADCAST SCOREBOARD (Top Center) */
    .hud-scoreboard-wrap {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 5px;
      pointer-events: auto;
    }
    .scoreboard-card {
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: linear-gradient(135deg, rgba(15, 23, 42, 0.94), rgba(11, 15, 25, 0.96));
      border: 1px solid rgba(255, 255, 255, 0.16);
      border-radius: 12px;
      padding: 7px 18px;
      box-shadow: 0 12px 36px rgba(0, 0, 0, 0.7), 0 0 1px rgba(255, 255, 255, 0.3);
      width: 480px;
      backdrop-filter: blur(16px);
    }
    .sb-team {
      display: flex;
      align-items: center;
      gap: 10px;
      flex: 1;
    }
    .sb-team.home { justify-content: flex-start; }
    .sb-team.away { justify-content: flex-end; }
    .sb-badge {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.88rem;
      font-weight: 800;
      padding: 4px 9px;
      border-radius: 6px;
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
      font-size: 0.95rem;
      letter-spacing: -0.01em;
      white-space: nowrap;
    }
    .sb-center {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-width: 140px;
    }
    .sb-score-box {
      display: flex;
      align-items: center;
      gap: 10px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 1.85rem;
      font-weight: 800;
      line-height: 1;
    }
    .sb-score {
      min-width: 22px;
      text-align: center;
      color: #f8fafc;
      text-shadow: 0 0 12px rgba(255, 255, 255, 0.3);
    }
    .sb-divider {
      color: rgba(255, 255, 255, 0.35);
      font-size: 1.35rem;
    }
    .sb-clock-box {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-top: 3px;
    }
    .sb-period {
      font-size: 0.65rem;
      font-weight: 700;
      color: #94a3b8;
      background: rgba(255, 255, 255, 0.06);
      padding: 1px 6px;
      border-radius: 4px;
      letter-spacing: 0.05em;
    }
    .sb-time {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.84rem;
      font-weight: 700;
      color: #38bdf8;
    }
    .goal-alert-banner {
      background: linear-gradient(90deg, #ef4444, #f59e0b, #ef4444);
      color: #ffffff;
      padding: 5px 16px;
      border-radius: 20px;
      font-size: 0.82rem;
      font-weight: 800;
      letter-spacing: 0.02em;
      box-shadow: 0 4px 20px rgba(239, 68, 68, 0.5);
      animation: pulseGlow 1.4s infinite alternate;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    @keyframes pulseGlow {
      from { transform: scale(1); filter: drop-shadow(0 0 4px rgba(245, 158, 11, 0.6)); }
      to { transform: scale(1.02); filter: drop-shadow(0 0 12px rgba(239, 68, 68, 0.9)); }
    }

    /* SUB-TOP: 90' CHAPTERS QUICK JUMP */
    .hud-chapters-wrap {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      margin-top: 4px;
      pointer-events: auto;
    }
    .chapters-bar {
      display: flex;
      align-items: center;
      gap: 6px;
      background: rgba(15, 23, 42, 0.82);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 9px;
      padding: 3px 8px;
      backdrop-filter: blur(12px);
      box-shadow: 0 6px 20px rgba(0,0,0,0.5);
      max-width: 88vw;
      overflow-x: auto;
    }
    .chapters-bar::-webkit-scrollbar { height: 3px; }
    .chapters-bar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 2px; }
    .chapter-btn {
      background: rgba(255, 255, 255, 0.05);
      color: var(--text-muted);
      border: 1px solid var(--border);
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 0.72rem;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.15s ease;
    }
    .chapter-btn:hover {
      background: rgba(255, 255, 255, 0.14);
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

    /* MIDDLE FLOATING STATS PILLS (LEFT & RIGHT) */
    .hud-middle-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      width: 100%;
      pointer-events: none;
      padding: 0 6px;
    }
    .hud-stat-pill {
      background: rgba(15, 23, 42, 0.86);
      border: 1px solid rgba(255, 255, 255, 0.14);
      border-radius: 12px;
      padding: 8px 14px;
      backdrop-filter: blur(14px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
      pointer-events: auto;
      min-width: 220px;
    }
    .hud-stat-title {
      font-size: 0.70rem;
      color: var(--text-muted);
      text-transform: uppercase;
      font-weight: 800;
      letter-spacing: 0.05em;
    }
    .hud-mono-val {
      font-family: 'JetBrains Mono', monospace;
      font-size: 1.15rem;
      font-weight: 800;
    }
    .shot-gauge {
      margin-top: 5px;
      background: rgba(255, 255, 255, 0.06);
      border-radius: 5px;
      height: 7px;
      overflow: hidden;
      border: 1px solid var(--border);
    }
    .shot-fill {
      height: 100%;
      background: linear-gradient(90deg, #10b981, #f59e0b, #ef4444);
      width: 0%;
      transition: width 0.08s ease;
    }

    /* BOTTOM FLOATING CONTROLS CONSOLE */
    .hud-bottom-row {
      display: flex;
      justify-content: center;
      align-items: center;
      width: 100%;
      pointer-events: none;
    }
    .controls-pill {
      display: flex;
      align-items: center;
      gap: 12px;
      background: rgba(15, 23, 42, 0.92);
      border: 1px solid rgba(255, 255, 255, 0.16);
      border-radius: 14px;
      padding: 9px 18px;
      backdrop-filter: blur(16px);
      box-shadow: 0 12px 36px rgba(0, 0, 0, 0.7);
      width: 94%;
      max-width: 1150px;
      pointer-events: auto;
    }
    .btn {
      background: #1f2937;
      color: var(--text);
      border: 1px solid var(--border);
      padding: 6px 14px;
      border-radius: 6px;
      font-size: 0.82rem;
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
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, 0.55);
      backdrop-filter: blur(6px);
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

    /* GOAL ENTRY TARGET VISUALIZER (Kanan / Kiri / Atas / Bawah Titik Masuk Bola) */
    .goal-target-visualizer {
      display: flex;
      flex-direction: column;
      align-items: center;
      margin: 12px auto 6px;
      background: rgba(15, 23, 42, 0.7);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 12px;
      padding: 10px 14px;
      max-width: 380px;
    }
    .goal-post-net-diagram {
      position: relative;
      width: 240px;
      height: 90px;
      border: 3px solid #ffffff;
      border-bottom: 2px dashed rgba(255, 255, 255, 0.5);
      background: repeating-linear-gradient(45deg, rgba(255,255,255,0.06), rgba(255,255,255,0.06) 8px, transparent 8px, transparent 16px),
                  repeating-linear-gradient(-45deg, rgba(255,255,255,0.06), rgba(255,255,255,0.06) 8px, transparent 8px, transparent 16px);
      box-shadow: inset 0 0 15px rgba(0,0,0,0.5);
      border-radius: 4px 4px 0 0;
      margin: 6px 0;
    }
    .goal-target-dot {
      position: absolute;
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: #fbbf24;
      border: 2px solid #ffffff;
      box-shadow: 0 0 14px #f59e0b, 0 0 25px #ef4444;
      transform: translate(-50%, -50%);
      animation: targetPulse 0.5s ease-in-out infinite alternate;
      z-index: 10;
    }
    @keyframes targetPulse {
      from { transform: translate(-50%, -50%) scale(0.9); }
      to { transform: translate(-50%, -50%) scale(1.35); }
    }
    .goal-net-quadrant {
      position: absolute;
      font-size: 0.55rem;
      font-weight: 700;
      color: rgba(255, 255, 255, 0.45);
      font-family: 'JetBrains Mono', monospace;
    }
    .q-tl { top: 4px; left: 6px; }
    .q-tc { top: 4px; left: 50%; transform: translateX(-50%); }
    .q-tr { top: 4px; right: 6px; }
    .q-bl { bottom: 4px; left: 6px; }
    .q-bc { bottom: 4px; left: 50%; transform: translateX(-50%); }
    .q-br { bottom: 4px; right: 6px; }

    /* GOALKEEPER ANALYTICS & CONCEDED HEATMAP MODAL */
    .gk-analytics-overlay {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(8px);
      z-index: 150;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .gk-analytics-modal {
      background: #0f172a;
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: 18px;
      width: 92vw;
      max-width: 820px;
      max-height: 88vh;
      overflow-y: auto;
      padding: 24px;
      color: #f8fafc;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.9);
      animation: fadeIn 0.2s ease-out;
    }
    .gk-header-title {
      font-size: 1.3rem;
      font-weight: 800;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      padding-bottom: 12px;
      margin-bottom: 16px;
    }
    .gk-close-btn {
      background: rgba(255, 255, 255, 0.1);
      border: none;
      color: #fff;
      font-size: 1.2rem;
      border-radius: 8px;
      width: 32px;
      height: 32px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .gk-close-btn:hover { background: rgba(239, 68, 68, 0.8); }

    .gk-cards-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
      gap: 16px;
      margin-bottom: 20px;
    }
    .gk-card {
      background: rgba(30, 41, 59, 0.7);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 12px;
      padding: 16px;
    }
    .gk-name-badge {
      font-size: 1.05rem;
      font-weight: 700;
      color: #38bdf8;
      display: flex;
      justify-content: space-between;
      margin-bottom: 10px;
    }
    .gk-net-heatmap {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      grid-template-rows: 1fr 1fr;
      gap: 4px;
      height: 120px;
      border: 3px solid #cbd5e1;
      border-bottom: 2px dashed #94a3b8;
      background: rgba(0, 0, 0, 0.4);
      border-radius: 6px 6px 0 0;
      padding: 4px;
    }
    .gk-heat-cell {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      border-radius: 4px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem;
      font-weight: 700;
      transition: all 0.2s;
    }
    .gk-heat-cell.heat-0 { background: rgba(255, 255, 255, 0.05); color: #64748b; }
    .gk-heat-cell.heat-1 { background: rgba(245, 158, 11, 0.35); color: #fde047; }
    .gk-heat-cell.heat-2 { background: rgba(239, 68, 68, 0.55); color: #ffffff; }
    .gk-heat-cell.heat-3 { background: rgba(185, 28, 28, 0.85); color: #ffffff; box-shadow: 0 0 10px rgba(239, 68, 68, 0.7); }

    .goals-history-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.82rem;
      font-family: 'JetBrains Mono', monospace;
      margin-top: 14px;
    }
    .goals-history-table th {
      background: rgba(15, 23, 42, 0.9);
      color: #94a3b8;
      padding: 8px 12px;
      text-align: left;
      font-weight: 700;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    .goals-history-table td {
      padding: 8px 12px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      color: #e2e8f0;
    }
    .goals-history-table tr:hover {
      background: rgba(255, 255, 255, 0.05);
    }

    /* FOUL / TACKLE BANNER ALERT */
    .foul-alert-banner {
      background: linear-gradient(90deg, rgba(234, 179, 8, 0.9), rgba(220, 38, 38, 0.9));
      color: #000000;
      font-weight: 800;
      font-size: 0.80rem;
      padding: 6px 14px;
      border-radius: 9999px;
      box-shadow: 0 0 20px rgba(234, 179, 8, 0.6);
      display: inline-flex;
      align-items: center;
      gap: 6px;
      letter-spacing: 0.02em;
      margin-top: 4px;
      animation: popBounce 0.3s ease-out;
    }
  </style>
</head>
<body>
  <!-- 1. FULLSCREEN 3D & 2D ENGINE (100vw x 100vh Edge-to-Edge) -->
  <div id="three-canvas-container"></div>
  <canvas id="pitch-2d-canvas"></canvas>

  <!-- CELEBRATION GOAL POPUP MODAL (Titik Masuk Gawang & Detail Assist/Gol) -->
  <div id="goal-popup-modal" class="goal-popup-overlay" style="display: none;" onclick="this.style.display='none'">
    <div class="goal-popup-card" onclick="event.stopPropagation()">
      <div class="goal-popup-burst">💥 ⚽ 💥</div>
      <div class="goal-popup-title">GOAAALLL!</div>
      <div class="goal-popup-scorer" id="popup-scorer-name">LIONEL MESSI</div>
      <div class="goal-popup-details">
        <span class="popup-badge" id="popup-minute-badge">92'</span>
        <span class="popup-stat" id="popup-type-stat">Precision Placement (Bottom Left)</span>
        <span class="popup-speed" id="popup-speed-stat">98.5 km/h</span>
      </div>

      <!-- Assist & Goalkeeper Facing Detail -->
      <div style="display: flex; justify-content: center; gap: 14px; font-size: 0.85rem; margin: 6px 0 10px; font-weight: 700;">
        <span style="color: #93c5fd;">🅰️ Assist: <span id="popup-assist-name" style="color: #ffffff;">Jordi Alba</span></span>
        <span style="color: rgba(255,255,255,0.4);">|</span>
        <span style="color: #fca5a5;">🧤 Conceded: <span id="popup-gk-name" style="color: #ffffff;">Keylor Navas</span></span>
      </div>

      <!-- GOAL ENTRY POINT TARGET VISUALIZER -->
      <div class="goal-target-visualizer">
        <div style="font-size: 0.72rem; font-weight: 800; letter-spacing: 0.05em; color: #fbbf24; text-transform: uppercase;">
          🎯 TITIK MASUK BOLA KE DALAM GAWANG:
        </div>
        <div class="goal-post-net-diagram" id="goal-post-diagram">
          <!-- Quadrant labels -->
          <span class="goal-net-quadrant q-tl">TOP LEFT</span>
          <span class="goal-net-quadrant q-tc">HIGH CENTER</span>
          <span class="goal-net-quadrant q-tr">TOP RIGHT</span>
          <span class="goal-net-quadrant q-bl">LOW LEFT</span>
          <span class="goal-net-quadrant q-bc">LOW CENTER</span>
          <span class="goal-net-quadrant q-br">LOW RIGHT</span>
          <!-- Dynamic Target Dot -->
          <div class="goal-target-dot" id="goal-target-dot" style="left: 20%; top: 75%;"></div>
        </div>
        <div id="popup-target-desc" style="font-size: 0.76rem; font-family: 'JetBrains Mono', monospace; color: #ffffff; font-weight: 700;">
          Sudut Bawah Kiri (Bottom Corner Left) · Ketinggian: 0.65m
        </div>
      </div>

      <div class="goal-popup-score" id="popup-score-display">REAL MADRID 2 - 3 FC BARCELONA</div>
      <div style="display: flex; justify-content: center; gap: 12px; margin-top: 10px;">
        <button class="btn" style="background: rgba(255,255,255,0.2); font-size: 0.75rem; padding: 4px 12px;" onclick="openGkAnalyticsModal()">📊 Lihat Statistik Gol Per Kiper</button>
        <button class="btn" style="background: #ffffff; color: #000; font-size: 0.75rem; padding: 4px 12px;" onclick="document.getElementById('goal-popup-modal').style.display='none'">Tutup (Dismiss)</button>
      </div>
    </div>
  </div>

  <!-- GOALKEEPER ANALYTICS & CONCEDED HEATMAP MODAL -->
  <div id="gk-analytics-modal-overlay" class="gk-analytics-overlay" style="display: none;" onclick="this.style.display='none'">
    <div class="gk-analytics-modal" onclick="event.stopPropagation()">
      <div class="gk-header-title">
        <span>🧤 Peta Titik Kebobolan Per Kiper & Detail Assist/Gol</span>
        <button class="gk-close-btn" onclick="document.getElementById('gk-analytics-modal-overlay').style.display='none'">✕</button>
      </div>
      <div style="font-size: 0.84rem; color: #94a3b8; margin-bottom: 14px;">
        Analisis distribusi sisi tembakan gol yang masuk ke gawang per penjaga gawang (Top/Bottom, Left/Center/Right) dari pertandingan nyata:
      </div>

      <!-- Dynamic Goalkeepers Heatmap Grid -->
      <div class="gk-cards-grid" id="gk-cards-container">
        <!-- Rendered dynamically via JS -->
      </div>

      <!-- Complete Goals & Assists History Table -->
      <div style="font-size: 0.95rem; font-weight: 800; color: #f8fafc; margin-top: 18px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 14px;">
        📋 Histori Detail Gol & Assist Pertandingan Ini
      </div>
      <table class="goals-history-table">
        <thead>
          <tr>
            <th>Menit</th>
            <th>Pencetak Gol</th>
            <th>Pemberi Assist</th>
            <th>Tim</th>
            <th>Kiper Lawan</th>
            <th>Titik / Sisi Masuk Gawang</th>
            <th>Kecepatan</th>
          </tr>
        </thead>
        <tbody id="goals-history-tbody">
          <!-- Populated via JS -->
        </tbody>
      </table>
    </div>
  </div>

  <!-- 2. FLOATING VIDEO GAME HUD OVERLAY (z-index: 10, pointer-events: none) -->
  <div class="hud-layer" id="hud-container">

    <!-- TOP ROW: Brand/Match (Left), Scoreboard (Center), Cam Angles & Fullscreen (Right) -->
    <div class="hud-top-bar">
      <!-- Top Left: Match Selector & 2D/3D View Mode -->
      <div class="hud-group">
        <div class="hud-brand">
          <span style="font-size: 1.15rem;">⚽</span>
          <div>
            <div style="font-weight: 800; font-size: 0.82rem; letter-spacing: -0.01em;">3D TACTICAL KINEMATICS</div>
            <div style="font-size: 0.65rem; color: var(--text-muted);">90' Match Arena Engine</div>
          </div>
        </div>

        <select id="match-select" onchange="onMatchChange(this.value)" class="hud-select">
          {% for m_id, m_data in matches.items() %}
            <option value="{{ m_id }}" {% if m_id == selected_match_id %}selected{% endif %}>{{ m_data.title }}</option>
          {% endfor %}
        </select>

        <div class="view-toggle">
          <button id="btn-view-3d" class="view-btn active" onclick="switchView('3d')">3D Stadium</button>
          <button id="btn-view-2d" class="view-btn" onclick="switchView('2d')">2D Planar</button>
        </div>
      </div>

      <!-- Top Center: Broadcast Scoreboard (Papan Skor) -->
      <div class="hud-scoreboard-wrap">
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
        <div id="foul-alert-banner" class="foul-alert-banner" style="display: none;">
          ⚡ <span id="foul-alert-text">FOUL! Hard Sliding Tackle</span>
        </div>
      </div>

      <!-- Top Right: 3D Camera Angles & Controls -->
      <div class="hud-group">
        <div id="cam-presets-bar" class="hud-cam-bar">
          <span style="font-size: 0.70rem; color: var(--text-muted); font-weight: 700;">🎥 CAM:</span>
          <button class="cam-btn active" onclick="setCameraPreset('broadcast')">🎮 FIFA Pitch</button>
          <button class="cam-btn" onclick="setCameraPreset('pro')">👤 Be-A-Pro (1P)</button>
          <button class="cam-btn" onclick="setCameraPreset('duel')">⚔️ Duel 1v1 (2P)</button>
          <button class="cam-btn" onclick="setCameraPreset('goal')">🥅 Behind Goal</button>
          <button class="cam-btn" onclick="setCameraPreset('action')">⚽ Dynamic</button>
          <button class="cam-btn" onclick="setCameraPreset('dugout')">🏟️ Dugout</button>
        </div>
        <button class="hud-btn" id="btn-gk-analytics" onclick="openGkAnalyticsModal()" title="Peta Gol & Analisis Kiper">🧤 Kiper & Gol</button>
        <button class="hud-btn" id="btn-toggle-fullscreen" onclick="toggleBrowserFullscreen()" title="Native Browser Fullscreen">⛶ Fullscreen</button>
        <button class="hud-btn" id="btn-toggle-hud" onclick="toggleHUD()" title="Hide / Show HUD Overlays">👁️ HUD</button>
      </div>
    </div>

    <!-- BOTTOM FLOATING CONTROLS & COMPACT TELEMETRY (All HUD anchored to bottom, zero center obstruction) -->
    <div class="hud-bottom-row" style="flex-direction: column; align-items: center; gap: 8px;">
      <!-- 90' Chapters Quick Jump Pills (Anchored right above playback bar) -->
      <div class="chapters-bar" id="chapters-bar">
        {% for ch in metadata.chapters|default([]) %}
          <button class="chapter-btn {% if 'GOAL' in ch.label %}goal-chapter{% endif %}" data-min="{{ ch.min }}" onclick="jumpToMinute({{ ch.min }})">{{ ch.label }}</button>
        {% endfor %}
      </div>

      <!-- Main Playback & Live Telemetry Strip -->
      <div class="controls-pill" style="max-width: 96vw; width: 1100px;">
        <button id="btn-play" class="btn btn-play" onclick="togglePlay()">Play ▶</button>
        <button class="btn" onclick="stepFrame(-10)">-10s</button>
        <button class="btn" onclick="stepFrame(-1)">◀</button>
        
        <!-- Scrubber Slider -->
        <div style="flex: 1; display: flex; flex-direction: column; gap: 2px;">
          <input type="range" id="frame-slider" class="slider" min="1" max="{{ total_frames }}" value="1" oninput="onSlide(this.value)">
          <div style="display: flex; justify-content: space-between; font-size: 0.62rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace;">
            <span>01' Kick-off</span>
            <span>45' HT</span>
            <span style="color: #ef4444; font-weight: 700;">89' ⚽ GOAL! (1-0)</span>
            <span>90' FT</span>
          </div>
        </div>

        <button class="btn" onclick="stepFrame(1)">▶</button>
        <button class="btn" onclick="stepFrame(10)">+10s</button>

        <!-- Compact Bottom Telemetry: Ball Speed & Possession (Unobtrusive) -->
        <div style="display: flex; gap: 14px; align-items: center; padding: 0 10px; border-left: 1px solid rgba(255,255,255,0.12); font-family: 'JetBrains Mono', monospace; font-size: 0.75rem;">
          <div><span style="color: var(--home); font-weight: 800;" id="stat-pc-home">{{ "%.1f"|format(home_pct) }}%</span> <span style="font-size: 0.65rem; color: var(--text-muted);">POSS</span> <span style="color: var(--away); font-weight: 800;" id="stat-pc-away">{{ "%.1f"|format(away_pct) }}%</span></div>
          <div style="color: rgba(255,255,255,0.2);">|</div>
          <div><span style="color: #f59e0b; font-weight: 800;" id="stat-speed">0.0 km/h</span> <span style="font-size: 0.65rem; color: var(--text-muted);" id="stat-z">0.0m</span></div>
        </div>

        <!-- Clock & Frames -->
        <div style="display: flex; flex-direction: column; align-items: flex-end; font-family: 'JetBrains Mono'; font-weight: 700; min-width: 90px; border-left: 1px solid rgba(255,255,255,0.12); padding-left: 10px;">
          <span style="color: #60a5fa; font-size: 0.94rem;" id="stat-clock">00:00</span>
          <span id="frame-label" style="font-size: 0.65rem; color: var(--text-muted);">1 / {{ total_frames }}</span>
        </div>
      </div>
    </div>

    <!-- Hidden placeholders to avoid JS null reference errors -->
    <div style="display: none;">
      <span id="lbl-status">STABLE</span>
      <span id="lbl-ball-state">GROUND PASS</span>
      <span id="lbl-speed-val">0.0 km/h</span>
      <span id="lbl-z-val">0.00 m</span>
      <span id="lbl-player">H10</span>
      <span id="lbl-team">Home</span>
      <span id="lbl-dist">0.0 m</span>
      <span id="lbl-pc-home">53.8%</span>
      <span id="lbl-pc-away">46.2%</span>
      <div id="shot-meter"></div>
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
        const testCanvas = document.createElement('canvas');
        const gl = testCanvas.getContext('webgl2') || testCanvas.getContext('webgl') || testCanvas.getContext('experimental-webgl');
        if (!gl) {
          console.info("Hardware WebGL is not available in current environment. Engaging Universal 3D Projection Engine.");
          return false;
        }

        scene = new THREE.Scene();
        scene.background = new THREE.Color(0x06090e);

        const initW = window.innerWidth;
        const initH = window.innerHeight;
        const aspect = initW / initH;
        camera = new THREE.PerspectiveCamera(40, aspect, 0.1, 1000);
        camera.position.set(52.5, 118.0, 36.0);
        camera.up.set(0, 0, 1);

        let createdRenderer = null;
        try {
          createdRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'default' });
        } catch (e1) {
          try {
            createdRenderer = new THREE.WebGLRenderer({ antialias: false, alpha: false, failIfMajorPerformanceCaveat: false });
          } catch (e2) {
            console.warn("Could not create WebGLRenderer:", e2);
            return false;
          }
        }

        if (!createdRenderer) return false;

        renderer = createdRenderer;
        renderer.setSize(initW, initH);
        renderer.shadowMap.enabled = true;
        container.appendChild(renderer.domElement);

        if (THREE.OrbitControls) {
          controls = new THREE.OrbitControls(camera, renderer.domElement);
          controls.target.set(52.5, 34.0, 1.0);
          controls.enableDamping = true;
          controls.dampingFactor = 0.05;
          controls.enableZoom = true;
          controls.zoomSpeed = 1.3;
          controls.minDistance = 5.0;
          controls.maxDistance = 260.0;
          controls.enableRotate = true;
          controls.rotateSpeed = 0.9;
          controls.enablePan = true;
          controls.panSpeed = 0.8;
          controls.maxPolarAngle = Math.PI / 2.0;
          controls.minPolarAngle = 0.01;
        }

        const ambientLight = new THREE.AmbientLight(0xffffff, 0.45);
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xfff7ed, 0.95);
        dirLight.position.set(52.5, -40, 80);
        dirLight.castShadow = true;
        scene.add(dirLight);

        const dirLight2 = new THREE.DirectionalLight(0x93c5fd, 0.35);
        dirLight2.position.set(52.5, 110, 70);
        scene.add(dirLight2);

        // Procedural Alternating FIFA Mowing Grass Texture
        function createGrassCanvasTexture() {
          const cvs = document.createElement('canvas');
          cvs.width = 1024;
          cvs.height = 512;
          const ctx = cvs.getContext('2d');
          const stripes = 10;
          const sw = cvs.width / stripes;
          for (let i = 0; i < stripes; i++) {
            ctx.fillStyle = (i % 2 === 0) ? '#14532d' : '#166534';
            ctx.fillRect(i * sw, 0, sw, cvs.height);
          }
          const tex = new THREE.CanvasTexture(cvs);
          tex.wrapS = THREE.ClampToEdgeWrapping;
          tex.wrapT = THREE.ClampToEdgeWrapping;
          return tex;
        }

        const grassTex = createGrassCanvasTexture();
        const pitchGeometry = new THREE.PlaneGeometry(105, 68);
        const pitchMaterial = new THREE.MeshStandardMaterial({
          map: grassTex,
          roughness: 0.55,
          metalness: 0.05,
          side: THREE.DoubleSide
        });
        pitchMesh = new THREE.Mesh(pitchGeometry, pitchMaterial);
        pitchMesh.position.set(52.5, 34, 0);
        pitchMesh.receiveShadow = true;
        scene.add(pitchMesh);

        // Technical Run-off Apron
        const outerGeo = new THREE.PlaneGeometry(125, 84);
        const outerMat = new THREE.MeshStandardMaterial({ color: 0x0a1e12, roughness: 0.85, side: THREE.DoubleSide });
        const outerMesh = new THREE.Mesh(outerGeo, outerMat);
        outerMesh.position.set(52.5, 34, -0.05);
        outerMesh.receiveShadow = true;
        scene.add(outerMesh);

        // 3D Stadium Grandstands (Stepped Tiered Terraces with Spectator Colors)
        function createTieredStand(x, y, w, d, h, zBase, color) {
          const standGeo = new THREE.BoxGeometry(w, d, h);
          const standMat = new THREE.MeshStandardMaterial({ color: color, roughness: 0.85 });
          const stand = new THREE.Mesh(standGeo, standMat);
          stand.position.set(x, y, zBase + h / 2);
          stand.receiveShadow = true;
          scene.add(stand);
        }
        // South Stand (Tier 1 & 2)
        createTieredStand(52.5, -12, 126, 12, 4.5, 0, 0x1e293b);
        createTieredStand(52.5, -24, 130, 16, 8.0, 4.5, 0x0f172a);
        // North Stand (Tier 1 & 2)
        createTieredStand(52.5, 80, 126, 12, 4.5, 0, 0x1e293b);
        createTieredStand(52.5, 92, 130, 16, 8.0, 4.5, 0x0f172a);
        // West Stand (Home End)
        createTieredStand(-12, 34, 12, 86, 4.5, 0, 0x1e293b);
        createTieredStand(-24, 34, 16, 92, 8.0, 4.5, 0x0f172a);
        // East Stand (Away End)
        createTieredStand(117, 34, 12, 86, 4.5, 0, 0x1e293b);
        createTieredStand(129, 34, 16, 92, 8.0, 4.5, 0x0f172a);

        // LED Electronic Advertising Boards along touchlines in 3D
        function createLedBoard(x, y, w, d, color) {
          const boardGeo = new THREE.BoxGeometry(w, d, 0.95);
          const boardMat = new THREE.MeshStandardMaterial({ color: color, roughness: 0.3, emissive: color, emissiveIntensity: 0.25 });
          const board = new THREE.Mesh(boardGeo, boardMat);
          board.position.set(x, y, 0.47);
          scene.add(board);
        }
        createLedBoard(52.5, -2.2, 108, 0.35, 0x2563eb);
        createLedBoard(52.5, 70.2, 108, 0.35, 0xdc2626);

        // 4 Stadium Floodlight Pylons
        function createFloodlightPylon(x, y) {
          const pylonPole = new THREE.Mesh(
            new THREE.CylinderGeometry(0.5, 0.7, 28, 8),
            new THREE.MeshStandardMaterial({ color: 0x475569, metalness: 0.8, roughness: 0.2 })
          );
          pylonPole.position.set(x, y, 14);
          pylonPole.rotation.x = Math.PI / 2;
          scene.add(pylonPole);

          const lightBank = new THREE.Mesh(
            new THREE.BoxGeometry(4.5, 2.5, 1.0),
            new THREE.MeshBasicMaterial({ color: 0xf8fafc })
          );
          lightBank.position.set(x, y, 28);
          scene.add(lightBank);

          const spot = new THREE.SpotLight(0xffffff, 0.7, 180, Math.PI / 4, 0.4);
          spot.position.set(x, y, 28);
          spot.target.position.set(52.5, 34, 0);
          scene.add(spot);
          scene.add(spot.target);
        }
        createFloodlightPylon(-14, -14);
        createFloodlightPylon(119, -14);
        createFloodlightPylon(-14, 82);
        createFloodlightPylon(119, 82);

        return true;
      } catch (err) {
        console.error("Three.js setup encountered error:", err);
        return false;
      }
    }

    threeInitialized = initThreeEngine();
    console.log("Three.js 3D Stadium initialized:", threeInitialized);

    // 3D Pitch Lines Wireframe & Regulation Markings
    function create3DPitchLines() {
      if (!threeInitialized) return;
      const lineMat = new THREE.LineBasicMaterial({ color: 0xffffff, linewidth: 2 });
      
      const points = [
        new THREE.Vector3(0, 0, 0.03),
        new THREE.Vector3(105, 0, 0.03),
        new THREE.Vector3(105, 68, 0.03),
        new THREE.Vector3(0, 68, 0.03),
        new THREE.Vector3(0, 0, 0.03)
      ];
      scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), lineMat));

      const halfPts = [new THREE.Vector3(52.5, 0, 0.03), new THREE.Vector3(52.5, 68, 0.03)];
      scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(halfPts), lineMat));

      const circlePts = [];
      for (let i = 0; i <= 64; i++) {
        const theta = (i / 64) * Math.PI * 2;
        circlePts.push(new THREE.Vector3(52.5 + Math.cos(theta) * 9.15, 34 + Math.sin(theta) * 9.15, 0.03));
      }
      scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(circlePts), lineMat));

      // 18-Yard Penalty Boxes & 6-Yard Goal Areas in 3D
      function addBoxLines(minX, maxX, minY, maxY) {
        const boxPts = [
          new THREE.Vector3(minX, minY, 0.03),
          new THREE.Vector3(maxX, minY, 0.03),
          new THREE.Vector3(maxX, maxY, 0.03),
          new THREE.Vector3(minX, maxY, 0.03)
        ];
        scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(boxPts), lineMat));
      }
      addBoxLines(0, 16.5, 13.84, 54.16);
      addBoxLines(0, 5.5, 24.84, 43.16);
      addBoxLines(105, 105 - 16.5, 13.84, 54.16);
      addBoxLines(105, 105 - 5.5, 24.84, 43.16);

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
        new THREE.SphereGeometry(0.32, 16, 16),
        new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3, metalness: 0.1 })
      );
      ballMesh.castShadow = true;
      scene.add(ballMesh);

      ballShadow = new THREE.Mesh(
        new THREE.CircleGeometry(0.32, 16),
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

    // High-Fidelity Humanoid Footballer Generator (Authentic FIFA Video Game Style)
    function createPlayerNumberTexture(num, team) {
      const cvs = document.createElement('canvas');
      cvs.width = 128;
      cvs.height = 128;
      const ctx = cvs.getContext('2d');
      if (team === 'Home') {
        // Authentic FC Barcelona Blaugrana Stripes
        const sw = 128 / 4;
        for (let s = 0; s < 4; s++) {
          ctx.fillStyle = (s % 2 === 0) ? '#991b1b' : '#1d4ed8';
          ctx.fillRect(s * sw, 0, sw, 128);
        }
        ctx.fillStyle = '#ffffff';
      } else {
        // Real Madrid Crisp Athletic White Kit with subtle contrast
        ctx.fillStyle = '#f8fafc';
        ctx.fillRect(0, 0, 128, 128);
        ctx.fillStyle = '#0f172a';
      }
      ctx.font = 'bold 72px monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(num || '', 64, 64);
      return new THREE.CanvasTexture(cvs);
    }

    function createPlayerNameSprite(name, num) {
      const cvs = document.createElement('canvas');
      cvs.width = 64;
      cvs.height = 64;
      const ctx = cvs.getContext('2d');
      // Compact circular badge
      ctx.fillStyle = 'rgba(15, 23, 42, 0.75)';
      ctx.beginPath();
      ctx.arc(32, 32, 28, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)';
      ctx.lineWidth = 3;
      ctx.stroke();
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 30px "JetBrains Mono", monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(`${num || ''}`, 32, 33);
      const tex = new THREE.CanvasTexture(cvs);
      const spriteMat = new THREE.SpriteMaterial({ map: tex, transparent: true });
      const sprite = new THREE.Sprite(spriteMat);
      sprite.scale.set(0.35, 0.35, 1);
      sprite.position.z = 2.15;
      return sprite;
    }

    function getOrCreatePlayerMesh(id, team, pData) {
      if (!threeInitialized) return null;
      if (playerMeshes[id]) return playerMeshes[id];

      const pGroup = new THREE.Group();
      const isHome = (team === 'Home');
      const isGK = (id === 'H1' || id === 'A1' || (pData && pData.role === 'GK'));
      const num = pData?.num !== undefined ? pData.num : id.replace(/[^\d]/g, '');
      const name = pData?.name || id;

      // Kit Colors
      let kitColor = isHome ? 0xef4444 : 0xeab308;
      let shortColor = isHome ? 0x2563eb : 0x0f172a;
      let sockColor = isHome ? 0xef4444 : 0xeab308;
      if (isGK) {
        kitColor = isHome ? 0x10b981 : 0xf97316; // Neon green or bright orange for GK
        shortColor = 0x064e3b;
        sockColor = kitColor;
      }

      const skinMat = new THREE.MeshStandardMaterial({ color: 0xffd1b3, roughness: 0.65 });
      const hairMat = new THREE.MeshStandardMaterial({ color: 0x26190e, roughness: 0.8 });
      const kitMat = new THREE.MeshStandardMaterial({ color: kitColor, roughness: 0.5 });
      const shortMat = new THREE.MeshStandardMaterial({ color: shortColor, roughness: 0.5 });
      const sockMat = new THREE.MeshStandardMaterial({ color: sockColor, roughness: 0.5 });
      const bootMat = new THREE.MeshStandardMaterial({ color: 0x111827, roughness: 0.3 });

      // 1. Torso / Jersey (Front & Back with Squad Number Texture on +Y and -Y faces)
      const numTex = createPlayerNumberTexture(num, team);
      const torsoMat = [
        kitMat, // +X Right
        kitMat, // -X Left
        new THREE.MeshStandardMaterial({ map: numTex, roughness: 0.5 }), // +Y Front Chest
        new THREE.MeshStandardMaterial({ map: numTex, roughness: 0.5 }), // -Y Back Squad Number
        kitMat,   // +Z Neck
        shortMat  // -Z Waist
      ];
      const torso = new THREE.Mesh(new THREE.BoxGeometry(0.58, 0.32, 0.72), torsoMat);
      torso.position.z = 1.25;
      torso.castShadow = true;
      pGroup.add(torso);

      // 2. Head & Hair
      const head = new THREE.Mesh(new THREE.SphereGeometry(0.20, 16, 16), skinMat);
      head.position.z = 1.76;
      head.castShadow = true;
      pGroup.add(head);

      const hair = new THREE.Mesh(new THREE.SphereGeometry(0.21, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2), hairMat);
      hair.position.z = 1.79;
      pGroup.add(hair);

      // 3. Arms & Shoulders (Left & Right)
      [-0.34, 0.34].forEach(xOff => {
        // Shoulder / Upper sleeve
        const sleeve = new THREE.Mesh(new THREE.CylinderGeometry(0.10, 0.10, 0.28, 8), kitMat);
        sleeve.position.set(xOff, 0, 1.40);
        sleeve.rotation.x = Math.PI / 2;
        pGroup.add(sleeve);
        // Forearm skin
        const arm = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.32, 8), skinMat);
        arm.position.set(xOff, 0.05, 1.15);
        arm.rotation.x = Math.PI / 2;
        pGroup.add(arm);
      });

      // 4. Shorts / Pelvis
      const shorts = new THREE.Mesh(new THREE.BoxGeometry(0.54, 0.30, 0.32), shortMat);
      shorts.position.z = 0.80;
      shorts.castShadow = true;
      pGroup.add(shorts);

      // 5. Legs, Socks & Boots as Articulated Pivot Groups (Left & Right)
      const leftLeg = new THREE.Group();
      leftLeg.position.set(-0.15, 0, 0.75); // Hip pivot

      const leftThigh = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.10, 0.35, 8), skinMat);
      leftThigh.position.set(0, 0, -0.17);
      leftThigh.rotation.x = Math.PI / 2;
      leftLeg.add(leftThigh);

      const leftCalf = new THREE.Mesh(new THREE.CylinderGeometry(0.10, 0.09, 0.38, 8), sockMat);
      leftCalf.position.set(0, 0, -0.50);
      leftCalf.rotation.x = Math.PI / 2;
      leftLeg.add(leftCalf);

      const leftBoot = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.26, 0.10), bootMat);
      leftBoot.position.set(0, 0.06, -0.70);
      leftLeg.add(leftBoot);

      pGroup.add(leftLeg);

      const rightLeg = new THREE.Group();
      rightLeg.position.set(0.15, 0, 0.75); // Hip pivot

      const rightThigh = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.10, 0.35, 8), skinMat);
      rightThigh.position.set(0, 0, -0.17);
      rightThigh.rotation.x = Math.PI / 2;
      rightLeg.add(rightThigh);

      const rightCalf = new THREE.Mesh(new THREE.CylinderGeometry(0.10, 0.09, 0.38, 8), sockMat);
      rightCalf.position.set(0, 0, -0.50);
      rightCalf.rotation.x = Math.PI / 2;
      rightLeg.add(rightCalf);

      const rightBoot = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.26, 0.10), bootMat);
      rightBoot.position.set(0, 0.06, -0.70);
      rightLeg.add(rightBoot);

      pGroup.add(rightLeg);

      pGroup.userData = { leftLeg, rightLeg };

      // 6. 3D Floating Name Pill Sprite above Player Head
      const nameSprite = createPlayerNameSprite(name, num);
      pGroup.add(nameSprite);
      pGroup.userData.nameSprite = nameSprite;

      // Realistic TV broadcast player scale (compact & proportional)
      pGroup.scale.set(0.55, 0.55, 0.55);

      scene.add(pGroup);
      playerMeshes[id] = pGroup;
      return pGroup;
    }

    // ---------------- UNIVERSAL 3D CANVAS PERSPECTIVE PROJECTION ENGINE ----------------
    const canvas2D = document.getElementById('pitch-2d-canvas');
    const ctx2D = canvas2D.getContext('2d');

    // ---------------- UNIVERSAL ROBUST 3D PERSPECTIVE ENGINE (LOOKAT VECTOR CAMERA) ----------------
    let camPosX = 52.5;
    let camPosY = -36.0;
    let camPosZ = 42.0;
    let camTargetX = 52.5;
    let camTargetY = 34.0;
    let camTargetZ = 0.0;
    let camFov = 42.0;
    let currentCamPreset = 'broadcast';
    let isDragging = false;
    let lastMouseX = 0;
    let lastMouseY = 0;

    // Orbit Spherical Angles for 360 degree drag rotation & zoom
    let orbitYaw = 0.0;       // 0 = south sideline TV view, Math.PI = north sideline
    let orbitPitch = 0.50;    // ~28 degrees elevation above pitch
    let orbitDist = 82.0;     // comfortable distance to see all 22 players

    function updateCameraPositionFromOrbit() {
      const cosP = Math.cos(orbitPitch);
      const sinP = Math.sin(orbitPitch);
      const sinY = Math.sin(orbitYaw);
      const cosY = Math.cos(orbitYaw);

      camPosX = camTargetX - sinY * (orbitDist * cosP);
      camPosY = camTargetY - cosY * (orbitDist * cosP);
      camPosZ = camTargetZ + orbitDist * sinP;
    }
    updateCameraPositionFromOrbit();

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

      // 360 degree smooth rotation without gimbal lock
      orbitYaw -= dx * 0.006;
      orbitPitch = Math.max(0.08, Math.min(1.45, orbitPitch + dy * 0.006));
      updateCameraPositionFromOrbit();
      render(currentFrame);
    });

    window.addEventListener('mouseup', () => { isDragging = false; });

    canvas2D.addEventListener('wheel', (e) => {
      if (activeView !== '3d') return;
      e.preventDefault();
      orbitDist = Math.max(25.0, Math.min(180.0, orbitDist + e.deltaY * 0.08));
      updateCameraPositionFromOrbit();
      render(currentFrame);
    }, { passive: false });

    function resizeCanvas() {
      if (canvas2D) {
        canvas2D.width = window.innerWidth;
        canvas2D.height = window.innerHeight;
      }
      if (threeInitialized && camera && renderer && container) {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
      }
    }

    function project3D(x, y, z, W, H) {
      // 1. Forward Vector (Camera -> Target)
      const fX = camTargetX - camPosX;
      const fY = camTargetY - camPosY;
      const fZ = camTargetZ - camPosZ;
      const fLen = Math.hypot(fX, fY, fZ) || 1.0;
      const fx = fX / fLen, fy = fY / fLen, fz = fZ / fLen;

      // 2. Camera Right = Forward x WorldUp (0, 0, 1)
      const rX = fy * 1.0;
      const rY = -fx * 1.0;
      const rZ = 0.0;
      const rLen = Math.hypot(rX, rY, rZ) || 1.0;
      const rx = rX / rLen, ry = rY / rLen, rz = rZ / rLen;

      // 3. Camera Up = Right x Forward
      const ux = ry * fz - rz * fy;
      const uy = rz * fx - rx * fz;
      const uz = rx * fy - ry * fx;

      // 4. Point in Camera Coordinates
      const dx = x - camPosX;
      const dy = y - camPosY;
      const dz = (z || 0) - camPosZ;

      const xCam = dx * rx + dy * ry + dz * rz;
      const yCam = dx * ux + dy * uy + dz * uz;
      const zCam = dx * fx + dy * fy + dz * fz;

      if (zCam <= 1.0) return { x: -9999, y: -9999, scale: 0, depth: zCam, visible: false };

      // 5. Focal Length from Field of View
      const fovRad = (camFov * Math.PI) / 180;
      const focal = (H / 2) / Math.tan(fovRad / 2);

      // 6. Screen Projection: Ground is strictly at the BOTTOM, Height (z) grows toward TOP
      const px = (W / 2) + (xCam / zCam) * focal;
      const py = (H / 2) - (yCam / zCam) * focal;
      const scale = Math.min(1.8, Math.max(0.12, focal / zCam));

      return { x: px, y: py, scale: scale, depth: zCam, visible: true };
    }

    // High-Fidelity Universal 3D Stadium Projection Engine
    function render3DStadium(frameData) {
      if (!canvas2D.width || !canvas2D.height) resizeCanvas();
      const W = canvas2D.width;
      const H = canvas2D.height;

      // 1. Stadium Night Arena Horizon & Sky with Atmospheric Floodlight Haze
      const bgGrad = ctx2D.createRadialGradient(W / 2, H * 0.28, 20, W / 2, H * 0.35, W * 0.85);
      bgGrad.addColorStop(0, '#0a1628');
      bgGrad.addColorStop(0.35, '#060d1a');
      bgGrad.addColorStop(0.7, '#03060c');
      bgGrad.addColorStop(1, '#010204');
      ctx2D.fillStyle = bgGrad;
      ctx2D.fillRect(0, 0, W, H);

      // Stadium Floodlight Cones (Atmospheric Night Glow)
      const lightPylons = [
        project3D(-18, -16, 26, W, H),
        project3D(123, -16, 26, W, H),
        project3D(-18, 84, 26, W, H),
        project3D(123, 84, 26, W, H)
      ];
      lightPylons.forEach(lp => {
        if (!lp.visible || lp.depth <= 0) return;
        const glow = ctx2D.createRadialGradient(lp.x, lp.y, 2, lp.x, lp.y, Math.max(30, 80 * lp.scale));
        glow.addColorStop(0, 'rgba(255, 255, 255, 0.85)');
        glow.addColorStop(0.2, 'rgba(199, 235, 255, 0.45)');
        glow.addColorStop(1, 'rgba(56, 189, 248, 0)');
        ctx2D.fillStyle = glow;
        ctx2D.beginPath();
        ctx2D.arc(lp.x, lp.y, Math.max(30, 80 * lp.scale), 0, Math.PI * 2);
        ctx2D.fill();
      });

      // Helper function to draw 3D Quad
      function draw3DQuad(p1, p2, p3, p4, fillStyle, strokeStyle = null) {
        if (!p1.visible || !p2.visible || !p3.visible || !p4.visible) return;
        ctx2D.fillStyle = fillStyle;
        ctx2D.beginPath();
        ctx2D.moveTo(p1.x, p1.y);
        ctx2D.lineTo(p2.x, p2.y);
        ctx2D.lineTo(p3.x, p3.y);
        ctx2D.lineTo(p4.x, p4.y);
        ctx2D.closePath();
        ctx2D.fill();
        if (strokeStyle) {
          ctx2D.strokeStyle = strokeStyle;
          ctx2D.lineWidth = 1;
          ctx2D.stroke();
        }
      }

      // 2. Multi-Tiered Stadium Grandstands (Tribunes with Spectators / Fans)
      function drawTieredStand(xMin, xMax, yMin, yMax, zBase, zTop, color, isCrowd = false) {
        const p1 = project3D(xMin, yMin, zBase, W, H);
        const p2 = project3D(xMax, yMin, zBase, W, H);
        const p3 = project3D(xMax, yMax, zTop, W, H);
        const p4 = project3D(xMin, yMax, zTop, W, H);
        draw3DQuad(p1, p2, p3, p4, color, 'rgba(255, 255, 255, 0.08)');

        // Procedural Spectator Crowd Texture (Thousands of fans in team colors)
        if (isCrowd && p1.visible && p3.visible) {
          const stepsX = 14;
          const stepsY = 4;
          for (let ix = 0; ix < stepsX; ix++) {
            for (let iy = 0; iy < stepsY; iy++) {
              const u = (ix + 0.5) / stepsX;
              const v = (iy + 0.5) / stepsY;
              const cx = xMin + (xMax - xMin) * u;
              const cy = yMin + (yMax - yMin) * v;
              const cz = zBase + (zTop - zBase) * v + 0.4;
              const pt = project3D(cx, cy, cz, W, H);
              if (pt.visible) {
                // Alternating fan jersey colors (Red, Blue, White, Yellow, Scarf lights)
                const cIdx = (ix * 3 + iy * 7) % 5;
                const fanColor = cIdx === 0 ? '#ef4444' : (cIdx === 1 ? '#3b82f6' : (cIdx === 2 ? '#f8fafc' : (cIdx === 3 ? '#eab308' : '#10b981')));
                ctx2D.fillStyle = fanColor;
                ctx2D.beginPath();
                ctx2D.arc(pt.x, pt.y, Math.max(1, 1.8 * pt.scale), 0, Math.PI * 2);
                ctx2D.fill();
              }
            }
          }
        }
      }

      // North Stand (Top)
      drawTieredStand(-16, 121, 74, 86, 0, 4.5, '#1e293b', true);
      drawTieredStand(-18, 123, 86, 102, 4.5, 11.5, '#0f172a', true);
      // South Stand (Bottom)
      drawTieredStand(-16, 121, -6, -18, 0, 4.5, '#1e293b', true);
      drawTieredStand(-18, 123, -18, -34, 4.5, 11.5, '#0f172a', true);
      // West Stand (Home End / Left)
      drawTieredStand(-6, -18, -6, 74, 0, 4.5, '#1e293b', true);
      drawTieredStand(-18, -32, -18, 86, 4.5, 11.5, '#0f172a', true);
      // East Stand (Away End / Right)
      drawTieredStand(111, 123, -6, 74, 0, 4.5, '#1e293b', true);
      drawTieredStand(123, 137, -18, 86, 4.5, 11.5, '#0f172a', true);

      // 3. Concrete Pitch Run-Off Apron / Outer Turf
      const apronP1 = project3D(-6, -6, -0.05, W, H);
      const apronP2 = project3D(111, -6, -0.05, W, H);
      const apronP3 = project3D(111, 74, -0.05, W, H);
      const apronP4 = project3D(-6, 74, -0.05, W, H);
      draw3DQuad(apronP1, apronP2, apronP3, apronP4, '#0c2817');

      // 4. Perimeter LED Electronic Advertising Boards (A-Boards along touchlines)
      function drawLedRibbon(x0, y0, x1, y1) {
        const b1 = project3D(x0, y0, 0, W, H);
        const b2 = project3D(x1, y1, 0, W, H);
        const t1 = project3D(x0, y0, 0.95, W, H);
        const t2 = project3D(x1, y1, 0.95, W, H);
        if (!b1.visible || !b2.visible || !t1.visible || !t2.visible) return;

        // Draw segmented glowing LED panels
        const segs = 8;
        for (let s = 0; s < segs; s++) {
          const uA = s / segs;
          const uB = (s + 1) / segs;
          const pA0 = project3D(x0 + (x1 - x0) * uA, y0 + (y1 - y0) * uA, 0, W, H);
          const pB0 = project3D(x0 + (x1 - x0) * uB, y0 + (y1 - y0) * uB, 0, W, H);
          const pA1 = project3D(x0 + (x1 - x0) * uA, y0 + (y1 - y0) * uA, 0.95, W, H);
          const pB1 = project3D(x0 + (x1 - x0) * uB, y0 + (y1 - y0) * uB, 0.95, W, H);

          const ledColor = (s % 3 === 0) ? '#2563eb' : ((s % 3 === 1) ? '#dc2626' : '#059669');
          draw3DQuad(pA0, pB0, pB1, pA1, ledColor, 'rgba(255, 255, 255, 0.4)');
        }
      }
      drawLedRibbon(-2.5, -2.2, 107.5, -2.2); // South Touchline LED Board
      drawLedRibbon(-2.5, 70.2, 107.5, 70.2); // North Touchline LED Board

      // 5. Realistic 3D Grass Mown Bands (10 Alternating FIFA Green Stripes)
      const numBands = 10;
      const bStep = 105.0 / numBands;
      for (let i = 0; i < numBands; i++) {
        const x0 = i * bStep;
        const x1 = (i + 1) * bStep;
        const p1 = project3D(x0, 0, 0, W, H);
        const p2 = project3D(x1, 0, 0, W, H);
        const p3 = project3D(x1, 68, 0, W, H);
        const p4 = project3D(x0, 68, 0, W, H);
        draw3DQuad(p1, p2, p3, p4, (i % 2 === 0) ? '#15803d' : '#166534');
      }

      // 6. 3D Regulation Pitch Lines
      ctx2D.strokeStyle = 'rgba(255, 255, 255, 0.92)';
      ctx2D.lineWidth = Math.max(1.5, 2.2 * (W / 1200));

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

      // Boundary Lines
      draw3DPoly([[0, 0], [105, 0], [105, 68], [0, 68]], true);
      // Halfway Line
      draw3DPoly([[52.5, 0], [52.5, 68]]);

      // Center Circle in 3D
      const centerCirclePts = [];
      for (let a = 0; a <= 36; a++) {
        const theta = (a / 36) * Math.PI * 2;
        centerCirclePts.push([52.5 + Math.cos(theta) * 9.15, 34.0 + Math.sin(theta) * 9.15]);
      }
      draw3DPoly(centerCirclePts, true);

      // Center Spot
      const cSpot = project3D(52.5, 34, 0, W, H);
      if (cSpot.visible) {
        ctx2D.fillStyle = '#ffffff';
        ctx2D.beginPath();
        ctx2D.arc(cSpot.x, cSpot.y, Math.max(2, 3.5 * cSpot.scale), 0, Math.PI * 2);
        ctx2D.fill();
      }

      // Penalty Boxes & 6-Yard Goal Areas
      draw3DPoly([[0, 13.84], [16.5, 13.84], [16.5, 54.16], [0, 54.16]], true);
      draw3DPoly([[0, 24.84], [5.5, 24.84], [5.5, 43.16], [0, 43.16]], true);
      draw3DPoly([[105, 13.84], [105 - 16.5, 13.84], [105 - 16.5, 54.16], [105, 54.16]], true);
      draw3DPoly([[105, 24.84], [105 - 5.5, 24.84], [105 - 5.5, 43.16], [105, 43.16]], true);

      // Penalty Spots & D-Arcs
      const hPenSpot = project3D(11.0, 34.0, 0, W, H);
      if (hPenSpot.visible) {
        ctx2D.beginPath(); ctx2D.arc(hPenSpot.x, hPenSpot.y, Math.max(1.8, 3.0 * hPenSpot.scale), 0, Math.PI * 2); ctx2D.fill();
      }
      const aPenSpot = project3D(105 - 11.0, 34.0, 0, W, H);
      if (aPenSpot.visible) {
        ctx2D.beginPath(); ctx2D.arc(aPenSpot.x, aPenSpot.y, Math.max(1.8, 3.0 * aPenSpot.scale), 0, Math.PI * 2); ctx2D.fill();
      }

      // Penalty D-Arcs
      const hArcPts = [];
      for (let a = -48; a <= 48; a += 6) {
        const rad = (a * Math.PI) / 180;
        hArcPts.push([11.0 + Math.cos(rad) * 9.15, 34.0 + Math.sin(rad) * 9.15]);
      }
      draw3DPoly(hArcPts);

      const aArcPts = [];
      for (let a = -48; a <= 48; a += 6) {
        const rad = (a * Math.PI) / 180;
        aArcPts.push([105 - 11.0 - Math.cos(rad) * 9.15, 34.0 + Math.sin(rad) * 9.15]);
      }
      draw3DPoly(aArcPts);

      // 7. 4 Corner Flag Poles with Fluttering Flags
      [[0, 0], [105, 0], [105, 68], [0, 68]].forEach(([cx, cy]) => {
        const fBase = project3D(cx, cy, 0, W, H);
        const fTop = project3D(cx, cy, 1.55, W, H);
        const fTip = project3D(cx + (cx === 0 ? 0.6 : -0.6), cy, 1.35, W, H);
        if (fBase.visible && fTop.visible && fTip.visible) {
          ctx2D.strokeStyle = '#ffffff';
          ctx2D.lineWidth = 1.8;
          ctx2D.beginPath(); ctx2D.moveTo(fBase.x, fBase.y); ctx2D.lineTo(fTop.x, fTop.y); ctx2D.stroke();
          // Yellow & Red Corner Flag
          ctx2D.fillStyle = '#eab308';
          ctx2D.beginPath(); ctx2D.moveTo(fTop.x, fTop.y); ctx2D.lineTo(fTip.x, fTip.y); ctx2D.lineTo(fTop.x, fTop.y + 7 * fTop.scale); ctx2D.closePath(); ctx2D.fill();
        }
      });

      // 8. 3D Goal Posts (2.44m tall) & 3D Netting Cage with Diamond Mesh
      function draw3DGoal(gx, gyMin, gyMax, depthDir) {
        ctx2D.strokeStyle = '#ffffff';
        ctx2D.lineWidth = 2.8;
        const p1 = project3D(gx, gyMin, 0, W, H);
        const p2 = project3D(gx, gyMin, 2.44, W, H);
        const p3 = project3D(gx, gyMax, 2.44, W, H);
        const p4 = project3D(gx, gyMax, 0, W, H);
        ctx2D.beginPath();
        ctx2D.moveTo(p1.x, p1.y); ctx2D.lineTo(p2.x, p2.y); ctx2D.lineTo(p3.x, p3.y); ctx2D.lineTo(p4.x, p4.y);
        ctx2D.stroke();

        const nb1 = project3D(gx + depthDir * 2.4, gyMin, 0, W, H);
        const nb2 = project3D(gx + depthDir * 2.4, gyMin, 2.1, W, H);
        const nb3 = project3D(gx + depthDir * 2.4, gyMax, 2.1, W, H);
        const nb4 = project3D(gx + depthDir * 2.4, gyMax, 0, W, H);
        ctx2D.strokeStyle = 'rgba(255, 255, 255, 0.45)';
        ctx2D.lineWidth = 1.2;
        ctx2D.beginPath();
        ctx2D.moveTo(p2.x, p2.y); ctx2D.lineTo(nb2.x, nb2.y); ctx2D.lineTo(nb3.x, nb3.y); ctx2D.lineTo(p3.x, p3.y);
        ctx2D.moveTo(nb2.x, nb2.y); ctx2D.lineTo(nb1.x, nb1.y);
        ctx2D.moveTo(nb3.x, nb3.y); ctx2D.lineTo(nb4.x, nb4.y);
        ctx2D.stroke();

        // Netting Grid Cross-Hatching
        ctx2D.strokeStyle = 'rgba(255, 255, 255, 0.18)';
        ctx2D.lineWidth = 0.8;
        for (let i = 1; i <= 4; i++) {
          const u = i / 5;
          const ny1 = gyMin + (gyMax - gyMin) * u;
          const pA = project3D(gx, ny1, 2.44, W, H);
          const pB = project3D(gx + depthDir * 2.4, ny1, 2.1, W, H);
          const pC = project3D(gx + depthDir * 2.4, ny1, 0, W, H);
          ctx2D.beginPath(); ctx2D.moveTo(pA.x, pA.y); ctx2D.lineTo(pB.x, pB.y); ctx2D.lineTo(pC.x, pC.y); ctx2D.stroke();
        }
      }
      draw3DGoal(0, 30.34, 37.66, -1);
      draw3DGoal(105, 30.34, 37.66, 1);

      // 9. Depth-Sorted Entities (Humanoid Players & Ball with Z-Buffer Sorting)
      const renderList = [];

      frameData.players.forEach(p => {
        const basePr = project3D(p.x, p.y, 0, W, H);
        renderList.push({
          type: 'player',
          depth: basePr.depth,
          data: p,
          base: basePr
        });
      });

      const b = frameData.ball;
      const bBallPr = project3D(b.x, b.y, b.z || 0, W, H);
      renderList.push({
        type: 'ball',
        depth: bBallPr.depth,
        data: b,
        ball: bBallPr
      });

      renderList.sort((a, b) => b.depth - a.depth);

      // 10. Draw Sorted Entities: Authentic FIFA Video Game Humanoid Footballers
      renderList.forEach(item => {
        if (item.type === 'player') {
          const p = item.data;
          const base = item.base;
          if (!base.visible || base.depth <= 0) return;

          const isHome = (p.team === 'Home');
          const isGK = (p.role === 'GK' || p.id === 'H1' || p.id === 'A1');
          const num = p.num !== undefined ? String(p.num) : (p.id.replace(/[^\d]/g, '') || '10');
          const name = p.name || p.id;

          // Biomechanical Kinematics: Calculate facing orientation & leg stride
          const vx = p.vx || 0;
          const vy = p.vy || 0;
          const speed = Math.sqrt(vx * vx + vy * vy);
          const facing = speed > 0.3 ? Math.atan2(vy, vx) : Math.atan2(b.y - p.y, b.x - p.x);
          const fCos = Math.cos(facing);
          const fSin = Math.sin(facing);
          const rCos = -fSin; // perpendicular right vector
          const rSin = fCos;

          // Running leg and arm swing animation
          const stridePhase = (currentFrame * 0.45) + (parseInt(num) * 1.3);
          const legSwing = (speed > 0.3) ? Math.sin(stridePhase) * Math.min(0.35, 0.12 + speed * 0.05) : 0;
          const armSwing = -legSwing * 0.85;

          // Scale factor based on perspective distance
          const sc = base.scale;
          const rad = Math.max(3.0, 6.2 * sc);

          // A. Ground Contact Drop Shadow
          ctx2D.fillStyle = 'rgba(0, 0, 0, 0.45)';
          ctx2D.beginPath();
          ctx2D.ellipse(base.x, base.y, rad * 1.3, rad * 0.55, 0, 0, Math.PI * 2);
          ctx2D.fill();

          // B. Football Boots / Cleats (Left & Right Foot)
          const lFootX = p.x - rCos * 0.16 - fCos * legSwing;
          const lFootY = p.y - rSin * 0.16 - fSin * legSwing;
          const lFootZ = Math.max(0, Math.sin(stridePhase) * 0.16 * (speed > 0.3 ? 1 : 0));
          const lFootPr = project3D(lFootX, lFootY, lFootZ, W, H);
          const lToePr = project3D(lFootX + fCos * 0.22, lFootY + fSin * 0.22, lFootZ, W, H);

          const rFootX = p.x + rCos * 0.16 + fCos * legSwing;
          const rFootY = p.y + rSin * 0.16 + fSin * legSwing;
          const rFootZ = Math.max(0, -Math.sin(stridePhase) * 0.16 * (speed > 0.3 ? 1 : 0));
          const rFootPr = project3D(rFootX, rFootY, rFootZ, W, H);
          const rToePr = project3D(rFootX + fCos * 0.22, rFootY + fSin * 0.22, rFootZ, W, H);

          // Draw Boots
          ctx2D.strokeStyle = '#111827';
          ctx2D.lineWidth = Math.max(2.0, 3.2 * sc);
          if (lFootPr.visible && lToePr.visible) {
            ctx2D.beginPath(); ctx2D.moveTo(lFootPr.x, lFootPr.y); ctx2D.lineTo(lToePr.x, lToePr.y); ctx2D.stroke();
          }
          if (rFootPr.visible && rToePr.visible) {
            ctx2D.beginPath(); ctx2D.moveTo(rFootPr.x, rFootPr.y); ctx2D.lineTo(rToePr.x, rToePr.y); ctx2D.stroke();
          }

          // C. Calves & Team Socks (From Boots to Knee z=0.48)
          const lKneePr = project3D(p.x - rCos * 0.16 - fCos * (legSwing * 0.5), p.y - rSin * 0.16 - fSin * (legSwing * 0.5), 0.48, W, H);
          const rKneePr = project3D(p.x + rCos * 0.16 + fCos * (legSwing * 0.5), p.y + rSin * 0.16 + fSin * (legSwing * 0.5), 0.48, W, H);

          const sockColor = isGK ? '#10b981' : (isHome ? '#dc2626' : '#eab308');
          ctx2D.strokeStyle = sockColor;
          ctx2D.lineWidth = Math.max(2.2, 3.8 * sc);
          if (lFootPr.visible && lKneePr.visible) {
            ctx2D.beginPath(); ctx2D.moveTo(lFootPr.x, lFootPr.y); ctx2D.lineTo(lKneePr.x, lKneePr.y); ctx2D.stroke();
          }
          if (rFootPr.visible && rKneePr.visible) {
            ctx2D.beginPath(); ctx2D.moveTo(rFootPr.x, rFootPr.y); ctx2D.lineTo(rKneePr.x, rKneePr.y); ctx2D.stroke();
          }

          // D. Shorts / Pelvis (From Knee z=0.48 to Waist z=0.92)
          const waistPr = project3D(p.x, p.y, 0.92, W, H);
          const shortColor = isGK ? '#064e3b' : (isHome ? '#1d4ed8' : '#f8fafc');
          if (lKneePr.visible && rKneePr.visible && waistPr.visible) {
            ctx2D.fillStyle = shortColor;
            ctx2D.beginPath();
            ctx2D.moveTo(waistPr.x - 3.8 * sc, waistPr.y);
            ctx2D.lineTo(lKneePr.x, lKneePr.y);
            ctx2D.lineTo(rKneePr.x, rKneePr.y);
            ctx2D.lineTo(waistPr.x + 3.8 * sc, waistPr.y);
            ctx2D.closePath();
            ctx2D.fill();
            ctx2D.strokeStyle = 'rgba(0,0,0,0.2)';
            ctx2D.lineWidth = 0.8;
            ctx2D.stroke();
          }

          // E. Torso & Team Jersey (From Waist z=0.92 to Shoulders z=1.48)
          const chestPr = project3D(p.x, p.y, 1.25, W, H);
          const lShoulderPr = project3D(p.x - rCos * 0.30, p.y - rSin * 0.30, 1.48, W, H);
          const rShoulderPr = project3D(p.x + rCos * 0.30, p.y + rSin * 0.30, 1.48, W, H);
          const neckPr = project3D(p.x, p.y, 1.54, W, H);

          if (waistPr.visible && lShoulderPr.visible && rShoulderPr.visible) {
            // Main Jersey Fill
            if (isGK) {
              ctx2D.fillStyle = '#10b981';
            } else if (isHome) {
              // Barcelona Blaugrana Garnet & Blue Gradient / Vertical Stripes
              const jGrad = ctx2D.createLinearGradient(lShoulderPr.x, lShoulderPr.y, rShoulderPr.x, rShoulderPr.y);
              jGrad.addColorStop(0, '#991b1b');
              jGrad.addColorStop(0.35, '#1d4ed8');
              jGrad.addColorStop(0.7, '#991b1b');
              jGrad.addColorStop(1, '#1d4ed8');
              ctx2D.fillStyle = jGrad;
            } else {
              // Real Madrid Crisp White with Gold/Dark Trim
              ctx2D.fillStyle = '#f8fafc';
            }

            ctx2D.beginPath();
            ctx2D.moveTo(waistPr.x - 3.2 * sc, waistPr.y);
            ctx2D.lineTo(lShoulderPr.x, lShoulderPr.y);
            ctx2D.lineTo(rShoulderPr.x, rShoulderPr.y);
            ctx2D.lineTo(waistPr.x + 3.2 * sc, waistPr.y);
            ctx2D.closePath();
            ctx2D.fill();
            ctx2D.strokeStyle = 'rgba(0,0,0,0.25)';
            ctx2D.lineWidth = 0.8;
            ctx2D.stroke();

            // Squad Number in Bold Monospace on Jersey Back/Front
            if (chestPr.visible) {
              ctx2D.fillStyle = (isHome || isGK) ? '#ffffff' : '#0f172a';
              ctx2D.font = `bold ${Math.max(7, Math.round(8.5 * sc))}px 'JetBrains Mono', monospace`;
              ctx2D.textAlign = 'center';
              ctx2D.textBaseline = 'middle';
              ctx2D.fillText(num, chestPr.x, chestPr.y);
            }
          }

          // F. Articulated Arms, Sleeves & Forearms
          const lHandPr = project3D(p.x - rCos * 0.34 - fCos * armSwing, p.y - rSin * 0.34 - fSin * armSwing, 1.08, W, H);
          const rHandPr = project3D(p.x + rCos * 0.34 + fCos * armSwing, p.y + rSin * 0.34 + fSin * armSwing, 1.08, W, H);

          // Sleeves
          ctx2D.strokeStyle = isGK ? '#10b981' : (isHome ? '#991b1b' : '#f8fafc');
          ctx2D.lineWidth = Math.max(1.8, 3.0 * sc);
          if (lShoulderPr.visible && lHandPr.visible) {
            ctx2D.beginPath(); ctx2D.moveTo(lShoulderPr.x, lShoulderPr.y); ctx2D.lineTo((lShoulderPr.x + lHandPr.x) / 2, (lShoulderPr.y + lHandPr.y) / 2); ctx2D.stroke();
          }
          if (rShoulderPr.visible && rHandPr.visible) {
            ctx2D.beginPath(); ctx2D.moveTo(rShoulderPr.x, rShoulderPr.y); ctx2D.lineTo((rShoulderPr.x + rHandPr.x) / 2, (rShoulderPr.y + rHandPr.y) / 2); ctx2D.stroke();
          }

          // Forearm & Hands (Skin Tone)
          ctx2D.strokeStyle = '#fed7aa';
          ctx2D.lineWidth = Math.max(1.5, 2.4 * sc);
          if (lShoulderPr.visible && lHandPr.visible) {
            ctx2D.beginPath(); ctx2D.moveTo((lShoulderPr.x + lHandPr.x) / 2, (lShoulderPr.y + lHandPr.y) / 2); ctx2D.lineTo(lHandPr.x, lHandPr.y); ctx2D.stroke();
          }
          if (rShoulderPr.visible && rHandPr.visible) {
            ctx2D.beginPath(); ctx2D.moveTo((rShoulderPr.x + rHandPr.x) / 2, (rShoulderPr.y + rHandPr.y) / 2); ctx2D.lineTo(rHandPr.x, rHandPr.y); ctx2D.stroke();
          }

          // G. Neck & Head with Styled 3D Hair
          const headPr = project3D(p.x, p.y, 1.74, W, H);
          if (headPr.visible) {
            const headR = Math.max(2.2, 3.8 * sc);
            // Face
            ctx2D.fillStyle = '#fed7aa';
            ctx2D.beginPath();
            ctx2D.arc(headPr.x, headPr.y, headR, 0, Math.PI * 2);
            ctx2D.fill();

            // Hair Cap
            ctx2D.fillStyle = '#29180b';
            ctx2D.beginPath();
            ctx2D.arc(headPr.x, headPr.y - headR * 0.25, headR * 0.95, Math.PI * 0.85, Math.PI * 2.15);
            ctx2D.fill();
          }

          // H. Compact Circular Number Badge (Never Huge, Clean Broadcast Look)
          if (headPr.visible) {
            const bR = Math.min(8.0, Math.max(4.0, 4.5 * sc));
            const pillY = headPr.y - bR * 1.6;

            ctx2D.fillStyle = isHome ? 'rgba(220, 38, 38, 0.90)' : 'rgba(234, 179, 8, 0.90)';
            ctx2D.beginPath();
            ctx2D.arc(headPr.x, pillY, bR, 0, Math.PI * 2);
            ctx2D.fill();

            ctx2D.strokeStyle = 'rgba(255, 255, 255, 0.85)';
            ctx2D.lineWidth = 1.0;
            ctx2D.stroke();

            ctx2D.font = `bold ${Math.min(9, Math.max(6, Math.round(bR * 1.3)))}px 'JetBrains Mono', monospace`;
            ctx2D.fillStyle = '#ffffff';
            ctx2D.textAlign = 'center';
            ctx2D.textBaseline = 'middle';
            ctx2D.fillText(num, headPr.x, pillY + 0.5);
          }

        } else if (item.type === 'ball') {
          const bData = item.data;
          const bElev = bData.z || 0;
          const sPr = project3D(bData.x, bData.y, 0, W, H);
          const bPr = item.ball;
          if (!bPr.visible || bPr.depth <= 0) return;

          const sc = bPr.scale;
          const rad = Math.min(4.8, Math.max(1.8, 2.8 * sc));

          // Ball Ground Drop Shadow
          if (sPr.visible) {
            const sAlpha = Math.max(0.12, 0.60 - (bElev * 0.08));
            const sScale = Math.max(0.4, 1.0 - (bElev * 0.07));
            ctx2D.fillStyle = `rgba(0, 0, 0, ${sAlpha})`;
            ctx2D.beginPath();
            ctx2D.ellipse(sPr.x, sPr.y, rad * 1.35 * sScale, rad * 0.60 * sScale, 0, 0, Math.PI * 2);
            ctx2D.fill();

            // Altitude Tether
            if (bElev > 0.4) {
              ctx2D.strokeStyle = 'rgba(255, 255, 255, 0.45)';
              ctx2D.lineWidth = 1;
              ctx2D.setLineDash([2, 2]);
              ctx2D.beginPath();
              ctx2D.moveTo(sPr.x, sPr.y);
              ctx2D.lineTo(bPr.x, bPr.y);
              ctx2D.stroke();
              ctx2D.setLineDash([]);
            }
          }

          // Kinetic Shot Halo / Fireball (>75 km/h)
          if ((bData.speed_kmh || 0) > 75) {
            ctx2D.fillStyle = 'rgba(239, 68, 68, 0.4)';
            ctx2D.beginPath();
            ctx2D.arc(bPr.x, bPr.y, rad + 5 * sc, 0, Math.PI * 2);
            ctx2D.fill();

            ctx2D.strokeStyle = '#ef4444';
            ctx2D.lineWidth = 2.0;
            ctx2D.beginPath();
            ctx2D.arc(bPr.x, bPr.y, rad + 6 * sc, 0, Math.PI * 2);
            ctx2D.stroke();
          }

          // 3D Sphere Shading
          const ballGrad = ctx2D.createRadialGradient(
            bPr.x - rad * 0.35, bPr.y - rad * 0.35, rad * 0.1,
            bPr.x, bPr.y, rad
          );
          ballGrad.addColorStop(0, '#ffffff');
          ballGrad.addColorStop(0.7, '#f1f5f9');
          ballGrad.addColorStop(1, '#94a3b8');
          ctx2D.fillStyle = ballGrad;
          ctx2D.beginPath();
          ctx2D.arc(bPr.x, bPr.y, rad, 0, Math.PI * 2);
          ctx2D.fill();

          ctx2D.strokeStyle = '#0f172a';
          ctx2D.lineWidth = 1.0;
          ctx2D.stroke();

          // Authentic Telstar Black Pentagons
          ctx2D.fillStyle = '#0f172a';
          ctx2D.beginPath();
          ctx2D.arc(bPr.x, bPr.y, rad * 0.32, 0, Math.PI * 2);
          ctx2D.fill();

          ctx2D.beginPath();
          ctx2D.arc(bPr.x - rad * 0.52, bPr.y - rad * 0.38, rad * 0.20, 0, Math.PI * 2);
          ctx2D.arc(bPr.x + rad * 0.52, bPr.y - rad * 0.34, rad * 0.20, 0, Math.PI * 2);
          ctx2D.arc(bPr.x, bPr.y + rad * 0.58, rad * 0.20, 0, Math.PI * 2);
          ctx2D.fill();
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
        // Action Visuals: Sliding Tackle & Foul Fall & Shooting Kick
        const action = p.action || "NORMAL";
        if (action === "SLIDING_TACKLE") {
          // Slide streak dust on pitch
          ctx2D.fillStyle = "rgba(255, 255, 255, 0.4)";
          ctx2D.beginPath();
          ctx2D.ellipse(sx - 12, sy + 4, 14, 4, -0.2, 0, Math.PI * 2);
          ctx2D.fill();
          // Lowered body and extended sliding leg
          ctx2D.strokeStyle = kitSec;
          ctx2D.lineWidth = 4;
          ctx2D.beginPath();
          ctx2D.moveTo(sx - 6, sy + 3);
          ctx2D.lineTo(sx + 15, sy + 6); // Slide lead leg
          ctx2D.stroke();
        } else if (action === "FOUL_FALL") {
          // Tumbled fallen pose
          ctx2D.strokeStyle = "rgba(239, 68, 68, 0.8)";
          ctx2D.lineWidth = 2;
          ctx2D.beginPath();
          ctx2D.arc(sx, sy, 11, 0, Math.PI * 2);
          ctx2D.stroke();
        } else if (action === "SHOOTING_KICK") {
          // Kicking leg follow-through
          ctx2D.strokeStyle = "#ffffff";
          ctx2D.lineWidth = 3.5;
          ctx2D.beginPath();
          ctx2D.moveTo(sx, sy);
          ctx2D.lineTo(sx + 8, sy - 4);
          ctx2D.stroke();
        }

        ctx2D.fillText(num, sx, sy + 0.5);

        // Player Name Pill below/above kit
        ctx2D.font = "bold 9px 'JetBrains Mono', monospace";
        const textW = ctx2D.measureText(name).width;
        const pillY = (action === "SLIDING_TACKLE") ? sy - 18 : sy - 14;

        ctx2D.fillStyle = (action === "SLIDING_TACKLE") ? "rgba(239, 68, 68, 0.9)" : "rgba(15, 23, 42, 0.85)";
        ctx2D.beginPath();
        ctx2D.roundRect(sx - textW / 2 - 4, pillY - 7, textW + 8, 13, 3);
        ctx2D.fill();

        ctx2D.strokeStyle = "rgba(255, 255, 255, 0.25)";
        ctx2D.lineWidth = 0.8;
        ctx2D.stroke();

        ctx2D.fillStyle = "#ffffff";
        ctx2D.textBaseline = "middle";
        ctx2D.fillText((action === "SLIDING_TACKLE" ? "⚡ " + name : name), sx, pillY - 0.5);
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

      // Dynamic Smooth Camera Tracking for active preset modes
      if (currentCamPreset === 'action') {
        camTargetX += (f.ball.x - camTargetX) * 0.18;
        if (threeInitialized && camera && controls) {
          camera.position.x += (f.ball.x - camera.position.x) * 0.18;
          camera.position.y = 118.0;
          camera.position.z = 36.0;
          controls.target.x = camera.position.x;
          controls.target.y = 34.0;
          controls.target.z = 1.0;
        }
      } else if (currentCamPreset === 'pro') {
        const p = getActiveBallPlayer(f);
        if (p) {
          const spd = Math.hypot(p.vx || 0, p.vy || 0);
          const fac = (spd > 0.3) ? Math.atan2(p.vy, p.vx) : (p.team === 'Home' ? 0 : Math.PI);
          const fc = Math.cos(fac), fs = Math.sin(fac);
          camTargetX += (p.x + fc * 12 - camTargetX) * 0.22;
          camTargetY += (p.y + fs * 12 - camTargetY) * 0.22;
          camYaw = fac - Math.PI / 2;
          if (threeInitialized && camera && controls) {
            const tx = p.x - fc * 6.5, ty = p.y - fs * 6.5;
            camera.position.x += (tx - camera.position.x) * 0.22;
            camera.position.y += (ty - camera.position.y) * 0.22;
            camera.position.z = Math.max(2.2, (p.z || 0) + 2.8);
            controls.target.x += (p.x + fc * 12 - controls.target.x) * 0.22;
            controls.target.y += (p.y + fs * 12 - controls.target.y) * 0.22;
            controls.target.z = 1.2;
          }
        }
      } else if (currentCamPreset === 'duel') {
        const { p1, p2 } = getDuelPlayers(f);
        if (p1 && p2) {
          const mx = (p1.x + p2.x) / 2, my = (p1.y + p2.y) / 2;
          let duelAngle = Math.atan2(p2.y - p1.y, p2.x - p1.x) - Math.PI / 2;
          camTargetX += (mx - camTargetX) * 0.20;
          camTargetY += (my - camTargetY) * 0.20;
          if (threeInitialized && camera && controls) {
            const tx = mx + Math.cos(duelAngle) * 8.5;
            const ty = my + Math.sin(duelAngle) * 8.5;
            camera.position.x += (tx - camera.position.x) * 0.20;
            camera.position.y += (ty - camera.position.y) * 0.20;
            camera.position.z = 3.2;
            controls.target.x += (mx - controls.target.x) * 0.20;
            controls.target.y += (my - controls.target.y) * 0.20;
            controls.target.z = 1.2;
          }
        }
      } else if (currentCamPreset === 'dugout') {
        camTargetX += (f.ball.x - camTargetX) * 0.18;
        if (threeInitialized && camera && controls) {
          camera.position.x += (f.ball.x - camera.position.x) * 0.18;
          camera.position.y = -6.0;
          camera.position.z = 2.2;
          controls.target.x = camera.position.x;
          controls.target.y = 34.0;
          controls.target.z = 1.2;
        }
      }

      // Update 3D Positions & Biomechanical Poses if Three.js WebGL is running
      if (threeInitialized) {
        const ballPos = new THREE.Vector3(f.ball.x, f.ball.y, Math.max(0.28, f.ball.z || 0));

        f.players.forEach(p => {
          const mesh = getOrCreatePlayerMesh(p.id, p.team, p);
          if (mesh) {
            mesh.position.set(p.x, p.y, p.z || 0);

            // Orient Player Body toward ball or movement direction (Realistic Look)
            const vx = p.vx || 0;
            const vy = p.vy || 0;
            const speed = Math.sqrt(vx * vx + vy * vy);

            let targetYaw = 0;
            if (speed > 0.4) {
              targetYaw = Math.atan2(vy, vx);
            } else {
              targetYaw = Math.atan2(f.ball.y - p.y, f.ball.x - p.x);
            }
            mesh.rotation.z = targetYaw - Math.PI / 2;

            // Biomechanical Animations (Running Stride vs Sliding Tackle vs Falling)
            const action = p.action || "NORMAL";
            if (action === "SLIDING_TACKLE") {
              // Sliding tackle: body lowers, leans backwards, lead leg extends straight out
              mesh.position.z = -0.22;
              mesh.rotation.x = -Math.PI / 3.2; // Slanted slide
              if (mesh.userData && mesh.userData.leftLeg && mesh.userData.rightLeg) {
                mesh.userData.leftLeg.rotation.x = Math.PI / 2.2; // Slide leg forward
                mesh.userData.rightLeg.rotation.x = -Math.PI / 4.0; // Trailing bent leg
              }
            } else if (action === "FOUL_FALL") {
              // Player tripped/tackled: tumbling fall
              mesh.position.z = -0.15;
              mesh.rotation.y = Math.PI / 3.0; // Stumble tilt
              mesh.rotation.x = Math.PI / 4.0;
              if (mesh.userData && mesh.userData.leftLeg && mesh.userData.rightLeg) {
                mesh.userData.leftLeg.rotation.x = -0.8;
                mesh.userData.rightLeg.rotation.x = 0.5;
              }
            } else if (action === "SHOOTING_KICK") {
              // Powerful strike follow-through pose
              mesh.position.z = 0.0;
              mesh.rotation.x = -0.15;
              mesh.rotation.y = 0;
              if (mesh.userData && mesh.userData.leftLeg && mesh.userData.rightLeg) {
                mesh.userData.rightLeg.rotation.x = 1.05; // Kicking right leg forward
                mesh.userData.leftLeg.rotation.x = -0.45; // Planted left leg back
              }
            } else {
              // Normal upright stance and running stride
              mesh.rotation.x = 0;
              mesh.rotation.y = 0;
              const legSwing = (speed > 0.3) ? Math.sin(frameIdx * 0.45 + (p.num || 1)) * 0.55 : 0;
              if (mesh.userData && mesh.userData.leftLeg && mesh.userData.rightLeg) {
                mesh.userData.leftLeg.rotation.x = legSwing;
                mesh.userData.rightLeg.rotation.x = -legSwing;
              }
            }

            // In Be-A-Pro mode, hide floating tag of active player directly ahead of camera
            if (mesh.userData && mesh.userData.nameSprite) {
              const activeP = (currentCamPreset === 'pro') ? getActiveBallPlayer(f) : null;
              mesh.userData.nameSprite.visible = !(activeP && (activeP.id === p.id || activeP.name === p.name));
            }
          }
        });

        if (ballMesh && ballShadow) {
          const bz = Math.max(0.28, f.ball.z || 0);
          ballMesh.position.copy(ballPos);
          ballShadow.position.set(f.ball.x, f.ball.y, 0.03);
          ballShadow.scale.setScalar(Math.max(0.4, 1.0 - (bz * 0.08)));
        }

        // Dynamic 3D Camera Tracking for Active Presets
        if (camera && controls) {
          if (currentCamPreset === 'pro') {
            const p = getActiveBallPlayer(f) || { x: f.ball.x, y: f.ball.y, vx: 1, vy: 0, team: 'Home' };
            const spd = Math.hypot(p.vx || 0, p.vy || 0);
            const fac = (spd > 0.3) ? Math.atan2(p.vy, p.vx) : (p.team === 'Home' ? 0 : Math.PI);
            const fc = Math.cos(fac), fs = Math.sin(fac);
            const camX = p.x - fc * 5.5;
            const camY = p.y - fs * 5.5;
            const camZ = 2.0;
            const tgtX = p.x + fc * 10.0;
            const tgtY = p.y + fs * 10.0;
            const tgtZ = 1.2;
            if (isPlaying) {
              camera.position.lerp(new THREE.Vector3(camX, camY, camZ), 0.2);
              controls.target.lerp(new THREE.Vector3(tgtX, tgtY, tgtZ), 0.2);
            } else {
              camera.position.set(camX, camY, camZ);
              controls.target.set(tgtX, tgtY, tgtZ);
            }
            controls.update();
          } else if (currentCamPreset === 'duel') {
            const { p1, p2 } = getDuelPlayers(f);
            const mx = (p1 && p2) ? (p1.x + p2.x) / 2 : f.ball.x;
            const my = (p1 && p2) ? (p1.y + p2.y) / 2 : f.ball.y;
            let duelAngle = 0;
            if (p1 && p2) {
              duelAngle = Math.atan2(p2.y - p1.y, p2.x - p1.x) - Math.PI / 2;
            }
            const camX = mx + Math.cos(duelAngle) * 7.5;
            const camY = my + Math.sin(duelAngle) * 7.5;
            const camZ = 2.2;
            if (isPlaying) {
              camera.position.lerp(new THREE.Vector3(camX, camY, camZ), 0.2);
              controls.target.lerp(new THREE.Vector3(mx, my, 1.1), 0.2);
            } else {
              camera.position.set(camX, camY, camZ);
              controls.target.set(mx, my, 1.1);
            }
            controls.update();
          } else if (currentCamPreset === 'action') {
            const camX = f.ball.x;
            if (isPlaying) {
              camera.position.x += (camX - camera.position.x) * 0.15;
              controls.target.x += (camX - controls.target.x) * 0.15;
            } else {
              camera.position.set(camX, -16, 9.0);
              controls.target.set(camX, 34, 1.5);
            }
            controls.update();
          } else if (currentCamPreset === 'dugout') {
            const camX = f.ball.x;
            if (isPlaying) {
              camera.position.x += (camX - camera.position.x) * 0.15;
              controls.target.x += (camX - controls.target.x) * 0.15;
            } else {
              camera.position.set(camX, -1.8, 1.4);
              controls.target.set(camX, 34, 1.0);
            }
            controls.update();
          }
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

        // Populate and display Goal Popup Celebration Modal with Goalmouth Coordinates & Target Dot
        if (goalModal) {
          document.getElementById('popup-scorer-name').textContent = activeGoal.scorer.toUpperCase();
          document.getElementById('popup-minute-badge').textContent = `${activeGoal.minute}'`;
          document.getElementById('popup-type-stat').textContent = activeGoal.type;
          document.getElementById('popup-speed-stat').textContent = `${activeGoal.speed_kmh} km/h`;

          // Assist & GK facing details
          const assistEl = document.getElementById('popup-assist-name');
          if (assistEl) assistEl.textContent = activeGoal.assist || "Solo Effort";
          const gkEl = document.getElementById('popup-gk-name');
          if (gkEl) gkEl.textContent = activeGoal.goalkeeper || "Kiper Lawan";

          // Calculate Dot Position inside the 240x90 Goal Post Net Diagram
          // Pitch y for goal is 30.34m to 37.66m (span = 7.32m). In diagram: 0% is left post, 100% is right post.
          const gY = (activeGoal.entry_y !== undefined) ? activeGoal.entry_y : 34.0;
          const gZ = (activeGoal.entry_z !== undefined) ? activeGoal.entry_z : 1.0;
          const normY = Math.max(0.05, Math.min(0.95, (gY - 30.34) / 7.32));
          // Height: 0m ground (bottom 90%) to 2.44m crossbar (top 10%)
          const normZ = Math.max(0.08, Math.min(0.92, 1.0 - (gZ / 2.44)));

          const targetDot = document.getElementById('goal-target-dot');
          if (targetDot) {
            targetDot.style.left = `${(normY * 100).toFixed(1)}%`;
            targetDot.style.top = `${(normZ * 100).toFixed(1)}%`;
          }

          const targetDesc = document.getElementById('popup-target-desc');
          if (targetDesc) {
            const sideDesc = activeGoal.zone_label || (normY < 0.35 ? "Sisi Kiri Gawang (Left)" : (normY > 0.65 ? "Sisi Kanan Gawang (Right)" : "Tengah Gawang (Center)"));
            targetDesc.textContent = `🎯 ${sideDesc} · Ketinggian: ${gZ.toFixed(2)}m · Entry (${activeGoal.entry_x || 105}m, ${gY.toFixed(1)}m)`;
          }

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

      // Dynamic Foul / Hard Sliding Tackle Banner Alert
      const foulBanner = document.getElementById('foul-alert-banner');
      let activeFoul = null;
      if (currentMetadata && currentMetadata.fouls) {
        currentMetadata.fouls.forEach(foul => {
          const fSec = foul.minute * 60 + (foul.second || 0);
          if (Math.abs(totalSec - fSec) <= 12) {
            activeFoul = foul;
          }
        });
      }
      if (foulBanner) {
        if (activeFoul) {
          foulBanner.style.display = 'inline-flex';
          const cardEmoji = activeFoul.card === 'Red Card' ? '🟥' : '🟨';
          document.getElementById('foul-alert-text').textContent =
            `${cardEmoji} FOUL (${activeFoul.minute}')! ${activeFoul.tackler} · ${activeFoul.action} (${activeFoul.card || 'Card'})`;
        } else {
          foulBanner.style.display = 'none';
        }
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
            const w = window.innerWidth;
            const h = window.innerHeight;
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

    // Player and Tactical Target Resolvers for Dynamic Video Game Cameras
    function getActiveBallPlayer(f) {
      if (!f || !f.players || f.players.length === 0) return null;
      const poss = f.possession;
      if (poss && poss.possessing_player) {
        const p = f.players.find(x => x.name === poss.possessing_player || x.id === poss.possessing_player);
        if (p) return p;
      }
      let bestP = f.players[0], minDist = 999;
      f.players.forEach(p => {
        const d = Math.hypot(p.x - f.ball.x, p.y - f.ball.y);
        if (d < minDist) { minDist = d; bestP = p; }
      });
      return bestP;
    }

    function getDuelPlayers(f) {
      const p1 = getActiveBallPlayer(f);
      if (!p1 || !f.players) return { p1: null, p2: null };
      let p2 = null, minDist = 999;
      f.players.forEach(other => {
        if (other.team !== p1.team) {
          const d = Math.hypot(other.x - p1.x, other.y - p1.y);
          if (d < minDist) { minDist = d; p2 = other; }
        }
      });
      return { p1, p2: p2 || p1 };
    }

    function toggleHUD() {
      const hud = document.getElementById('hud-container');
      if (hud) hud.classList.toggle('hidden');
    }

    function toggleBrowserFullscreen() {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => console.log(err));
      } else {
        document.exitFullscreen().catch(err => console.log(err));
      }
    }

    // 3D Camera Angles Preset Controller (Calibrated Low Pitch Elevation)
    function setCameraPreset(mode) {
      currentCamPreset = mode;
      if (activeView !== '3d') switchView('3d');

      const btns = document.querySelectorAll('.cam-btn');
      btns.forEach(b => {
        const clk = b.getAttribute('onclick') || '';
        if (clk.includes(`'${mode}'`) || clk.includes(`"${mode}"`)) b.classList.add('active');
        else b.classList.remove('active');
      });

      if (window.history && window.history.replaceState) {
        try {
          const u = new URL(window.location.href);
          u.searchParams.set('cam', mode);
          window.history.replaceState(null, '', u.toString());
        } catch (e) {}
      }

      const f = matchData[currentFrame - 1];
      const bx = f ? f.ball.x : 52.5;
      const by = f ? f.ball.y : 34.0;

      if (mode === 'broadcast') {
        // Authentic TV Broadcast View (Grandstand TV perspective, ground at bottom, never hanging)
        orbitYaw = 0.0;
        orbitPitch = 0.44; // ~25° elevation
        orbitDist = 84.0;
        camTargetX = 52.5;
        camTargetY = 34.0;
        camTargetZ = 0.0;
        camFov = 42.0;
        updateCameraPositionFromOrbit();
        if (threeInitialized && camera && controls) {
          camera.fov = 40;
          camera.updateProjectionMatrix();
          camera.position.set(52.5, 118.0, 36.0);
          controls.target.set(52.5, 34.0, 1.0);
          controls.update();
        }
      } else if (mode === 'pro') {
        // Single Player (Be-A-Pro / 3rd Person over-the-shoulder tracking)
        const p = getActiveBallPlayer(f) || { x: bx, y: by, vx: 1, vy: 0, team: 'Home' };
        const spd = Math.hypot(p.vx || 0, p.vy || 0);
        const fac = (spd > 0.3) ? Math.atan2(p.vy, p.vx) : (p.team === 'Home' ? 0 : Math.PI);
        const fc = Math.cos(fac), fs = Math.sin(fac);
        camPosX = p.x - fc * 8.5;
        camPosY = p.y - fs * 8.5;
        camPosZ = 3.6;
        camTargetX = p.x + fc * 14;
        camTargetY = p.y + fs * 14;
        camTargetZ = 1.2;
        camFov = 52.0;
        if (threeInitialized && camera && controls) {
          camera.fov = 52;
          camera.updateProjectionMatrix();
          camera.position.set(camPosX, camPosY, camPosZ);
          controls.target.set(camTargetX, camTargetY, camTargetZ);
          controls.update();
        }
      } else if (mode === 'duel') {
        // 2-Player Duel (1v1 Clash tight cinematic framing)
        const { p1, p2 } = getDuelPlayers(f);
        const mx = (p1 && p2) ? (p1.x + p2.x) / 2 : bx;
        const my = (p1 && p2) ? (p1.y + p2.y) / 2 : by;
        let duelAngle = 0;
        if (p1 && p2) {
          duelAngle = Math.atan2(p2.y - p1.y, p2.x - p1.x) - Math.PI / 2;
        }
        camPosX = mx + Math.cos(duelAngle) * 9.5;
        camPosY = my + Math.sin(duelAngle) * 9.5;
        camPosZ = 4.0;
        camTargetX = mx;
        camTargetY = my;
        camTargetZ = 1.0;
        camFov = 50.0;
        if (threeInitialized && camera && controls) {
          camera.fov = 50;
          camera.updateProjectionMatrix();
          camera.position.set(camPosX, camPosY, camPosZ);
          controls.target.set(camTargetX, camTargetY, camTargetZ);
          controls.update();
        }
      } else if (mode === 'action') {
        // Dynamic Follow Ball (Sideline gliding with possession at TV height)
        camTargetX = bx;
        camTargetY = 34.0;
        camTargetZ = 0.0;
        camPosX = bx;
        camPosY = -48.0;
        camPosZ = 38.0;
        camFov = 42.0;
        if (threeInitialized && camera && controls) {
          camera.fov = 40;
          camera.updateProjectionMatrix();
          camera.position.set(bx, 118.0, 36.0);
          controls.target.set(bx, 34.0, 1.0);
          controls.update();
        }
      } else if (mode === 'goal') {
        // Behind Goal (Endzone TV camera looking forward through posts, ground strictly at bottom)
        camPosX = -14.0;
        camPosY = 34.0;
        camPosZ = 5.5;
        camTargetX = 52.5;
        camTargetY = 34.0;
        camTargetZ = 1.2;
        camFov = 48.0;
        if (threeInitialized && camera && controls) {
          camera.fov = 48;
          camera.updateProjectionMatrix();
          camera.position.set(-14.0, 34.0, 5.5);
          controls.target.set(52.5, 34.0, 1.2);
          controls.update();
        }
      } else if (mode === 'dugout') {
        // Sideline Pitch-Level Dugout (Manager eye level)
        camPosX = bx;
        camPosY = -6.0;
        camPosZ = 2.4;
        camTargetX = bx;
        camTargetY = 34.0;
        camTargetZ = 1.2;
        camFov = 52.0;
        if (threeInitialized && camera && controls) {
          camera.fov = 52;
          camera.updateProjectionMatrix();
          camera.position.set(bx, -6.0, 2.4);
          controls.target.set(bx, 34.0, 1.2);
          controls.update();
        }
      } else if (mode === 'top') {
        camYaw = 0.0;
        camPitch = 1.48;
        camDist = 95.0;
        camTargetX = 52.5;
        camTargetY = 34.0;
        camFovMult = 1.4;
        camOffsetY = 0.0;
        if (threeInitialized && camera && controls) {
          camera.fov = 45;
          camera.updateProjectionMatrix();
          camera.position.set(52.5, 34, 95);
          controls.target.set(52.5, 34, 0);
          controls.update();
        }
      }

      if (threeInitialized && renderer && scene && camera) {
        renderer.render(scene, camera);
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

          // Clear previous match player 3D meshes from Three.js scene
          if (threeInitialized && scene) {
            Object.keys(playerMeshes).forEach(pid => {
              scene.remove(playerMeshes[pid]);
              delete playerMeshes[pid];
            });
          }

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

    // Default to 3D Stadium and parse URL camera preset if present
    switchView('3d');
    const urlParams = new URLSearchParams(window.location.search);
    const initialCam = urlParams.get('cam') || 'broadcast';
    setCameraPreset(initialCam);

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
    // Open Goalkeeper Analytics & Conceded Heatmap Modal
    function openGkAnalyticsModal() {
      const modal = document.getElementById('gk-analytics-modal-overlay');
      if (!modal) return;

      const gkContainer = document.getElementById('gk-cards-container');
      const tableBody = document.getElementById('goals-history-tbody');
      if (!currentMetadata) return;

      // 1. Render Goalkeeper Conceded Cards & Quadrant Heatmaps
      const gks = currentMetadata.goalkeepers || [];
      if (gkContainer) {
        if (gks.length === 0) {
          gkContainer.innerHTML = `<div style="color: #94a3b8; font-size: 0.85rem;">Belum ada gol yang bersarang ke gawang kiper pada pertandingan ini.</div>`;
        } else {
          gkContainer.innerHTML = gks.map(gk => {
            const z = gk.zones || {};
            const tl = z["TL"] || 0;
            const tc = z["TC"] || 0;
            const tr = z["TR"] || 0;
            const bl = z["BL"] || 0;
            const bc = z["BC"] || 0;
            const br = z["BR"] || 0;

            const getHeatClass = (cnt) => {
              if (cnt === 0) return 'heat-0';
              if (cnt === 1) return 'heat-1';
              if (cnt === 2) return 'heat-2';
              return 'heat-3';
            };

            return `
              <div class="gk-card">
                <div class="gk-name-badge">
                  <span>🧤 ${gk.name}</span>
                  <span style="color: #f87171; font-family: 'JetBrains Mono';">${gk.total_conceded} Kebobolan</span>
                </div>
                <div style="font-size: 0.72rem; color: #94a3b8; margin-bottom: 6px;">
                  Distribusi Sisi Gawang Yang Paling Sering Kebobolan:
                </div>
                <div class="gk-net-heatmap">
                  <div class="gk-heat-cell ${getHeatClass(tl)}">
                    <span>ATAS KIRI</span>
                    <span style="font-size: 0.95rem;">${tl}</span>
                  </div>
                  <div class="gk-heat-cell ${getHeatClass(tc)}">
                    <span>ATAS TENGAH</span>
                    <span style="font-size: 0.95rem;">${tc}</span>
                  </div>
                  <div class="gk-heat-cell ${getHeatClass(tr)}">
                    <span>ATAS KANAN</span>
                    <span style="font-size: 0.95rem;">${tr}</span>
                  </div>
                  <div class="gk-heat-cell ${getHeatClass(bl)}">
                    <span>BAWAH KIRI</span>
                    <span style="font-size: 0.95rem;">${bl}</span>
                  </div>
                  <div class="gk-heat-cell ${getHeatClass(bc)}">
                    <span>BAWAH TENGAH</span>
                    <span style="font-size: 0.95rem;">${bc}</span>
                  </div>
                  <div class="gk-heat-cell ${getHeatClass(br)}">
                    <span>BAWAH KANAN</span>
                    <span style="font-size: 0.95rem;">${br}</span>
                  </div>
                </div>
              </div>
            `;
          }).join('');
        }
      }

      // 2. Render Historical Goals & Assists Table
      const goals = currentMetadata.goals || [];
      if (tableBody) {
        if (goals.length === 0) {
          tableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #94a3b8;">Belum ada data gol.</td></tr>`;
        } else {
          tableBody.innerHTML = goals.map(g => {
            const teamBadge = g.team === 'Home' 
              ? `<span style="color: var(--home); font-weight: 800;">${currentMetadata.home_team?.short || 'HOME'}</span>` 
              : `<span style="color: var(--away); font-weight: 800;">${currentMetadata.away_team?.short || 'AWAY'}</span>`;
            return `
              <tr>
                <td style="font-weight: 800; color: #fbbf24;">${g.minute}'</td>
                <td style="font-weight: 700; color: #ffffff;">⚽ ${g.scorer}</td>
                <td style="color: #60a5fa;">🅰️ ${g.assist || 'Solo Effort'}</td>
                <td>${teamBadge}</td>
                <td style="color: #f87171;">🧤 ${g.goalkeeper || '-'}</td>
                <td style="color: #34d399;">🎯 ${g.zone_label || g.type} (${g.entry_z || 1.0}m)</td>
                <td style="color: #f59e0b;">⚡ ${g.speed_kmh} km/h</td>
              </tr>
            `;
          }).join('');
        }
      }

      modal.style.display = 'flex';
    }
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
