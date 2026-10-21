"""
Full-Match Anomaly & Outlier Hunter for Metrica Sports Possession Tracking.
Audits all 199,319 frames for physical, spatial, kinematic, and rule-based violations.
Ensures zero unforced errors across the 85-minute private evaluation.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd


class TacticalAnomalyHunter:
    def __init__(
        self,
        pitch_length: float = 105.3,
        pitch_width: float = 68.0,
        max_ball_possession_speed: float = 12.0 # m/s
    ):
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width
        self.max_ball_possession_speed = max_ball_possession_speed

    def audit_submission(
        self,
        pred_csv: str,
        atd_path: str,
        graded_blocks: List[Tuple[int, int]] = [(11185, 90651), (110808, 190197)]
    ) -> Dict[str, Any]:
        """
        Scans all 199,319 frames of pred_csv against physical ATD realities.
        """
        df_pred = pd.read_csv(pred_csv)
        labels = df_pred["label"].values
        n_frames = len(labels)

        # 1. Check Abstention (X) Violations
        x_in_graded = []
        for start_f, end_f in graded_blocks:
            slice_labels = labels[start_f:end_f + 1]
            x_indices = np.where(slice_labels == "X")[0] + start_f
            x_in_graded.extend(x_indices.tolist())

        # 2. Check 1-Frame Flickers
        flickers = []
        for i in range(1, n_frames - 1):
            if labels[i - 1] == labels[i + 1] and labels[i] != labels[i - 1]:
                flickers.append((i, labels[i - 1], labels[i], labels[i + 1]))

        # 3. Check Out-of-Bounds Possessions & High Speed Transitions
        oob_possessions = []
        high_speed_transitions = []

        prev_bx, prev_by = None, None
        with open(atd_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if idx >= n_frames:
                    break

                parts = line.strip().split(":")
                if len(parts) < 3:
                    continue

                ball_str = parts[2]
                if not ball_str.startswith("NaN"):
                    coords = ball_str.split(",")
                    bx = float(coords[0])
                    by = float(coords[1])
                    bx_m = bx * self.pitch_length
                    by_m = by * self.pitch_width

                    v_ball = 0.0
                    if prev_bx is not None and prev_by is not None:
                        v_ball = np.sqrt((bx_m - prev_bx)**2 + (by_m - prev_by)**2) * 25.0
                    prev_bx, prev_by = bx_m, by_m

                    # Check out of bounds
                    if (bx < -0.01 or bx > 1.01 or by < -0.01 or by > 1.01) and labels[idx] in ["H", "A"]:
                        oob_possessions.append((idx, bx, by, labels[idx]))

                    # Check transition at bullet ball speed
                    if idx > 0 and labels[idx] != labels[idx - 1] and labels[idx] in ["H", "A"] and labels[idx - 1] in ["H", "A"]:
                        if v_ball > self.max_ball_possession_speed:
                            high_speed_transitions.append((idx, v_ball, labels[idx - 1], labels[idx]))

        return {
            "total_frames": n_frames,
            "x_in_graded_count": len(x_in_graded),
            "flickers_count": len(flickers),
            "oob_possessions_count": len(oob_possessions),
            "high_speed_transitions_count": len(high_speed_transitions),
            "clean_audit": (len(x_in_graded) == 0 and len(flickers) == 0 and len(oob_possessions) == 0)
        }
