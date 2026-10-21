"""
Unit tests for Expected Possession Value (EPV) & Counter-Press Latency engines.
"""

import pytest
import numpy as np
from src.epv_threat_engine import ExpectedPossessionValueEngine
from src.counter_press_engine import CounterPressEngine


def test_epv_threat_engine_bounds():
    engine = ExpectedPossessionValueEngine()
    
    # Check threat at goal center vs midfield
    threat_goal_mouth = engine.evaluate_ball_threat(1.0, 0.5, attacking_team="H", half=1)
    threat_midfield = engine.evaluate_ball_threat(0.5, 0.5, attacking_team="H", half=1)
    threat_own_box = engine.evaluate_ball_threat(0.1, 0.5, attacking_team="H", half=1)

    assert threat_goal_mouth > threat_midfield > threat_own_box
    assert 0.0 <= threat_goal_mouth <= 1.0
    assert 0.0 <= threat_midfield <= 1.0


def test_epv_sequence_evaluation():
    engine = ExpectedPossessionValueEngine()
    
    # 100 frames progressing towards goal
    x_coords = np.linspace(0.4, 0.95, 100)
    y_coords = np.full(100, 0.5)
    ball_coords = np.stack([x_coords, y_coords], axis=-1)
    possession_labels = np.array(["H"] * 100)

    res = engine.compute_epv_sequence(ball_coords, possession_labels, half=1)
    assert res["total_active_threat_frames"] == 100
    assert res["mean_threat_home"] > 0.1
    assert res["max_threat_home"] >= res["mean_threat_home"]
    assert len(res["epv_array"]) == 100


def test_counter_press_engine():
    engine = CounterPressEngine(fps=25.0, press_distance_threshold=2.0)
    
    labels = np.array(["H", "H", "A", "A", "A", "H", "H"])
    
    # Mock atd data
    mock_atd = []
    for i in range(len(labels)):
        mock_atd.append({
            "ball_x": 0.5,
            "ball_y": 0.5,
            "players_home": [(0.51, 0.51)], # ~1.5m away -> within 2.0m
            "players_away": [(0.80, 0.80)]
        })

    res = engine.analyze_turnovers(labels, mock_atd)
    assert res["total_turnovers"] == 2
    assert res["turnovers_h_to_a"] == 1
    assert res["turnovers_a_to_h"] == 1
    assert res["barca_mean_press_latency_sec"] >= 0.0
