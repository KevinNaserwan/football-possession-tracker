"""
Spatial Pitch Control Surface & Tactical Dominance Field Analyzer.
Computes Spearman 2018 2D Pitch Control Field, Voronoi Space Partitioning,
and Team Territorial Domination across possession spells.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


class PitchControlFieldAnalyzer:
    """
    Computes spatial pitch control surface on a discrete grid (e.g., 32x20 or 50x32).
    Quantifies territorial dominance (percentage of pitch controlled) per frame and spell.
    """
    def __init__(
        self,
        pitch_length: float = 105.3,
        pitch_width: float = 68.0,
        grid_cells_x: int = 32,
        grid_cells_y: int = 20,
        reaction_time: float = 0.5,
        max_sprint_speed: float = 7.5,
        lambda_intercept: float = 4.3
    ):
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width
        self.nx = grid_cells_x
        self.ny = grid_cells_y
        self.reaction_time = reaction_time
        self.max_sprint_speed = max_sprint_speed
        self.lambda_intercept = lambda_intercept

        # Precompute 2D pitch grid coordinates in meters
        x_lin = np.linspace(0, pitch_length, grid_cells_x)
        y_lin = np.linspace(0, pitch_width, grid_cells_y)
        self.grid_x, self.grid_y = np.meshgrid(x_lin, y_lin)  # Shape: (ny, nx)
        self.flat_x = self.grid_x.ravel()  # (N_grid,)
        self.flat_y = self.grid_y.ravel()  # (N_grid,)
        self.n_grid_points = len(self.flat_x)

    def compute_frame_control_surface(
        self,
        home_players: np.ndarray,
        away_players: np.ndarray
    ) -> Tuple[np.ndarray, float, float]:
        """
        Calculates pitch control probability field P_home(x, y) on the grid.
        Returns:
            P_home: 2D array of shape (ny, nx) with values in [0, 1]
            home_territory_pct: Percentage of pitch dominated by Home (> 0.5)
            away_territory_pct: Percentage of pitch dominated by Away (< 0.5)
        """
        if len(home_players) == 0 or len(away_players) == 0:
            return np.full((self.ny, self.nx), 0.5), 50.0, 50.0

        # home_players: (N_h, 2) | away_players: (N_a, 2)
        # Compute distances from each grid point to each player
        # Grid: (N_pts, 1, 2) vs Players: (1, N_p, 2)
        grid_pts = np.stack([self.flat_x, self.flat_y], axis=1)[:, np.newaxis, :]

        # Home distances & time-to-intercept
        h_diff = grid_pts - home_players[np.newaxis, :, :]
        h_dists = np.sqrt(np.sum(h_diff**2, axis=-1))  # (N_pts, N_h)
        tau_home = self.reaction_time + (h_dists / self.max_sprint_speed)
        min_tau_home = np.min(tau_home, axis=-1)  # (N_pts,)

        # Away distances & time-to-intercept
        a_diff = grid_pts - away_players[np.newaxis, :, :]
        a_dists = np.sqrt(np.sum(a_diff**2, axis=-1))  # (N_pts, N_a)
        tau_away = self.reaction_time + (a_dists / self.max_sprint_speed)
        min_tau_away = np.min(tau_away, axis=-1)  # (N_pts,)

        # Logistic pitch control advantage Delta tau
        delta_tau = min_tau_away - min_tau_home  # Positive = Home arrives faster
        p_home_flat = 1.0 / (1.0 + np.exp(-self.lambda_intercept * delta_tau))

        p_home_2d = p_home_flat.reshape((self.ny, self.nx))
        home_pct = float(np.mean(p_home_flat >= 0.5) * 100.0)
        away_pct = float(100.0 - home_pct)

        return p_home_2d, home_pct, away_pct

    def compute_spell_territorial_dominance(
        self,
        atd_path: str,
        meta_path: str,
        start_frame: int,
        end_frame: int,
        sample_step: int = 5
    ) -> Dict[str, float]:
        """
        Measures the average tactical pitch control dominance across a possession spell.
        """
        import xml.etree.ElementTree as ET
        root = ET.parse(meta_path).getroot()
        home_id = list(root.iter("Team"))[0].get("id")
        slots = [p.get("teamId") for p in root.iter("Player")]
        track_team = np.array([0 if tid == home_id else 1 for tid in slots], dtype=np.int8)

        home_pcts = []
        away_pcts = []

        with open(atd_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if idx < start_frame:
                    continue
                if idx > end_frame:
                    break
                if (idx - start_frame) % sample_step != 0:
                    continue

                parts = line.strip().split(":")
                if len(parts) < 2:
                    continue

                players_str = parts[1].split(";")
                h_pos, a_pos = [], []
                for s, p_str in enumerate(players_str):
                    if p_str.startswith("NaN") or s >= len(track_team):
                        continue
                    coords = p_str.split(",")
                    x_m = float(coords[0]) * self.pitch_length
                    y_m = float(coords[1]) * self.pitch_width
                    if track_team[s] == 0:
                        h_pos.append([x_m, y_m])
                    else:
                        a_pos.append([x_m, y_m])

                _, hp, ap = self.compute_frame_control_surface(
                    np.array(h_pos), np.array(a_pos)
                )
                home_pcts.append(hp)
                away_pcts.append(ap)

        return {
            "mean_home_territory_pct": float(np.mean(home_pcts)) if home_pcts else 50.0,
            "mean_away_territory_pct": float(np.mean(away_pcts)) if away_pcts else 50.0,
            "frames_analyzed": len(home_pcts)
        }
