"""
Unit tests for Team Shape Analyzer and Space Creation Engine.
"""

import pytest
import numpy as np
from src.team_shape_analyzer import TeamShapeAnalyzer
from src.space_creation_engine import SpaceCreationEngine


def test_team_shape_convex_hull():
    analyzer = TeamShapeAnalyzer()
    
    # 4 corners of a box (0.2, 0.2) to (0.6, 0.8)
    coords = [(0.2, 0.2), (0.2, 0.8), (0.6, 0.8), (0.6, 0.2), (0.4, 0.5)]
    res = analyzer.compute_team_shape(coords)

    assert res["width"] > 0.0
    assert res["length"] > 0.0
    assert res["area_hull"] > 0.0
    assert res["stretch_index"] > 0.0
    # Expected area: length (0.4 * 105.3) * width (0.6 * 68) = 42.12 * 40.8 = 1718.5 m^2
    assert 1600.0 < res["area_hull"] < 1800.0


def test_space_creation_engine():
    engine = SpaceCreationEngine(fps=25.0)

    # 2 frames mock data
    labels = np.array(["H", "H"])
    atd_mock = [
        {
            "ball_x": 0.5,
            "ball_y": 0.5,
            "players_home": [(0.50, 0.50), (0.60, 0.50)], # Carrier and teammate
            "players_away": [(0.80, 0.80), (0.85, 0.85)]  # Defenders far away
        },
        {
            "ball_x": 0.5,
            "ball_y": 0.5,
            "players_home": [(0.50, 0.50), (0.65, 0.50)], # Teammate ran forward (speed > 4.5 m/s)
            "players_away": [(0.80, 0.80), (0.85, 0.85)]
        }
    ]

    res = engine.analyze_space_creation(atd_mock, labels)
    assert res["barca_high_intensity_runs_count"] >= 1
    assert res["barca_passing_lane_permeability"] == 1.0 # Unblocked lane
