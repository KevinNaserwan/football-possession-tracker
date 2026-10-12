import numpy as np
from typing import Dict, Any, Optional

class MarkovPossessionFilter:
    """
    Markov Temporal State Filter for Frame-by-Frame Ball Possession.
    Smooths high-frequency possession fluttering and flickering caused by
    noisy tracking data, deflections, or momentary physical proximity.

    State space:
      0: Home possession
      1: Away possession
      2: Contested / Loose ball
      3: Out of play
    """
    STATES = ["Home", "Away", "Contested", "out_of_play"]

    def __init__(
        self,
        inertia: float = 0.85,
        contested_damping: float = 0.70,
        switch_threshold: float = 0.65
    ):
        """
        inertia: Probability of remaining in the current possession state.
        contested_damping: Damping factor to prevent instant flips through loose ball states.
        switch_threshold: Confidence required to switch from active team to opposing team.
        """
        self.inertia = inertia
        self.contested_damping = contested_damping
        self.switch_threshold = switch_threshold

        self.current_team: Optional[str] = None
        self.consecutive_frames_in_state = 0
        self.history = []

    def reset(self):
        self.current_team = None
        self.consecutive_frames_in_state = 0
        self.history.clear()

    def update(self, raw_frame_estimate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applies Markov temporal filtering to the raw estimate.
        Returns smoothed possession state with adjusted confidence.
        """
        raw_team = raw_frame_estimate.get("possessing_team")
        raw_conf = raw_frame_estimate.get("confidence", 0.0)
        state_status = raw_frame_estimate.get("state", "controlled")

        if state_status == "out_of_play" or raw_team is None:
            self.current_team = None
            self.consecutive_frames_in_state = 0
            return {
                **raw_frame_estimate,
                "smoothed_team": None,
                "is_stable": True
            }

        # First frame initialization
        if self.current_team is None:
            self.current_team = raw_team
            self.consecutive_frames_in_state = 1
            return {
                **raw_frame_estimate,
                "smoothed_team": raw_team,
                "is_stable": False
            }

        # If raw estimate matches current state, strengthen inertia
        if raw_team == self.current_team:
            self.consecutive_frames_in_state += 1
            smoothed_conf = min(0.99, raw_conf * 0.4 + self.inertia * 0.6)
            smoothed_team = self.current_team
        else:
            # Candidate for turnover or loose ball transition
            if raw_team == "Contested":
                # Damped resistance: require multiple contested frames to drop team possession
                if self.consecutive_frames_in_state > 5:
                    smoothed_team = self.current_team
                    smoothed_conf = raw_conf * self.contested_damping
                else:
                    smoothed_team = "Contested"
                    smoothed_conf = raw_conf
                    self.current_team = "Contested"
                    self.consecutive_frames_in_state = 1
            else:
                # Direct switch to opposing team
                # Requires sufficient raw confidence or consecutive challenger frames
                if raw_conf >= self.switch_threshold:
                    self.current_team = raw_team
                    self.consecutive_frames_in_state = 1
                    smoothed_team = raw_team
                    smoothed_conf = raw_conf
                else:
                    # Suppress single-frame spike as tracking noise / anomaly
                    smoothed_team = self.current_team
                    smoothed_conf = self.inertia * 0.8

        result = {
            **raw_frame_estimate,
            "smoothed_team": smoothed_team,
            "consecutive_frames": self.consecutive_frames_in_state,
            "is_stable": self.consecutive_frames_in_state >= 3
        }

        self.history.append(smoothed_team)
        return result
