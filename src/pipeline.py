import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from src.pitch_control import PitchControlEngine
from src.markov_filter import MarkovPossessionFilter

class FullPossessionPipeline:
    """
    End-to-End Match Processing Pipeline:
    Combines planar tracking, Euclidean proximity, Spearman Pitch Control,
    and Markov Temporal Filtering for robust frame-by-frame match analytics.
    """
    def __init__(
        self,
        proximity_threshold: float = 2.0,
        enable_pitch_control: bool = True,
        enable_markov_smoothing: bool = True
    ):
        self.proximity_threshold = proximity_threshold
        self.enable_pitch_control = enable_pitch_control
        self.enable_markov_smoothing = enable_markov_smoothing

        self.pitch_control_engine = PitchControlEngine() if enable_pitch_control else None
        self.markov_filter = MarkovPossessionFilter() if enable_markov_smoothing else None

    def process_frame(self, frame_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single frame dictionary:
        frame_data: {
            'frame_id': int,
            'ball': {'x': float, 'y': float, 'vx': float, 'vy': float, 'in_play': bool},
            'players': [{'id': str, 'team': str, 'x': float, 'y': float, 'vx': float, 'vy': float}, ...]
        }
        """
        frame_id = frame_data.get("frame_id", 0)
        ball = frame_data.get("ball")
        players = frame_data.get("players", [])

        if not ball or not ball.get("in_play", True) or len(players) == 0:
            raw_res = {
                "frame_id": frame_id,
                "possessing_team": None,
                "possessing_player": None,
                "confidence": 0.0,
                "state": "out_of_play"
            }
            if self.markov_filter:
                return self.markov_filter.update(raw_res)
            return raw_res

        ball_pos = np.array([ball["x"], ball["y"]])

        # 1. Proximity and closest player detection
        distances = []
        home_players = []
        away_players = []

        for p in players:
            p_pos = np.array([p["x"], p["y"]])
            dist = float(np.linalg.norm(p_pos - ball_pos))
            distances.append((p, dist))

            if p.get("team") == "Home":
                home_players.append(p)
            elif p.get("team") == "Away":
                away_players.append(p)

        distances.sort(key=lambda x: x[1])
        closest_player, min_distance = distances[0]

        if min_distance <= self.proximity_threshold:
            confidence = max(0.5, 1.0 - (min_distance / self.proximity_threshold))
            raw_res = {
                "frame_id": frame_id,
                "possessing_team": closest_player["team"],
                "possessing_player": closest_player["id"],
                "min_distance": min_distance,
                "confidence": float(confidence),
                "state": "controlled"
            }
        else:
            raw_res = {
                "frame_id": frame_id,
                "possessing_team": "Contested",
                "possessing_player": None,
                "min_distance": min_distance,
                "confidence": 0.25,
                "state": "loose_ball"
            }

        # 2. Pitch control surface estimation
        if self.pitch_control_engine:
            pc_metrics = self.pitch_control_engine.calculate_pitch_control_surface(
                home_players, away_players, (ball["x"], ball["y"])
            )
            raw_res["home_pitch_control_pct"] = pc_metrics["home_pct"]
            raw_res["away_pitch_control_pct"] = pc_metrics["away_pct"]

        # 3. Markov temporal filtering
        if self.markov_filter:
            final_res = self.markov_filter.update(raw_res)
        else:
            final_res = raw_res

        return final_res
