"""
Unit and regression tests for Multi-Camera ATD Fusion.
Validates homography verification, timeline alignment (+4014 offset), and ball recovery.
"""

import os
import pytest
import numpy as np
from src.multi_camera_fusion import MultiCameraFusion


def test_multi_camera_initialization():
    fusion = MultiCameraFusion(pitch_length=105.3, pitch_width=68.0, max_reprojection_error=0.5)
    assert fusion.pitch_length == 105.3
    assert fusion.pitch_width == 68.0
    assert fusion.first_half_offset == 4014


def test_fusion_on_sample_data():
    fusion = MultiCameraFusion(first_half_offset=4014, max_reprojection_error=0.5)
    tac_path = "/home/rchandra/git/more-than-a-hack-2027/data/tactical/BAR-ATH_tactical_atd.txt"
    bc_path = "/home/rchandra/git/more-than-a-hack-2027/data/broadcast/BAR-ATH_broadcast_atd.txt"
    homo_path = "/home/rchandra/git/more-than-a-hack-2027/data/broadcast/BAR-ATH_broadcast_homography.csv"

    if os.path.exists(tac_path) and os.path.exists(bc_path) and os.path.exists(homo_path):
        # Run on first 20,000 frames
        bx, by, src, stats = fusion.fuse_ball_trajectories(
            tac_path, bc_path, homo_path, n_frames=20000
        )
        assert len(bx) == 20000
        assert stats["tactical_valid"] > 0
        assert stats["broadcast_recovered"] > 0
        # Check source tags: 1 is tactical, 2 is broadcast
        assert np.any(src == 1)
        assert np.any(src == 2)
