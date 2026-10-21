"""
Unit tests for Pass Detection Engine.
"""

from src.pass_detection_engine import PassDetectionEngine


def test_pass_engine_initialization():
    pde = PassDetectionEngine(min_pass_speed=4.5, control_radius=2.0)
    assert pde.min_pass_speed == 4.5
    assert pde.control_radius == 2.0
