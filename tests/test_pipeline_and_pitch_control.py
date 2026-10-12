import unittest
import numpy as np
from src.pitch_control import PitchControlEngine
from src.markov_filter import MarkovPossessionFilter
from src.pipeline import FullPossessionPipeline

class TestPitchControlAndMarkovFilter(unittest.TestCase):
    def setUp(self):
        self.pc_engine = PitchControlEngine(grid_cells_x=20, grid_cells_y=15)
        self.markov_filter = MarkovPossessionFilter(inertia=0.85, switch_threshold=0.60)
        self.pipeline = FullPossessionPipeline(proximity_threshold=2.0)

    def test_pitch_control_equal_teams(self):
        # Two teams stationed symmetrically on both halves
        home = [
            {"id": "H1", "team": "Home", "x": 25.0, "y": 34.0, "vx": 0.0, "vy": 0.0},
            {"id": "H2", "team": "Home", "x": 35.0, "y": 20.0, "vx": 0.0, "vy": 0.0},
        ]
        away = [
            {"id": "A1", "team": "Away", "x": 80.0, "y": 34.0, "vx": 0.0, "vy": 0.0},
            {"id": "A2", "team": "Away", "x": 70.0, "y": 20.0, "vx": 0.0, "vy": 0.0},
        ]

        res = self.pc_engine.calculate_pitch_control_surface(home, away)
        self.assertIn("home_surface", res)
        self.assertIn("away_surface", res)
        self.assertAlmostEqual(res["home_pct"] + res["away_pct"], 100.0, places=2)
        # Symmetrical setup should result in near 50-50 total territory
        self.assertGreater(res["home_pct"], 40.0)
        self.assertLess(res["home_pct"], 60.0)

    def test_markov_smoothing_flicker_suppression(self):
        # Continuous Home possession followed by a single noisy glitch frame
        f1 = {"frame_id": 1, "possessing_team": "Home", "confidence": 0.9, "state": "controlled"}
        f2 = {"frame_id": 2, "possessing_team": "Home", "confidence": 0.9, "state": "controlled"}
        f3 = {"frame_id": 3, "possessing_team": "Home", "confidence": 0.9, "state": "controlled"}
        f4 = {"frame_id": 4, "possessing_team": "Away", "confidence": 0.3, "state": "controlled"} # Anomaly
        f5 = {"frame_id": 5, "possessing_team": "Home", "confidence": 0.9, "state": "controlled"}

        self.markov_filter.reset()
        _ = self.markov_filter.update(f1)
        _ = self.markov_filter.update(f2)
        _ = self.markov_filter.update(f3)
        res4 = self.markov_filter.update(f4)
        res5 = self.markov_filter.update(f5)

        # Single frame glitch with low confidence should be suppressed to Home
        self.assertEqual(res4["smoothed_team"], "Home")
        self.assertEqual(res5["smoothed_team"], "Home")

    def test_full_pipeline_execution(self):
        frame = {
            "frame_id": 100,
            "ball": {"x": 52.5, "y": 34.0, "vx": 1.2, "vy": 0.0, "in_play": True},
            "players": [
                {"id": "H10", "team": "Home", "x": 53.0, "y": 34.0, "vx": 1.0, "vy": 0.0},
                {"id": "A4", "team": "Away", "x": 58.0, "y": 34.0, "vx": -1.0, "vy": 0.0}
            ]
        }

        output = self.pipeline.process_frame(frame)
        self.assertEqual(output["frame_id"], 100)
        self.assertEqual(output["smoothed_team"], "Home")
        self.assertEqual(output["possessing_player"], "H10")
        self.assertIn("home_pitch_control_pct", output)
        self.assertIn("away_pitch_control_pct", output)

if __name__ == "__main__":
    unittest.main()
