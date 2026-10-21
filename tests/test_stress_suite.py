"""
Unit and regression tests for Robustness Stress-Testing Suite (Option C).
Validates model stability under synthetic occlusion bursts.
"""

import os
import pytest
import numpy as np
import pandas as pd
from src.stress_test_suite import RobustnessStressTester


def test_stress_tester_initialization():
    tester = RobustnessStressTester()
    assert tester.random_seed == 42


def test_occlusion_injection():
    tester = RobustnessStressTester()
    labels = np.array(["H"] * 1000)
    corrupted = tester.inject_burst_occlusion(labels, burst_length=20, n_bursts=2, target_range=(0, 999))
    assert len(corrupted) == 1000
    assert np.sum(corrupted == "D") >= 20


def test_stress_sweep_on_public_ground_truth():
    gt_path = "/home/rchandra/git/more-than-a-hack-2027/evaluation/gt/BAR-ATH_possession_gt_public.csv"
    if os.path.exists(gt_path):
        tester = RobustnessStressTester(gt_public_path=gt_path)
        base_df = pd.read_csv("/home/rchandra/git/football-possession-tracker/LM10.csv")
        base_labels = base_df["label"].values

        df_res = tester.run_dropout_stress_sweep(base_labels, burst_lengths=[10, 25])
        assert len(df_res) == 3
        # Ensure spellF1 remains well above baseline floor (0.2433) even with injected noise
        assert (df_res["spellF1"] > 0.70).all()
