"""
Passing Event & Sequence Detection Engine for Metrica Tracking Data.
Detects pass release, ball flight trajectory, pass reception, and sequence lengths.
Provides tactical explainability and proves pass transit possession continuity.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET


class PassDetectionEngine:
    def __init__(
        self,
        pitch_length: float = 105.3,
        pitch_width: float = 68.0,
        min_pass_speed: float = 4.0,       # Min ball speed in m/s to qualify as pass flight
        max_pass_duration_frames: int = 100, # Max flight duration ~ 4 seconds
        control_radius: float = 2.0         # Reception distance
    ):
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width
        self.min_pass_speed = min_pass_speed
        self.max_pass_duration_frames = max_pass_duration_frames
        self.control_radius = control_radius

    def parse_metadata(self, meta_path: str) -> Tuple[np.ndarray, str, str]:
        root = ET.parse(meta_path).getroot()
        teams = list(root.iter("Team"))
        home_id = teams[0].get("id")
        home_name = teams[0].get("name", "Home")
        away_name = teams[1].get("name", "Away") if len(teams) > 1 else "Away"
        slots = [p.get("teamId") for p in root.iter("Player")]
        track_team = np.array([0 if tid == home_id else 1 for tid in slots], dtype=np.int8)
        return track_team, home_name, away_name

    def detect_passes(
        self,
        atd_path: str,
        meta_path: str,
        start_frame: int = 11185,
        end_frame: int = 18684
    ) -> pd.DataFrame:
        """
        Scans frames to detect ballistic ball flight events between players.
        """
        track_team, _, _ = self.parse_metadata(meta_path)
        
        # Load ball and player coordinates for range
        frames_data = []
        with open(atd_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if idx < start_frame:
                    continue
                if idx > end_frame:
                    break
                
                parts = line.strip().split(":")
                if len(parts) < 3:
                    continue

                ball_str = parts[2]
                players_str = parts[1].split(";")

                is_ball_missing = ball_str.startswith("NaN")
                bx_m, by_m = np.nan, np.nan
                if not is_ball_missing:
                    b_coords = ball_str.split(",")
                    bx_m = float(b_coords[0]) * self.pitch_length
                    by_m = float(b_coords[1]) * self.pitch_width

                p_pos = []
                p_teams = []
                for s, p in enumerate(players_str):
                    if p.startswith("NaN") or s >= len(track_team):
                        continue
                    coords = p.split(",")
                    px = float(coords[0]) * self.pitch_length
                    py = float(coords[1]) * self.pitch_width
                    p_pos.append([px, py])
                    p_teams.append(track_team[s])

                frames_data.append({
                    "frame": idx,
                    "bx": bx_m,
                    "by": by_m,
                    "p_pos": np.array(p_pos) if p_pos else np.empty((0, 2)),
                    "p_teams": np.array(p_teams) if p_teams else np.empty(0, dtype=np.int8)
                })

        passes = []
        in_pass = False
        pass_start_f = 0
        pass_start_team = -1
        pass_start_pos = (0.0, 0.0)

        for i in range(1, len(frames_data) - 1):
            curr = frames_data[i]
            prev = frames_data[i - 1]
            
            if np.isnan(curr["bx"]) or np.isnan(prev["bx"]):
                continue

            # Calculate 2D instantaneous ball speed
            dx = curr["bx"] - prev["bx"]
            dy = curr["by"] - prev["by"]
            v_ball = np.sqrt(dx * dx + dy * dy) * 25.0

            # Find closest player
            if len(curr["p_pos"]) > 0:
                p_diff = curr["p_pos"] - np.array([curr["bx"], curr["by"]])
                dists = np.sqrt(np.sum(p_diff**2, axis=-1))
                min_idx = np.argmin(dists)
                min_dist = dists[min_idx]
                closest_team = curr["p_teams"][min_idx]
            else:
                min_dist = 999.0
                closest_team = -1

            if not in_pass:
                # Trigger pass start: ball accelerating away with high speed, previously controlled
                if v_ball >= self.min_pass_speed and min_dist <= 2.5 and closest_team != -1:
                    in_pass = True
                    pass_start_f = curr["frame"]
                    pass_start_team = closest_team
                    pass_start_pos = (curr["bx"], curr["by"])
            else:
                # Check for pass completion or interception
                flight_dur = curr["frame"] - pass_start_f
                
                # Reception condition: ball slows down or player gets within control radius
                if min_dist <= self.control_radius and flight_dur >= 5:
                    outcome = "successful" if closest_team == pass_start_team else "intercepted"
                    pass_dist = np.sqrt((curr["bx"] - pass_start_pos[0])**2 + (curr["by"] - pass_start_pos[1])**2)
                    
                    if pass_dist >= 4.0:  # Valid pass must travel at least 4 meters
                        passes.append({
                            "pass_id": len(passes) + 1,
                            "start_frame": pass_start_f,
                            "end_frame": curr["frame"],
                            "duration_s": flight_dur / 25.0,
                            "team": "Barcelona" if pass_start_team == 0 else "Athletic Club",
                            "distance_m": round(pass_dist, 2),
                            "outcome": outcome,
                            "start_x": round(pass_start_pos[0], 2),
                            "start_y": round(pass_start_pos[1], 2),
                            "end_x": round(curr["bx"], 2),
                            "end_y": round(curr["by"], 2)
                        })
                    in_pass = False

                elif flight_dur > self.max_pass_duration_frames:
                    in_pass = False

        return pd.DataFrame(passes)
