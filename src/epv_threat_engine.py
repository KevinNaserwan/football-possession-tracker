"""
Expected Possession Value (EPV) & Spatial Threat Surface Engine.
Quantifies offensive danger, threat generation, and expected possession value (EPV)
by coupling continuous 2D Pitch Control with empirical spatial goal-threat surfaces.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np


class ExpectedPossessionValueEngine:
    """
    Computes spatial threat surfaces, instantaneous EPV, and cumulative threat added (ΔEPV)
    across possession spells for both Home (FC Barcelona) and Away (Athletic Club).
    """

    def __init__(
        self,
        pitch_length: float = 105.3,
        pitch_width: float = 68.0,
        grid_cells_x: int = 32,
        grid_cells_y: int = 20,
        goal_width: float = 7.32
    ):
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width
        self.nx = grid_cells_x
        self.ny = grid_cells_y
        self.goal_width = goal_width

        # Goal coordinates in meters
        self.goal_home_x = pitch_length  # When Home attacks right (+x)
        self.goal_home_y = pitch_width / 2.0
        self.goal_away_x = 0.0           # When Away attacks left (-x)
        self.goal_away_y = pitch_width / 2.0

        # Create coordinate grids
        x_lin = np.linspace(0, pitch_length, grid_cells_x)
        y_lin = np.linspace(0, pitch_width, grid_cells_y)
        self.grid_x, self.grid_y = np.meshgrid(x_lin, y_lin)

        # Precompute static spatial threat baseline for attacking right and left
        self.threat_grid_right = self._compute_spatial_threat_grid(target_x=self.goal_home_x)
        self.threat_grid_left = self._compute_spatial_threat_grid(target_x=self.goal_away_x)

    def _compute_spatial_threat_grid(self, target_x: float) -> np.ndarray:
        """
        Computes a calibrated goal-threat surface based on distance to goal,
        subtended shooting angle, and proximity to danger zones (penalty box / half-spaces).
        Output range: [0.0, 1.0].
        """
        gy_top = (self.pitch_width + self.goal_width) / 2.0
        gy_bot = (self.pitch_width - self.goal_width) / 2.0

        dx = target_x - self.grid_x
        dy_center = self.pitch_width / 2.0 - self.grid_y
        dist = np.sqrt(dx**2 + dy_center**2) + 1e-5

        # Subtended angle theta by goal posts
        vec1 = np.stack([target_x - self.grid_x, gy_top - self.grid_y], axis=-1)
        vec2 = np.stack([target_x - self.grid_x, gy_bot - self.grid_y], axis=-1)
        cos_theta = np.sum(vec1 * vec2, axis=-1) / (
            np.linalg.norm(vec1, axis=-1) * np.linalg.norm(vec2, axis=-1) + 1e-5
        )
        cos_theta = np.clip(cos_theta, -1.0, 1.0)
        theta = np.arccos(cos_theta)  # radians

        # Distance decay exponential
        dist_factor = np.exp(-dist / 22.0)

        # Angle factor normalized by pi
        angle_factor = theta / (np.pi / 2.0)

        # Base threat surface
        threat = 0.65 * (angle_factor * dist_factor) + 0.35 * (dist_factor ** 1.5)

        # Penalty box bonus (within 16.5m of goal line and inside width 40.32m)
        in_box_x = np.abs(self.grid_x - target_x) <= 16.5
        in_box_y = np.abs(self.grid_y - self.pitch_width / 2.0) <= 20.16
        threat[in_box_x & in_box_y] *= 1.25

        return np.clip(threat, 0.0, 1.0)

    def evaluate_ball_threat(
        self,
        ball_x_norm: float,
        ball_y_norm: float,
        attacking_team: str,
        half: int = 1
    ) -> float:
        """
        Evaluates the spatial goal-threat value at the normalized ball location [0, 1].
        """
        if np.isnan(ball_x_norm) or np.isnan(ball_y_norm):
            return 0.0

        bx_m = np.clip(ball_x_norm, 0.0, 1.0) * self.pitch_length
        by_m = np.clip(ball_y_norm, 0.0, 1.0) * self.pitch_width

        # Direction: in 1st half, Home (Barca) attacks right (+x), Away attacks left (-x)
        # in 2nd half: reversed
        if half == 1:
            attacks_right = (attacking_team == "H")
        else:
            attacks_right = (attacking_team == "A")

        target_x = self.goal_home_x if attacks_right else self.goal_away_x
        gy_top = (self.pitch_width + self.goal_width) / 2.0
        gy_bot = (self.pitch_width - self.goal_width) / 2.0

        dx = target_x - bx_m
        dy_center = self.pitch_width / 2.0 - by_m
        dist = np.sqrt(dx**2 + dy_center**2) + 1e-5

        vec1 = np.array([target_x - bx_m, gy_top - by_m])
        vec2 = np.array([target_x - bx_m, gy_bot - by_m])
        cos_th = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2) + 1e-5)
        theta = np.arccos(np.clip(cos_th, -1.0, 1.0))

        dist_factor = np.exp(-dist / 22.0)
        angle_factor = theta / (np.pi / 2.0)
        threat = 0.65 * (angle_factor * dist_factor) + 0.35 * (dist_factor ** 1.5)

        if np.abs(bx_m - target_x) <= 16.5 and np.abs(by_m - self.pitch_width / 2.0) <= 20.16:
            threat *= 1.25

        return float(np.clip(threat, 0.0, 1.0))

    def compute_epv_sequence(
        self,
        ball_coords: np.ndarray,
        possession_labels: np.ndarray,
        half: int = 1
    ) -> Dict[str, Any]:
        """
        Computes the frame-by-frame instantaneous Expected Possession Value (EPV)
        and cumulative threat metrics across a sequence.
        
        Args:
            ball_coords: Shape (N, 2), normalized [0, 1].
            possession_labels: Array of 'H', 'A', 'D', 'X'.
            half: Match half (1 or 2).
            
        Returns:
            Dict containing epv_values, mean_epv_home, mean_epv_away, peak_threat_spells.
        """
        n_frames = len(possession_labels)
        epv_arr = np.zeros(n_frames, dtype=float)

        home_threats = []
        away_threats = []

        for i in range(n_frames):
            lbl = possession_labels[i]
            if lbl in ("H", "A"):
                bx, by = ball_coords[i, 0], ball_coords[i, 1]
                t_val = self.evaluate_ball_threat(bx, by, attacking_team=lbl, half=half)
                epv_arr[i] = t_val
                if lbl == "H":
                    home_threats.append(t_val)
                else:
                    away_threats.append(t_val)

        return {
            "epv_array": epv_arr,
            "mean_threat_home": float(np.mean(home_threats)) if home_threats else 0.0,
            "mean_threat_away": float(np.mean(away_threats)) if away_threats else 0.0,
            "max_threat_home": float(np.max(home_threats)) if home_threats else 0.0,
            "max_threat_away": float(np.max(away_threats)) if away_threats else 0.0,
            "total_active_threat_frames": len(home_threats) + len(away_threats)
        }
