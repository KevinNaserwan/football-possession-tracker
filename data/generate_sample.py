import json
import math

def generate_sample_match(num_frames: int = 100) -> dict:
    """
    Generates a realistic 100-frame synthetic match sequence
    with Home buildup, pass to midfield, turnover, and Away counter-attack.
    """
    frames = []
    
    # 11 Home players starting in defensive half (30m - 50m)
    # 11 Away players starting in defending their half (55m - 80m)
    home_bases = [
        ("H1", 5.0, 34.0),   # GK
        ("H2", 20.0, 12.0),  # RB
        ("H3", 18.0, 26.0),  # CB
        ("H4", 18.0, 42.0),  # CB
        ("H5", 20.0, 56.0),  # LB
        ("H6", 35.0, 34.0),  # DM
        ("H7", 45.0, 18.0),  # RM
        ("H8", 42.0, 34.0),  # CM
        ("H9", 45.0, 50.0),  # LM
        ("H10", 52.0, 28.0), # ST (Ball carrier early)
        ("H11", 52.0, 40.0)  # ST
    ]

    away_bases = [
        ("A1", 100.0, 34.0), # GK
        ("A2", 85.0, 12.0),  # LB
        ("A3", 87.0, 26.0),  # CB
        ("A4", 87.0, 42.0),  # CB
        ("A5", 85.0, 56.0),  # RB
        ("A6", 70.0, 34.0),  # DM
        ("A7", 60.0, 18.0),  # LM
        ("A8", 62.0, 34.0),  # CM
        ("A9", 60.0, 50.0),  # RM
        ("A10", 55.0, 30.0), # ST (Tackler)
        ("A11", 55.0, 38.0)  # ST
    ]

    for frame_idx in range(1, num_frames + 1):
        t = frame_idx * 0.04 # 25 FPS
        
        # Ball trajectory: starts with H10, then turnover around frame 50 to A10
        if frame_idx < 50:
            ball_x = 52.0 + (frame_idx * 0.05)
            ball_y = 28.0 + math.sin(t) * 1.5
            ball_vx = 1.25
            ball_vy = 0.5
        elif frame_idx < 55:
            # Contested tackle moment
            ball_x = 54.5 + (frame_idx - 50) * 0.2
            ball_y = 28.0 + (frame_idx - 50) * 0.4
            ball_vx = 2.0
            ball_vy = 1.0
        else:
            # Away team counter attack
            ball_x = 55.5 - (frame_idx - 55) * 0.3
            ball_y = 30.0 + (frame_idx - 55) * 0.1
            ball_vx = -2.5
            ball_vy = 0.5

        players = []
        for pid, bx, by in home_bases:
            px = bx + (frame_idx * 0.03 if pid in ["H10", "H8"] else 0.0)
            py = by + math.sin(t + bx) * 0.4
            players.append({
                "id": pid,
                "team": "Home",
                "x": px,
                "y": py,
                "vx": 0.5 if pid in ["H10", "H8"] else 0.0,
                "vy": 0.1
            })

        for pid, bx, by in away_bases:
            px = bx - ((frame_idx - 50) * 0.15 if frame_idx > 50 and pid in ["A10", "A8"] else 0.0)
            py = by + math.cos(t + bx) * 0.4
            players.append({
                "id": pid,
                "team": "Away",
                "x": px,
                "y": py,
                "vx": -1.5 if frame_idx > 50 and pid in ["A10", "A8"] else 0.0,
                "vy": -0.2
            })

        frames.append({
            "frame_id": frame_idx,
            "ball": {
                "x": ball_x,
                "y": ball_y,
                "vx": ball_vx,
                "vy": ball_vy,
                "in_play": True
            },
            "players": players
        })

    return {"match_id": "METRICA_SAMPLE_001", "frames": frames}

if __name__ == "__main__":
    data = generate_sample_match(120)
    with open("data/sample_match_tracking.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Generated {len(data['frames'])} frames in data/sample_match_tracking.json")
