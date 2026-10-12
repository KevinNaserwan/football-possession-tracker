import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Generator

class MetricaTrackingParser:
    """
    Parser for Metrica Sports EPTS & ATD tracking datasets.
    Handles coordinate normalization (converts normalized [0, 1] space
    to standard pitch dimensions [105m x 68m]) and structures frame streams.
    """
    def __init__(self, pitch_length: float = 105.0, pitch_width: float = 68.0):
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width

    def parse_frame_dict(self, raw_frame: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalizes single raw frame coordinates into pitch meters.
        """
        frame_id = raw_frame.get("frame_id", 0)
        ball = raw_frame.get("ball", {})

        norm_ball = {
            "x": float(ball.get("x", 0.5) * self.pitch_length if ball.get("x", 0.0) <= 1.0 else ball.get("x", 0.0)),
            "y": float(ball.get("y", 0.5) * self.pitch_width if ball.get("y", 0.0) <= 1.0 else ball.get("y", 0.0)),
            "z": float(ball.get("z", 0.0)),
            "vx": float(ball.get("vx", 0.0)),
            "vy": float(ball.get("vy", 0.0)),
            "vz": float(ball.get("vz", 0.0)),
            "speed_kmh": float(ball.get("speed_kmh", 0.0)),
            "in_play": bool(ball.get("in_play", True))
        }

        norm_players = []
        for p in raw_frame.get("players", []):
            raw_x = p.get("x", 0.5)
            raw_y = p.get("y", 0.5)
            x_m = float(raw_x * self.pitch_length if raw_x <= 1.0 else raw_x)
            y_m = float(raw_y * self.pitch_width if raw_y <= 1.0 else raw_y)

            norm_players.append({
                "id": str(p.get("id")),
                "team": str(p.get("team")),
                "x": x_m,
                "y": y_m,
                "z": float(p.get("z", 0.0)),
                "vx": float(p.get("vx", 0.0)),
                "vy": float(p.get("vy", 0.0))
            })

        return {
            "frame_id": frame_id,
            "match_time": str(raw_frame.get("match_time", "00:00")),
            "ball": norm_ball,
            "players": norm_players
        }

    def load_json_match(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Loads match tracking JSON sequence and returns normalized frames.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Tracking file not found: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        frames = data.get("frames", data if isinstance(data, list) else [])
        return [self.parse_frame_dict(f) for f in frames]
