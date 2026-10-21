"""
Hidden Markov Model (HMM) Viterbi Sequence Decoder & LightGBM Sequence Classifier.
Option B: Advanced Feature-Based Sequence Modeling for Metrica Sports Possession Tracking.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import f1_score


class ViterbiSequenceDecoder:
    """
    Log-space Viterbi Sequence Decoder for temporal possession smoothing.
    Guarantees mathematically optimal state trajectories under physical dwell-time priors.
    States: 0: Home (H), 1: Away (A), 2: Dead Ball (D)
    """
    def __init__(
        self,
        mean_possession_seconds: float = 13.5,
        mean_stoppage_seconds: float = 25.0,
        fps: float = 25.0,
        turnover_penalty: float = 2.0
    ):
        self.fps = fps
        self.n_states = 3
        self.label_map = {0: "H", 1: "A", 2: "D"}
        self.inv_label_map = {"H": 0, "A": 1, "D": 2}

        # Calculate self-transition probabilities from physical durations
        dur_poss_frames = mean_possession_seconds * fps
        dur_stop_frames = mean_stoppage_seconds * fps

        p_stay_poss = max(0.990, 1.0 - (1.0 / dur_poss_frames))
        p_stay_stop = max(0.990, 1.0 - (1.0 / dur_stop_frames))

        p_leave_poss = 1.0 - p_stay_poss
        p_leave_stop = 1.0 - p_stay_stop

        # Transition matrix A: rows = from_state, cols = to_state
        # Turnovers (H <-> A) are rarer than transitions to Dead ball (foul/whistle)
        p_ha = (p_leave_poss / 3.0) / turnover_penalty
        p_hd = p_leave_poss - p_ha

        p_ah = (p_leave_poss / 3.0) / turnover_penalty
        p_ad = p_leave_poss - p_ah

        p_dh = p_leave_stop / 2.0
        p_da = p_leave_stop / 2.0

        A = np.array([
            [p_stay_poss, p_ha, p_hd],
            [p_ah, p_stay_poss, p_ad],
            [p_dh, p_da, p_stay_stop]
        ], dtype=np.float64)

        # Normalize rows
        A = A / A.sum(axis=1, keepdims=True)
        self.log_A = np.log(A)

    def decode(
        self,
        emission_probs: np.ndarray,
        initial_probs: Optional[np.ndarray] = None
    ) -> List[str]:
        """
        Executes log-space Viterbi dynamic programming.
        emission_probs: (T, 3) matrix of [P(H), P(A), P(D)]
        """
        T = len(emission_probs)
        if T == 0:
            return []

        # Avoid log(0)
        eps = 1e-12
        log_B = np.log(np.clip(emission_probs, eps, 1.0))

        if initial_probs is None:
            initial_probs = np.array([1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0])  # Uniform prior
        log_pi = np.log(np.clip(initial_probs, eps, 1.0))

        # DP tables
        V = np.zeros((T, self.n_states), dtype=np.float64)
        backtrack = np.zeros((T, self.n_states), dtype=np.int32)

        # Base case
        V[0] = log_pi + log_B[0]

        # Forward trellis
        for t in range(1, T):
            for j in range(self.n_states):
                # V[t-1] + log_A[:, j]
                candidates = V[t - 1] + self.log_A[:, j]
                best_prev = np.argmax(candidates)
                V[t, j] = candidates[best_prev] + log_B[t, j]
                backtrack[t, j] = best_prev

        # Backtrack
        best_last = np.argmax(V[-1])
        path = [best_last]
        for t in range(T - 1, 0, -1):
            prev_state = backtrack[t, path[-1]]
            path.append(prev_state)

        path.reverse()
        return [self.label_map[s] for s in path]


class LightGBMPossessionClassifier:
    """
    Supervised LightGBM Sequence Classifier with probabilistic calibration.
    """
    def __init__(self, n_estimators: int = 150, learning_rate: float = 0.05):
        self.model = lgb.LGBMClassifier(
            objective="multiclass",
            num_class=3,
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            num_leaves=31,
            max_depth=6,
            min_child_samples=20,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbose=-1
        )
        self.feature_cols: List[str] = []
        self.label_to_id = {"H": 0, "A": 1, "D": 2}
        self.id_to_label = {0: "H", 1: "A", 2: "D"}

    def fit(self, X: pd.DataFrame, y: pd.Series):
        exclude_cols = ["frame", "label"]
        self.feature_cols = [c for c in X.columns if c not in exclude_cols]
        y_encoded = y.map(self.label_to_id).values
        self.model.fit(X[self.feature_cols], y_encoded)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.predict_proba(X[self.feature_cols])

    def feature_importances(self) -> pd.DataFrame:
        return pd.DataFrame({
            "feature": self.feature_cols,
            "importance": self.model.feature_importances_
        }).sort_values(by="importance", ascending=False)
