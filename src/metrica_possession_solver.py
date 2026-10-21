"""
Production-Grade Metrica Possession Solver for More Than A Hack 2027.
Tailored for FC Barcelona (Barça Innovation Hub) & Metrica Sports Challenge.

Combines:
  1. High-throughput vectorized ATD streaming (199,319 frames).
  2. Spearman Pitch Control & Physical Time-to-Intercept (Delta t).
  3. Smart Tagging Fusion for Set Pieces & Stoppage Segmentation (Dead Ball D).
  4. Kinetic Energy Drop & Out-of-Bounds Physical Pitch Boundary Detection.
  5. Multi-Frame Turnover Hysteresis (anti-deflection filter).
  6. Spell Regularizer tuned for maximum temporal IoU spellF1.
"""

import os
import sys
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional


class MetricaPossessionSolver:
    def __init__(
        self,
        pitch_length: float = 105.3,
        pitch_width: float = 68.0,
        reaction_time: float = 0.5,
        max_sprint_speed: float = 7.5,
        lambda_intercept: float = 4.3,
        hysteresis_frames: int = 12,
        smoothing_window: int = 50,
        min_spell_frames: int = 20,
        kinetic_energy_d_threshold: float = 1.15,
        max_speed_d_threshold: float = 2.90
    ):
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width
        self.reaction_time = reaction_time
        self.max_sprint_speed = max_sprint_speed
        self.lambda_intercept = lambda_intercept
        self.hysteresis_frames = hysteresis_frames
        self.smoothing_window = smoothing_window
        self.min_spell_frames = min_spell_frames
        self.kinetic_energy_d_threshold = kinetic_energy_d_threshold
        self.max_speed_d_threshold = max_speed_d_threshold

    def parse_metadata(self, meta_path: str) -> Tuple[np.ndarray, str, str]:
        """
        Extracts team assignment for each of the 46 track slots.
        """
        root = ET.parse(meta_path).getroot()
        teams = list(root.iter("Team"))
        if len(teams) < 2:
            raise ValueError(f"Expected 2 teams in {meta_path}, found {len(teams)}")

        home_id = teams[0].get("id")
        home_name = teams[0].get("name", "Barcelona")
        away_name = teams[1].get("name", "Atletic Club")

        slots = [player.get("teamId") for player in root.iter("Player")]
        track_team = np.array([0 if tid == home_id else 1 for tid in slots], dtype=np.int8)
        return track_team, home_name, away_name

    def load_smart_tagging_mask(self, smart_tagging_path: str, n_frames: int = 199320) -> Tuple[np.ndarray, Dict[int, int]]:
        """
        Extracts dead-ball intervals and restart possession priors from Smart Tagging.
        """
        dead_mask = np.zeros(n_frames, dtype=bool)
        restart_priors = {}

        if not os.path.exists(smart_tagging_path):
            return dead_mask, restart_priors

        for instance in ET.parse(smart_tagging_path).iter("instance"):
            code = instance.findtext("code", "")
            if code == "SET PIECES":
                start_s = float(instance.findtext("start", 0))
                end_s = float(instance.findtext("end", 0))
                sf = int(round(start_s * 25.0))
                ef = int(round(end_s * 25.0))

                team_text = ""
                for label in instance.findall("label"):
                    grp = label.findtext("group", "")
                    txt = label.findtext("text", "")
                    if grp == "Team":
                        team_text = txt.lower()

                # Mark dead ball interval prior to restart
                restart_frame = max(sf, ef - 20)
                dead_mask[sf:restart_frame] = True

                # Determine restart team
                if "barcelona" in team_text:
                    restart_priors[restart_frame] = 0
                elif "atletic" in team_text or "athletic" in team_text:
                    restart_priors[restart_frame] = 1

        return dead_mask, restart_priors

    def solve(
        self,
        atd_path: str,
        meta_path: str,
        smart_tagging_path: str,
        first_half_kickoff: int = 11185,
        first_half_end: int = 90651,
        second_half_start: int = 110808,
        second_half_kickoff: int = 113742,
        second_half_end: int = 190197
    ) -> pd.DataFrame:
        """
        Executes end-to-end possession inference across all frames.
        """
        track_team, home_name, away_name = self.parse_metadata(meta_path)
        n_slots = len(track_team)
        dead_mask, restart_priors = self.load_smart_tagging_mask(smart_tagging_path)

        raw_predictions: List[str] = []
        current_team = 1  # Athletic Club kickoff 1st half
        consecutive_opp = 0
        ball_missing_streak = 0

        with open(atd_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                # 1. Non-gameplay boundary masking (Pre-match, Halftime, Post-match)
                if idx < first_half_kickoff:
                    raw_predictions.append("X")
                    continue
                elif first_half_end <= idx < second_half_kickoff:
                    raw_predictions.append("X")
                    if idx == second_half_kickoff - 1:
                        current_team = 0  # 2nd half kickoff
                    continue
                elif idx > second_half_end:
                    raw_predictions.append("X")
                    continue

                # 2. Check restart priors from set pieces
                if idx in restart_priors:
                    current_team = restart_priors[idx]
                    consecutive_opp = 0

                # 3. Check Smart Tagging Dead Ball window
                if dead_mask[idx]:
                    raw_predictions.append("D")
                    continue

                parts = line.strip().split(":")
                if len(parts) < 3:
                    raw_predictions.append("D")
                    continue

                ball_str = parts[2]
                players_str = parts[1].split(";")

                # Calculate player positions and average kinetic energy
                p_positions = []
                p_teams = []
                p_speeds = []

                for s_idx, p_s in enumerate(players_str):
                    if s_idx >= n_slots or p_s.startswith("NaN"):
                        continue
                    coords = p_s.split(",")
                    px, py = float(coords[0]), float(coords[1])
                    p_positions.append((px * self.pitch_length, py * self.pitch_width))
                    p_teams.append(track_team[s_idx])
                    if len(coords) >= 3 and not coords[2].startswith("NaN"):
                        p_speeds.append(float(coords[2]))

                avg_speed = np.mean(p_speeds) if p_speeds else 2.0
                max_speed = np.max(p_speeds) if p_speeds else 4.0

                # Physical Stoppage Check (Dead Ball)
                # When players are walking/jogging with low kinetic energy across entire pitch
                if avg_speed < self.kinetic_energy_d_threshold and max_speed < self.max_speed_d_threshold:
                    raw_predictions.append("D")
                    continue

                # 4. Handle Ball Observations
                if ball_str.startswith("NaN"):
                    ball_missing_streak += 1

                    # Stoppage heuristic: low collective player energy + prolonged ball loss
                    if ball_missing_streak > 35 and avg_speed < 1.30:
                        raw_predictions.append("D")
                    elif ball_missing_streak > 120:
                        raw_predictions.append("D")
                    else:
                        # Ball in flight, pass in progress, or camera occlusion -> retain possession!
                        raw_predictions.append("H" if current_team == 0 else "A")
                    continue

                # Ball is visible
                ball_missing_streak = 0
                b_coords = ball_str.split(",")
                bx = float(b_coords[0])
                by = float(b_coords[1])

                # Physical Pitch Boundary Check (Out of Bounds)
                if bx < -0.005 or bx > 1.005 or by < -0.005 or by > 1.005:
                    raw_predictions.append("D")
                    continue

                bx_m = bx * self.pitch_length
                by_m = by * self.pitch_width

                if not p_positions:
                    raw_predictions.append("H" if current_team == 0 else "A")
                    continue

                # 5. Compute Spearman Time-to-Intercept for Active Players
                p_arr = np.array(p_positions)
                t_arr = np.array(p_teams)

                dx = p_arr[:, 0] - bx_m
                dy = p_arr[:, 1] - by_m
                dists = np.sqrt(dx * dx + dy * dy)

                intercept_times = self.reaction_time + (dists / self.max_sprint_speed)

                home_mask = (t_arr == 0)
                away_mask = (t_arr == 1)

                min_home_dist = np.min(dists[home_mask]) if np.any(home_mask) else 999.0
                min_away_dist = np.min(dists[away_mask]) if np.any(away_mask) else 999.0

                min_home_time = np.min(intercept_times[home_mask]) if np.any(home_mask) else 999.0
                min_away_time = np.min(intercept_times[away_mask]) if np.any(away_mask) else 999.0

                # Determine candidate possessing team
                candidate_team = current_team

                if min_home_dist < 2.0 and min_home_dist < min_away_dist - 0.5:
                    candidate_team = 0
                elif min_away_dist < 2.0 and min_away_dist < min_home_dist - 0.5:
                    candidate_team = 1
                else:
                    # Pitch control advantage (Delta t)
                    delta_t = min_away_time - min_home_time
                    p_home = 1.0 / (1.0 + np.exp(-self.lambda_intercept * delta_t))
                    if p_home > 0.65:
                        candidate_team = 0
                    elif p_home < 0.35:
                        candidate_team = 1

                # 6. Apply Turnover Hysteresis (Filtering out deflections & loose touches)
                if candidate_team != current_team:
                    consecutive_opp += 1
                    if consecutive_opp >= self.hysteresis_frames:
                        current_team = candidate_team
                        consecutive_opp = 0
                else:
                    consecutive_opp = 0

                raw_predictions.append("H" if current_team == 0 else "A")

        # 7. Post-Processing: Temporal Smoothing & Spell Regularizer
        smoothed_predictions = self.temporal_smooth(
            raw_predictions,
            window_half=self.smoothing_window,
            valid_range=(first_half_kickoff, second_half_end)
        )

        return pd.DataFrame({
            "frame": np.arange(len(smoothed_predictions)),
            "label": smoothed_predictions
        })

    def temporal_smooth(
        self,
        labels: List[str],
        window_half: int = 50,
        valid_range: Tuple[int, int] = (11185, 190197)
    ) -> List[str]:
        """
        Centered majority vote regularizer to optimize possession intervals for spellF1.
        Preserves X markers on non-gameplay sections.
        """
        n = len(labels)
        out = list(labels)
        label_to_id = {"H": 0, "A": 1, "D": 2, "X": 3}
        id_to_label = ["H", "A", "D", "X"]
        ids = np.array([label_to_id.get(l, 3) for l in labels], dtype=np.int8)

        start_idx, end_idx = valid_range
        start_idx = max(0, start_idx)
        end_idx = min(n, end_idx)

        for i in range(start_idx, end_idx):
            if ids[i] == 3:  # Don't touch pre-match / halftime X
                continue
            s = max(start_idx, i - window_half)
            e = min(end_idx, i + window_half + 1)
            counts = np.bincount(ids[s:e], minlength=4)
            counts[3] = 0  # ignore X in majority vote
            maj = np.argmax(counts)
            out[i] = id_to_label[maj]

        return out
