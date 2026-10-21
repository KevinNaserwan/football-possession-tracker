"""
Unit tests for 2D Pitch Control Field Analyzer.
"""

import numpy as np
from src.pitch_control_field import PitchControlFieldAnalyzer


def test_pitch_control_field_dimensions():
    analyzer = PitchControlFieldAnalyzer(grid_cells_x=16, grid_cells_y=10)
    home_p = np.array([[30.0, 34.0], [40.0, 20.0]])
    away_p = np.array([[70.0, 34.0], [60.0, 50.0]])

    p_surf, hp, ap = analyzer.compute_frame_control_surface(home_p, away_p)
    assert p_surf.shape == (10, 16)
    assert 0.0 <= hp <= 100.0
    assert 0.0 <= ap <= 100.0
    assert abs(hp + ap - 100.0) < 1e-4
