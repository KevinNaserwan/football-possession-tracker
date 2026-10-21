"""
Vectorized Feature Extractor for Football Possession Tracking.
Extracts spatial, kinematic, pitch control, and tactical features per frame.
Designed for Metrica Sports EPTS data.
"""

import os
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET


class TacticalFeatureExtractor:
    def __init__(
        self,
        pitch_length: float = 105.3,
        pitch_width: float = 68.0,
        reaction_time: float = 0.5,
        max_sprint_speed: float = 7.5,
        lambda_intercept: float = 4.3
    ):
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width
        self.reaction_time = reaction_time
        self.max_sprint_speed = max_sprint_speed
        self.lambda_intercept = lambda_intercept

    def parse_metadata(self, meta_path: str) -> Tuple[np.ndarray, str, str]:
        root = ET.parse(meta_path).getroot()
        teams = list(root.iter("Team"))
        home_id = teams[0].get("id")
        home_name = teams[0].get("name", "Home")
        away_name = teams[1].get("name", "Away") if len(teams) > 1 else "Away"
        slots = [p.get("teamId") for p in root.iter("Player")]
        track_team = np.array([0 if tid == home_id else 1 for tid in slots], dtype=np.int8)
        return track_team, home_name, away_name

    def load_smart_tagging_masks(
        self,
        smart_tagging_path: str,
        n_frames: int = 199320
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Returns binary masks:
          dead_mask: True during set piece stoppages
          active_phase_mask: True during tactical progression/buildup
          goal_mask: True during goal celebrations
        """
        dead_mask = np.zeros(n_frames, dtype=bool)
        active_phase_mask = np.zeros(n_frames, dtype=bool)
        goal_mask = np.zeros(n_frames, dtype=bool)

        if not os.path.exists(smart_tagging_path):
            return dead_mask, active_phase_mask, goal_mask

        tree = ET.parse(smart_tagging_path)
        for instance in tree.iter("instance"):
            code = instance.findtext("code", "").strip()
            start_s = float(instance.findtext("start", 0))
            end_s = float(instance.findtext("end", 0))
            sf = int(round(start_s * 25.0))
            ef = int(round(end_s * 25.0))

            if code == "SET PIECES":
                stoppage_start = max(0, sf - 150)
                dead_mask[stoppage_start:ef] = True
            elif code == "GOALS":
                goal_mask[sf:ef] = True
            elif code in [
                "PROGRESSION", "BUILD UP", "ATTACKING TRANSITION",
                "CREATING CHANCES", "BALL IN FINAL THIRD"
            ]:
                active_phase_mask[sf:ef] = True

        return dead_mask, active_phase_mask, goal_mask

    def extract_features(
        self,
        atd_path: str,
        meta_path: str,
        smart_tagging_path: str,
        start_frame: int = 0,
        end_frame: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Streams ATD and extracts per-frame features.
        """
        track_team, _, _ = self.parse_metadata(meta_path)
        dead_mask, active_mask, goal_mask = self.load_smart_tagging_masks(smart_tagging_path)

        rows = []
        prev_bx, prev_by = None, None
        ball_missing_streak = 0

        with open(atd_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if idx < start_frame:
                    continue
                if end_frame is not None and idx > end_frame:
                    break

                parts = line.strip().split(":")
                if len(parts) < 3:
                    continue

                ball_str = parts[2]
                players_str = parts[1].split(";")

                # Parse ball
                is_ball_missing = ball_str.startswith("NaN")
                if is_ball_missing:
                    ball_missing_streak += 1
                    bx_norm, by_norm = np.nan, np.nan
                    bx_m, by_m = np.nan, np.nan
                    ball_speed = 0.0
                else:
                    ball_missing_streak = 0
                    b_coords = ball_str.split(",")
                    bx_norm = float(b_coords[0])
                    by_norm = float(b_coords[1])
                    bx_m = bx_norm * self.pitch_length
                    by_m = by_norm * self.pitch_width

                    ball_speed = 0.0
                    if prev_bx is not None and prev_by is not None:
                        ball_speed = np.sqrt((bx_m - prev_bx)**2 + (by_m - prev_by)**2) * 25.0
                    prev_bx, prev_by = bx_m, by_m

                # Parse players
                p_positions = []
                p_teams = []
                p_speeds = []

                for slot, p_str in enumerate(players_str):
                    if p_str.startswith("NaN") or slot >= len(track_team):
                        continue
                    p_coords = p_str.split(",")
                    px_m = float(p_coords[0]) * self.pitch_length
                    py_m = float(p_coords[1]) * self.pitch_width
                    spd = float(p_coords[2]) if len(p_coords) > 2 and not p_coords[2].startswith("NaN") else 0.0

                    p_positions.append([px_m, py_m])
                    p_teams.append(track_team[slot])
                    p_speeds.append(spd)

                # Collective team metrics
                avg_speed = np.mean(p_speeds) if p_speeds else 0.0
                max_speed = np.max(p_speeds) if p_speeds else 0.0

                p_arr = np.array(p_positions) if p_positions else np.empty((0, 2))
                t_arr = np.array(p_teams) if p_teams else np.empty(0, dtype=np.int8)

                # Centroids
                home_mask = (t_arr == 0)
                away_mask = (t_arr == 1)

                c_hx = np.mean(p_arr[home_mask, 0]) if np.any(home_mask) else 52.65
                c_hy = np.mean(p_arr[home_mask, 1]) if np.any(home_mask) else 34.0
                c_ax = np.mean(p_arr[away_mask, 0]) if np.any(away_mask) else 52.65
                c_ay = np.mean(p_arr[away_mask, 1]) if np.any(away_mask) else 34.0

                # Proximity & Pitch Control
                if not is_ball_missing and len(p_arr) > 0:
                    dx = p_arr[:, 0] - bx_m
                    dy = p_arr[:, 1] - by_m
                    dists = np.sqrt(dx * dx + dy * dy)

                    d_home_min = np.min(dists[home_mask]) if np.any(home_mask) else 50.0
                    d_away_min = np.min(dists[away_mask]) if np.any(away_mask) else 50.0

                    n_home_3m = np.sum((dists[home_mask] <= 3.0)) if np.any(home_mask) else 0
                    n_away_3m = np.sum((dists[away_mask] <= 3.0)) if np.any(away_mask) else 0

                    tau_home = self.reaction_time + (d_home_min / self.max_sprint_speed)
                    tau_away = self.reaction_time + (d_away_min / self.max_sprint_speed)
                    delta_tau = tau_away - tau_home
                    p_spearman = 1.0 / (1.0 + np.exp(-self.lambda_intercept * delta_tau))

                    dist_center = np.sqrt((bx_m - 52.65)**2 + (by_m - 34.0)**2)
                    in_home_box = 1.0 if (bx_m <= 16.5 and 13.84 <= by_m <= 54.16) else 0.0
                    in_away_box = 1.0 if (bx_m >= 88.8 and 13.84 <= by_m <= 54.16) else 0.0
                else:
                    d_home_min = 50.0
                    d_away_min = 50.0
                    n_home_3m = 0
                    n_away_3m = 0
                    delta_tau = 0.0
                    p_spearman = 0.5
                    dist_center = 0.0
                    in_home_box = 0.0
                    in_away_box = 0.0

                # Stoppage flag
                is_kinetic_dead = 1.0 if (avg_speed < 1.15 and max_speed < 2.80) else 0.0

                rows.append({
                    "frame": idx,
                    "ball_missing": 1 if is_ball_missing else 0,
                    "ball_missing_streak": ball_missing_streak,
                    "ball_x_norm": bx_norm if not is_ball_missing else 0.5,
                    "ball_y_norm": by_norm if not is_ball_missing else 0.5,
                    "ball_speed": ball_speed,
                    "d_home_min": d_home_min,
                    "d_away_min": d_away_min,
                    "d_delta": d_away_min - d_home_min,
                    "d_ratio": d_home_min / (d_home_min + d_away_min + 1e-4),
                    "n_home_3m": n_home_3m,
                    "n_away_3m": n_away_3m,
                    "delta_tau": delta_tau,
                    "p_spearman": p_spearman,
                    "dist_center": dist_center,
                    "in_home_box": in_home_box,
                    "in_away_box": in_away_box,
                    "avg_player_speed": avg_speed,
                    "max_player_speed": max_speed,
                    "is_kinetic_dead": is_kinetic_dead,
                    "is_set_piece": 1 if dead_mask[idx] else 0,
                    "is_active_phase": 1 if active_mask[idx] else 0,
                    "is_goal": 1 if goal_mask[idx] else 0,
                    "c_hx": c_hx, "c_hy": c_hy,
                    "c_ax": c_ax, "c_ay": c_ay
                })

        return pd.DataFrame(rows)
