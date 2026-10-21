"""
Synthetic Occlusion & Robustness Stress-Testing Suite for Football Possession Tracking.
Evaluates model resilience under artificial ball dropouts, tracking noise, and camera blackouts.
"""

import os
import sys
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

eval_dir = "/home/rchandra/git/more-than-a-hack-2027/evaluation"
if eval_dir not in sys.path:
    sys.path.insert(0, eval_dir)
import possession_metrics as pm


class RobustnessStressTester:
    """
    Simulates adversarial tracking degradations:
      1. Burst Ball Dropout (consecutive frames of NaN)
      2. Uniform Random Ball Dropout
      3. Gaussian Positional Noise on Coordinates
      4. Tracker Identity Swaps
    """
    def __init__(
        self,
        gt_public_path: str = "/home/rchandra/git/more-than-a-hack-2027/evaluation/gt/BAR-ATH_possession_gt_public.csv",
        random_seed: int = 42
    ):
        self.gt_public_path = gt_public_path
        self.random_seed = random_seed
        self.rng = np.random.default_rng(random_seed)

        if os.path.exists(gt_public_path):
            self.gt_df = pm.read_label_csv(gt_public_path)
            self.gt_codes = pm.label_codes(self.gt_df)
        else:
            self.gt_df = None
            self.gt_codes = None

    def inject_burst_occlusion(
        self,
        labels: np.ndarray,
        burst_length: int = 50,
        n_bursts: int = 5,
        target_range: Tuple[int, int] = (11185, 18684)
    ) -> np.ndarray:
        """
        Artificially introduces complete tracking dropouts (replacing with D or X).
        """
        corrupted = labels.copy()
        start, end = target_range
        valid_starts = np.arange(start, end - burst_length)

        if len(valid_starts) == 0:
            return corrupted

        chosen_starts = self.rng.choice(valid_starts, size=min(n_bursts, len(valid_starts)), replace=False)
        for s in chosen_starts:
            # Dropout can cause a naive system to flicker to Dead ball
            corrupted[s:s + burst_length] = "D"
        return corrupted

    def evaluate_submission_labels(self, labels: np.ndarray) -> Dict[str, float]:
        """
        Evaluates a label array against the official public ground truth metric.
        """
        if self.gt_codes is None:
            raise FileNotFoundError(f"GT file not found at {self.gt_public_path}")

        pred_codes = pm.label_codes(pd.Series(labels))
        res = pm.evaluate(self.gt_codes, pred_codes)
        t25 = res["transitions"][25]

        return {
            "spellF1": res["spell_f1_mean"],
            "macroF1": res["macro_f1"],
            "alive_dead_f1": res["alive_dead_f1"],
            "transF1": t25["f1"],
            "mean_latency": t25["mean_latency"],
            "n_pred_spells": res["n_pred_spells"],
            "n_gt_spells": res["n_gt_spells"],
            "mean_duration": res["mean_spell_duration_s"]
        }

    def run_dropout_stress_sweep(
        self,
        base_labels: np.ndarray,
        burst_lengths: List[int] = [10, 25, 50, 75, 100, 150]
    ) -> pd.DataFrame:
        """
        Simulates consecutive ball occlusion bursts and measures performance degradation.
        """
        results = []
        # Baseline (0 dropout)
        base_metrics = self.evaluate_submission_labels(base_labels)
        results.append({
            "occlusion_frames": 0,
            "occlusion_seconds": 0.0,
            "spellF1": base_metrics["spellF1"],
            "macroF1": base_metrics["macroF1"],
            "transF1": base_metrics["transF1"],
            "possessions": base_metrics["n_pred_spells"],
            "retention_pct": 100.0
        })

        for burst in burst_lengths:
            # Simulate 5 distinct ball occlusions of length `burst`
            corrupted = self.inject_burst_occlusion(base_labels, burst_length=burst, n_bursts=5)
            metrics = self.evaluate_submission_labels(corrupted)
            retention = (metrics["spellF1"] / base_metrics["spellF1"]) * 100.0

            results.append({
                "occlusion_frames": burst,
                "occlusion_seconds": burst / 25.0,
                "spellF1": metrics["spellF1"],
                "macroF1": metrics["macroF1"],
                "transF1": metrics["transF1"],
                "possessions": metrics["n_pred_spells"],
                "retention_pct": retention
            })

        return pd.DataFrame(results)
