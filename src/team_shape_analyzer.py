"""
Tactical Team Shape Dynamics & Dynamic Convex Hull Compactness Analyzer.
Computes tactical team width, length, centroid progression, convex hull surface area,
and stretch index during in-possession vs out-of-possession match states.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy.spatial import ConvexHull


class TeamShapeAnalyzer:
    """
    Quantifies dynamic collective team behavior:
    - Tactical Width (y-spread) and Length (x-depth)
    - Team Surface Area (Convex Hull in m^2)
    - Team Centroid position (Progression line)
    - Team Stretch Index (spatial dispersion around centroid)
    """

    def __init__(
        self,
        pitch_length: float = 105.3,
        pitch_width: float = 68.0
    ):
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width

    def compute_team_shape(self, player_coords_norm: List[Tuple[float, float]]) -> Dict[str, float]:
        """
        Computes spatial metrics for a single team in one frame.
        player_coords_norm: List of (x, y) normalized [0, 1].
        """
        valid_coords = [
            (x * self.pitch_length, y * self.pitch_width)
            for x, y in player_coords_norm
            if x is not None and not np.isnan(x) and y is not None and not np.isnan(y)
        ]

        if len(valid_coords) < 3:
            return {
                "width": 0.0,
                "length": 0.0,
                "area_hull": 0.0,
                "centroid_x": 0.0,
                "centroid_y": 0.0,
                "stretch_index": 0.0
            }

        pts = np.array(valid_coords)
        xs = pts[:, 0]
        ys = pts[:, 1]

        width = float(np.max(ys) - np.min(ys))
        length = float(np.max(xs) - np.min(xs))

        cx = float(np.mean(xs))
        cy = float(np.mean(ys))

        # Stretch index: mean distance of all players to team centroid
        dists_to_centroid = np.hypot(xs - cx, ys - cy)
        stretch_index = float(np.mean(dists_to_centroid))

        # Convex Hull Surface Area
        try:
            hull = ConvexHull(pts)
            area_hull = float(hull.volume)  # In 2D, hull.volume is the 2D surface area
        except Exception:
            area_hull = float(width * length * 0.5)

        return {
            "width": width,
            "length": length,
            "area_hull": area_hull,
            "centroid_x": cx,
            "centroid_y": cy,
            "stretch_index": stretch_index
        }

    def analyze_match_shape(
        self,
        atd_data: List[Dict[str, Any]],
        possession_labels: np.ndarray
    ) -> Dict[str, Any]:
        """
        Analyzes team shape metrics across possession states (In-Possession vs Out-of-Possession).
        """
        n_frames = min(len(atd_data), len(possession_labels))

        home_in_poss_area = []
        home_out_poss_area = []
        home_in_poss_width = []
        home_out_poss_width = []

        away_in_poss_area = []
        away_out_poss_area = []
        away_in_poss_width = []
        away_out_poss_width = []

        for i in range(n_frames):
            lbl = possession_labels[i]
            frame_item = atd_data[i]

            h_shape = self.compute_team_shape(frame_item.get("players_home", []))
            a_shape = self.compute_team_shape(frame_item.get("players_away", []))

            if lbl == "H":
                if h_shape["area_hull"] > 0:
                    home_in_poss_area.append(h_shape["area_hull"])
                    home_in_poss_width.append(h_shape["width"])
                if a_shape["area_hull"] > 0:
                    away_out_poss_area.append(a_shape["area_hull"])
                    away_out_poss_width.append(a_shape["width"])
            elif lbl == "A":
                if a_shape["area_hull"] > 0:
                    away_in_poss_area.append(a_shape["area_hull"])
                    away_in_poss_width.append(a_shape["width"])
                if h_shape["area_hull"] > 0:
                    home_out_poss_area.append(h_shape["area_hull"])
                    home_out_poss_width.append(h_shape["width"])

        return {
            "barca_in_possession_mean_area_m2": float(np.mean(home_in_poss_area)) if home_in_poss_area else 0.0,
            "barca_out_of_possession_mean_area_m2": float(np.mean(home_out_poss_area)) if home_out_poss_area else 0.0,
            "barca_expansion_ratio": float(np.mean(home_in_poss_area) / max(1.0, np.mean(home_out_poss_area))) if home_in_poss_area and home_out_poss_area else 1.0,
            "barca_in_possession_mean_width_m": float(np.mean(home_in_poss_width)) if home_in_poss_width else 0.0,
            "barca_out_of_possession_mean_width_m": float(np.mean(home_out_poss_width)) if home_out_poss_width else 0.0,
            "athletic_in_possession_mean_area_m2": float(np.mean(away_in_poss_area)) if away_in_poss_area else 0.0,
            "athletic_out_of_possession_mean_area_m2": float(np.mean(away_out_poss_area)) if away_out_poss_area else 0.0,
            "athletic_expansion_ratio": float(np.mean(away_in_poss_area) / max(1.0, np.mean(away_out_poss_area))) if away_in_poss_area and away_out_poss_area else 1.0,
            "athletic_in_possession_mean_width_m": float(np.mean(away_in_poss_width)) if away_in_poss_width else 0.0,
            "athletic_out_of_possession_mean_width_m": float(np.mean(away_out_poss_width)) if away_out_poss_width else 0.0
        }
