
# Auto-generated incremental update
import pytest
from src.time_to_intercept import compute_intercept_time

def test_intercept():
    t = compute_intercept_time([0, 0], [10, 0], max_speed=5.0)
    assert abs(t - 2.0) < 1e-4


# Auto-generated incremental update
import pytest
from src.time_to_intercept import compute_intercept_time

def test_intercept():
    t = compute_intercept_time([0, 0], [10, 0], max_speed=5.0)
    assert abs(t - 2.0) < 1e-4

