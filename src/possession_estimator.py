import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

class PossessionEstimator:
    """
    Estimates team ball possession for each frame of a football match
    based on spatial proximity, velocity vectors, and pitch control.
    """
    def __init__(self, proximity_threshold: float = 2.0):
        self.proximity_threshold = proximity_threshold

    def estimate_frame(self, frame_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates controlling team and player for a given frame.
        frame_data: {
            'frame_id': int,
            'ball': {'x': float, 'y': float, 'vx': float, 'vy': float, 'in_play': bool},
            'players': [{'id': str, 'team': str, 'x': float, 'y': float, 'vx': float, 'vy': float}, ...]
        }
        """
        ball = frame_data.get('ball')
        players = frame_data.get('players', [])

        if not ball or not ball.get('in_play', True) or len(players) == 0:
            return {
                'frame_id': frame_data.get('frame_id'),
                'possessing_team': None,
                'possessing_player': None,
                'confidence': 0.0,
                'state': 'out_of_play'
            }

        ball_pos = np.array([ball['x'], ball['y']])

        # Calculate Euclidean distances from each player to the ball
        distances = []
        for p in players:
            p_pos = np.array([p['x'], p['y']])
            dist = np.linalg.norm(p_pos - ball_pos)
            distances.append((p, dist))

        distances.sort(key=lambda x: x[1])
        closest_player, min_distance = distances[0]

        if min_distance <= self.proximity_threshold:
            confidence = max(0.5, 1.0 - (min_distance / self.proximity_threshold))
            return {
                'frame_id': frame_data.get('frame_id'),
                'possessing_team': closest_player['team'],
                'possessing_player': closest_player['id'],
                'confidence': float(confidence),
                'state': 'controlled'
            }
        else:
            return {
                'frame_id': frame_data.get('frame_id'),
                'possessing_team': 'Contested',
                'possessing_player': None,
                'confidence': 0.2,
                'state': 'loose_ball'
            }
