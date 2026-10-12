import unittest
import numpy as np
from src.kalman_smoother import KalmanTrajectorySmoother
from src.metrica_parser import MetricaTrackingParser

class TestKalmanAndMetricaParser(unittest.TestCase):
    def test_kalman_smoother_noise_reduction(self):
        smoother = KalmanTrajectorySmoother(dt=0.04)
        true_x, true_y = 50.0, 30.0
        
        # Add noisy measurements
        noisy_measurements = [
            (true_x + 1.5, true_y - 1.2),
            (true_x - 1.0, true_y + 1.0),
            (true_x + 0.8, true_y - 0.5),
            (true_x - 0.4, true_y + 0.3),
            (true_x + 0.1, true_y - 0.2)
        ]

        smoothed_positions = []
        for mx, my in noisy_measurements:
            sx, sy, _, _ = smoother.update(mx, my)
            smoothed_positions.append((sx, sy))

        final_sx, final_sy = smoothed_positions[-1]
        # Kalman filter should converge closely to true position
        self.assertAlmostEqual(final_sx, true_x, delta=0.7)
        self.assertAlmostEqual(final_sy, true_y, delta=0.7)

    def test_metrica_parser_coordinate_normalization(self):
        parser = MetricaTrackingParser(pitch_length=105.0, pitch_width=68.0)
        raw_frame = {
            "frame_id": 1,
            "ball": {"x": 0.5, "y": 0.5, "vx": 0.0, "vy": 0.0, "in_play": True},
            "players": [
                {"id": "P1", "team": "Home", "x": 0.2, "y": 0.8, "vx": 0.0, "vy": 0.0}
            ]
        }

        parsed = parser.parse_frame_dict(raw_frame)
        self.assertAlmostEqual(parsed["ball"]["x"], 52.5, places=1)
        self.assertAlmostEqual(parsed["ball"]["y"], 34.0, places=1)
        self.assertAlmostEqual(parsed["players"][0]["x"], 21.0, places=1)
        self.assertAlmostEqual(parsed["players"][0]["y"], 54.4, places=1)

if __name__ == "__main__":
    unittest.main()
