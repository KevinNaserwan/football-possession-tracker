"""
Multi-Camera ATD Fusion Module for More Than A Hack 2027.
Fuses Tactical Optical ATD with Broadcast Camera ATD via Homography Validation.
Recovers occluded ball trajectories and increases active tracking coverage.
"""

import os
from typing import Dict, Tuple, Optional
import numpy as np
import pandas as pd


class MultiCameraFusion:
    def __init__(
        self,
        pitch_length: float = 105.3,
        pitch_width: float = 68.0,
        max_reprojection_error: float = 0.50,
        first_half_offset: int = 4014
    ):
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width
        self.max_reprojection_error = max_reprojection_error
        self.first_half_offset = first_half_offset

    def load_broadcast_valid_frames(self, homography_path: str) -> set:
        """
        Extracts broadcast frames where homography is verified valid
        and reprojection error is strictly below threshold (filters out replays & cuts).
        """
        if not os.path.exists(homography_path):
            return set()

        df = pd.read_csv(homography_path)
        valid_df = df[
            (df["valid"] == 1) &
            (df["reprojection_error"] < self.max_reprojection_error)
        ]
        return set(valid_df["frame"].astype(int).values)

    def load_broadcast_ball_map(
        self,
        broadcast_atd_path: str,
        valid_bc_frames: set
    ) -> Dict[int, Tuple[float, float]]:
        """
        Extracts valid normalized (x, y) ball coordinates from Broadcast ATD.
        """
        bc_ball_map: Dict[int, Tuple[float, float]] = {}
        if not os.path.exists(broadcast_atd_path):
            return bc_ball_map

        with open(broadcast_atd_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if idx in valid_bc_frames:
                    parts = line.strip().split(":")
                    if len(parts) >= 3 and not parts[2].startswith("NaN"):
                        coords = parts[2].split(",")
                        bx = float(coords[0])
                        by = float(coords[1])
                        # Keep physical pitch bounds [0, 1]
                        if -0.01 <= bx <= 1.01 and -0.01 <= by <= 1.01:
                            bc_ball_map[idx] = (bx, by)
        return bc_ball_map

    def fuse_ball_trajectories(
        self,
        tactical_atd_path: str,
        broadcast_atd_path: str,
        broadcast_homography_path: str,
        n_frames: int = 199320
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, int]]:
        """
        Fuses tactical ball tracking with broadcast optical recovery.
        Returns:
            bx_arr: Float array of normalized x coordinates (NaN if missing in both)
            by_arr: Float array of normalized y coordinates
            source_arr: Int array (0: None, 1: Tactical, 2: Broadcast Imputed)
            stats: Dictionary of fusion metrics
        """
        valid_bc_frames = self.load_broadcast_valid_frames(broadcast_homography_path)
        bc_ball_map = self.load_broadcast_ball_map(broadcast_atd_path, valid_bc_frames)

        bx_arr = np.full(n_frames, np.nan, dtype=np.float32)
        by_arr = np.full(n_frames, np.nan, dtype=np.float32)
        source_arr = np.zeros(n_frames, dtype=np.int8)

        stats = {
            "tactical_valid": 0,
            "tactical_missing": 0,
            "broadcast_recovered": 0,
            "both_missing": 0
        }

        with open(tactical_atd_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if idx >= n_frames:
                    break

                parts = line.strip().split(":")
                if len(parts) < 3:
                    continue

                ball_str = parts[2]
                if not ball_str.startswith("NaN"):
                    coords = ball_str.split(",")
                    bx_arr[idx] = float(coords[0])
                    by_arr[idx] = float(coords[1])
                    source_arr[idx] = 1
                    stats["tactical_valid"] += 1
                else:
                    stats["tactical_missing"] += 1
                    # Attempt broadcast optical recovery in 1st half
                    if idx <= 90651:
                        bc_idx = idx - self.first_half_offset
                        if bc_idx in bc_ball_map:
                            bx_rec, by_rec = bc_ball_map[bc_idx]
                            bx_arr[idx] = bx_rec
                            by_arr[idx] = by_rec
                            source_arr[idx] = 2
                            stats["broadcast_recovered"] += 1
                        else:
                            stats["both_missing"] += 1
                    else:
                        stats["both_missing"] += 1

        return bx_arr, by_arr, source_arr, stats
