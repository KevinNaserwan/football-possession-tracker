import json
import math
import random

def generate_multi_minute_match(num_frames: int = 1500) -> dict:
    """
    Generates realistic, long-form continuous football tracking sequences (1,500 frames / 60 seconds of continuous multi-phase play):
    Phase 1 (Frames 1-350): Home Goalkeeper buildup -> short pass to CB -> progressive wing pass to RM
    Phase 2 (Frames 351-600): Midfield duel & high press from Away DM -> loose ball scramble
    Phase 3 (Frames 601-950): Turnover -> Away rapid counter-attack down the right flank -> aerial cross
    Phase 4 (Frames 951-1250): Defensive interception by Home CB -> second-phase transition
    Phase 5 (Frames 1251-1500): Long-range shot towards goal with realistic 3D parabolic trajectory, ball elevation (Z), and shot speed (km/h)
    """
    frames = []

    # Standard 4-3-3 Home setup
    home_bases = {
        "H1": (5.0, 34.0, "GK"),
        "H2": (22.0, 10.0, "RB"),
        "H3": (18.0, 26.0, "CB"),
        "H4": (18.0, 42.0, "CB"),
        "H5": (22.0, 58.0, "LB"),
        "H6": (36.0, 34.0, "DM"),
        "H7": (50.0, 14.0, "RW"),
        "H8": (45.0, 26.0, "CM"),
        "H9": (45.0, 42.0, "CM"),
        "H10": (52.0, 34.0, "ST"),
        "H11": (50.0, 54.0, "LW"),
    }

    # Standard 4-2-3-1 Away setup
    away_bases = {
        "A1": (100.0, 34.0, "GK"),
        "A2": (83.0, 10.0, "LB"),
        "A3": (86.0, 26.0, "CB"),
        "A4": (86.0, 42.0, "CB"),
        "A5": (83.0, 58.0, "RB"),
        "A6": (68.0, 28.0, "DM"),
        "A7": (68.0, 40.0, "DM"),
        "A8": (56.0, 34.0, "AM"),
        "A9": (56.0, 12.0, "LM"),
        "A10": (56.0, 56.0, "RM"),
        "A11": (53.0, 34.0, "ST"),
    }

    last_bx, last_by, last_bz = 5.0, 34.0, 0.0

    for f_idx in range(1, num_frames + 1):
        t = f_idx * 0.04 # 25 FPS interval

        # Ball trajectory & 3D Z elevation across continuous phases
        if f_idx <= 200:
            # Phase 1: Goalkeeper to CB
            alpha = f_idx / 200.0
            bx = 5.0 + alpha * 13.0
            by = 34.0 - alpha * 8.0
            bz = 0.0
        elif f_idx <= 450:
            # CB to RW wing pass
            alpha = (f_idx - 200) / 250.0
            bx = 18.0 + alpha * 32.0
            by = 26.0 - alpha * 12.0
            bz = math.sin(alpha * math.pi) * 2.2 # Slight ground-hop/low trajectory
        elif f_idx <= 650:
            # Midfield scramble & high press
            alpha = (f_idx - 450) / 200.0
            bx = 50.0 + math.sin(alpha * 4 * math.pi) * 3.5
            by = 14.0 + alpha * 16.0
            bz = 0.0
        elif f_idx <= 900:
            # Away turnover & fast break
            alpha = (f_idx - 650) / 250.0
            bx = 52.0 + alpha * 28.0
            by = 30.0 + alpha * 22.0
            bz = 0.0
        elif f_idx <= 1100:
            # Aerial cross towards box (high parabolic arc)
            alpha = (f_idx - 900) / 200.0
            bx = 80.0 - alpha * 15.0
            by = 52.0 - alpha * 18.0
            bz = math.sin(alpha * math.pi) * 6.8 # High 3D cross (6.8 meters peak height!)
        elif f_idx <= 1300:
            # Header duel & Home interception
            alpha = (f_idx - 1100) / 200.0
            bx = 65.0 - alpha * 20.0
            by = 34.0 + math.sin(t * 2) * 2.0
            bz = max(0.0, math.sin(alpha * math.pi) * 1.5)
        else:
            # Powerful long-range strike towards goal (Shot speed > 100 km/h)
            alpha = (f_idx - 1300) / 200.0
            bx = 45.0 + alpha * 53.0
            by = 34.0 + (alpha * 0.5)
            bz = math.sin(alpha * math.pi) * 4.2 # Curving ball flight into top corner

        # Compute ball 3D velocities & shot power in km/h
        b_vx = (bx - last_bx) / 0.04
        b_vy = (by - last_by) / 0.04
        b_vz = (bz - last_bz) / 0.04
        speed_mps = math.sqrt(b_vx**2 + b_vy**2 + b_vz**2)
        shot_power_kmh = round(speed_mps * 3.6, 1)

        last_bx, last_by, last_bz = bx, by, bz

        # Player movements dynamically reacting to ball position
        players = []
        for pid, (base_x, base_y, role) in home_bases.items():
            # Shift towards ball with role-based constraints
            pull_factor = 0.35 if "M" in role or "W" in role else 0.15
            px = base_x + (bx - base_x) * pull_factor + math.sin(t + base_x) * 0.5
            py = base_y + (by - base_y) * pull_factor + math.cos(t + base_y) * 0.5
            
            # Distance to ball
            dist_ball = math.sqrt((px - bx)**2 + (py - by)**2)
            p_vx = (bx - px) * 0.2 if dist_ball < 6.0 else math.sin(t) * 0.8
            p_vy = (by - py) * 0.2 if dist_ball < 6.0 else math.cos(t) * 0.8

            players.append({
                "id": pid,
                "team": "Home",
                "x": round(px, 2),
                "y": round(py, 2),
                "z": 0.0,
                "vx": round(p_vx, 2),
                "vy": round(p_vy, 2)
            })

        for pid, (base_x, base_y, role) in away_bases.items():
            pull_factor = 0.38 if "M" in role or "S" in role else 0.18
            px = base_x + (bx - base_x) * pull_factor + math.cos(t + base_x) * 0.5
            py = base_y + (by - base_y) * pull_factor + math.sin(t + base_y) * 0.5
            
            dist_ball = math.sqrt((px - bx)**2 + (py - by)**2)
            p_vx = (bx - px) * 0.25 if dist_ball < 6.0 else -math.cos(t) * 0.8
            p_vy = (by - py) * 0.25 if dist_ball < 6.0 else -math.sin(t) * 0.8

            players.append({
                "id": pid,
                "team": "Away",
                "x": round(px, 2),
                "y": round(py, 2),
                "z": 0.0,
                "vx": round(p_vx, 2),
                "vy": round(p_vy, 2)
            })

        # Match clock formatted as MM:SS (e.g. 14:22, 14:23...)
        match_seconds = int(840 + t) # Starting from 14th minute of match
        mm = match_seconds // 60
        ss = match_seconds % 60
        clock_str = f"{mm:02d}:{ss:02d}"

        frames.append({
            "frame_id": f_idx,
            "match_time": clock_str,
            "ball": {
                "x": round(bx, 2),
                "y": round(by, 2),
                "z": round(bz, 2),
                "vx": round(b_vx, 2),
                "vy": round(b_vy, 2),
                "vz": round(b_vz, 2),
                "speed_kmh": shot_power_kmh,
                "in_play": True
            },
            "players": players
        })

    return {"match_id": "BARCA_METRICA_OFFICIAL_MATCH_01", "frames": frames}

if __name__ == "__main__":
    data = generate_multi_minute_match(1500)
    with open("data/sample_match_tracking.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Generated {len(data['frames'])} long-form frames with 3D Z-elevation in data/sample_match_tracking.json")
