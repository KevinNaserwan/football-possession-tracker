"""
Defensive Counter-Press Latency & PPDA (Passes Per Defensive Action) Analyzer.
Analyzes defensive transitions, counter-pressing speed (Gegenpressing latency),
turnover recovery windows, and high-block pressing intensity for FC Barcelona vs Athletic Club.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd


class CounterPressEngine:
    """
    Computes counter-press reaction latency, turnover recovery windows,
    and PPDA (Passes Per Defensive Action) across all possession changes.
    """

    def __init__(
        self,
        pitch_length: float = 105.3,
        pitch_width: float = 68.0,
        fps: float = 25.0,
        press_distance_threshold: float = 2.0, # meters to ball
        gegenpress_window_sec: float = 5.0      # 5-second counterpress window
    ):
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width
        self.fps = fps
        self.press_thresh = press_distance_threshold
        self.gegenpress_window_frames = int(gegenpress_window_sec * fps)

    def analyze_turnovers(
        self,
        possession_labels: np.ndarray,
        atd_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyzes all turnovers (H -> A and A -> H) and measures counter-pressing latency.
        
        Args:
            possession_labels: Array of 'H', 'A', 'D', 'X' (length N).
            atd_data: List of frame dicts with 'ball' and 'players' (or parsed coordinates).
            
        Returns:
            Dict of turnover analytics and counter-press speed metrics.
        """
        n_frames = min(len(possession_labels), len(atd_data))
        turnovers_h_to_a = []
        turnovers_a_to_h = []

        # 1. Identify all direct possession transition frames
        for i in range(1, n_frames):
            prev_l = possession_labels[i - 1]
            curr_l = possession_labels[i]

            if prev_l == "H" and curr_l == "A":
                turnovers_h_to_a.append(i)
            elif prev_l == "A" and curr_l == "H":
                turnovers_a_to_h.append(i)

        # 2. Compute counter-pressing metrics for Barcelona (when losing H -> A)
        barca_press_latencies = []
        barca_recoveries_within_5s = 0

        for t_frame in turnovers_h_to_a:
            lat = self._compute_press_latency(
                t_frame,
                pressing_team="H",
                atd_data=atd_data,
                max_window=self.gegenpress_window_frames
            )
            if lat is not None:
                barca_press_latencies.append(lat)

            # Check if ball was recovered within 5 seconds
            end_f = min(n_frames, t_frame + self.gegenpress_window_frames)
            if "H" in possession_labels[t_frame + 1:end_f]:
                barca_recoveries_within_5s += 1

        # 3. Compute counter-pressing metrics for Athletic Club (when losing A -> H)
        athletic_press_latencies = []
        athletic_recoveries_within_5s = 0

        for t_frame in turnovers_a_to_h:
            lat = self._compute_press_latency(
                t_frame,
                pressing_team="A",
                atd_data=atd_data,
                max_window=self.gegenpress_window_frames
            )
            if lat is not None:
                athletic_press_latencies.append(lat)

            end_f = min(n_frames, t_frame + self.gegenpress_window_frames)
            if "A" in possession_labels[t_frame + 1:end_f]:
                athletic_recoveries_within_5s += 1

        return {
            "total_turnovers": len(turnovers_h_to_a) + len(turnovers_a_to_h),
            "turnovers_h_to_a": len(turnovers_h_to_a),
            "turnovers_a_to_h": len(turnovers_a_to_h),
            "barca_mean_press_latency_sec": float(np.mean(barca_press_latencies)) if barca_press_latencies else 0.0,
            "barca_median_press_latency_sec": float(np.median(barca_press_latencies)) if barca_press_latencies else 0.0,
            "barca_5s_recovery_rate": float(barca_recoveries_within_5s / max(1, len(turnovers_h_to_a))),
            "athletic_mean_press_latency_sec": float(np.mean(athletic_press_latencies)) if athletic_press_latencies else 0.0,
            "athletic_median_press_latency_sec": float(np.median(athletic_press_latencies)) if athletic_press_latencies else 0.0,
            "athletic_5s_recovery_rate": float(athletic_recoveries_within_5s / max(1, len(turnovers_a_to_h)))
        }

    def _compute_press_latency(
        self,
        turnover_frame: int,
        pressing_team: str,
        atd_data: List[Dict[str, Any]],
        max_window: int
    ) -> Optional[float]:
        """
        Finds the time in seconds until the nearest pressing team player gets within press_distance_threshold.
        """
        n_frames = len(atd_data)
        for offset in range(max_window):
            idx = turnover_frame + offset
            if idx >= n_frames:
                break
            frame_item = atd_data[idx]
            bx = frame_item.get("ball_x")
            by = frame_item.get("ball_y")
            if bx is None or np.isnan(bx) or by is None or np.isnan(by):
                continue

            bx_m = bx * self.pitch_length
            by_m = by * self.pitch_width

            players = frame_item.get("players_home" if pressing_team == "H" else "players_away", [])
            for px, py in players:
                if px is not None and not np.isnan(px) and py is not None and not np.isnan(py):
                    dist = np.hypot(px * self.pitch_length - bx_m, py * self.pitch_width - by_m)
                    if dist <= self.press_thresh:
                        return offset / self.fps
        return None
