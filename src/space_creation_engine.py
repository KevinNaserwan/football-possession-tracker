"""
Off-Ball Space Creation & Passing Lane Permeability Engine.
Quantifies off-ball decoy runs, penetrative movements, and dynamic passing lane
permeability during active team possession spells.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np


class SpaceCreationEngine:
    """
    Evaluates off-ball player movements, passing lane permeability,
    and space generation for FC Barcelona and Athletic Club.
    """

    def __init__(
        self,
        pitch_length: float = 105.3,
        pitch_width: float = 68.0,
        fps: float = 25.0,
        high_intensity_speed_thresh: float = 4.5, # m/s (16.2 km/h)
        lane_clearance_thresh: float = 1.8         # meters of lane clearance
    ):
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width
        self.fps = fps
        self.run_thresh = high_intensity_speed_thresh
        self.lane_thresh = lane_clearance_thresh

    def analyze_space_creation(
        self,
        atd_data: List[Dict[str, Any]],
        possession_labels: np.ndarray
    ) -> Dict[str, Any]:
        """
        Analyzes off-ball runs and passing lane availability across the match.
        """
        n_frames = min(len(atd_data), len(possession_labels))

        barca_offball_runs = 0
        barca_open_lanes_count = 0
        barca_total_eval_lanes = 0

        athletic_offball_runs = 0
        athletic_open_lanes_count = 0
        athletic_total_eval_lanes = 0

        # Precompute positions in meters
        for i in range(1, n_frames):
            lbl = possession_labels[i]
            if lbl not in ("H", "A"):
                continue

            curr_frame = atd_data[i]
            prev_frame = atd_data[i - 1]

            bx = curr_frame.get("ball_x")
            by = curr_frame.get("ball_y")
            if bx is None or np.isnan(bx) or by is None or np.isnan(by):
                continue
            bx_m = bx * self.pitch_length
            by_m = by * self.pitch_width

            if lbl == "H":
                attackers = curr_frame.get("players_home", [])
                prev_att = prev_frame.get("players_home", [])
                defenders = curr_frame.get("players_away", [])
            else:
                attackers = curr_frame.get("players_away", [])
                prev_att = prev_frame.get("players_away", [])
                defenders = curr_frame.get("players_home", [])

            if len(attackers) < 2 or len(defenders) < 2:
                continue

            # Convert to meters
            att_m = [
                (p[0] * self.pitch_length, p[1] * self.pitch_width)
                for p in attackers if p[0] is not None and not np.isnan(p[0])
            ]
            prev_att_m = [
                (p[0] * self.pitch_length, p[1] * self.pitch_width)
                for p in prev_att if p[0] is not None and not np.isnan(p[0])
            ]
            def_m = [
                (p[0] * self.pitch_length, p[1] * self.pitch_width)
                for p in defenders if p[0] is not None and not np.isnan(p[0])
            ]

            if len(att_m) < 2 or len(def_m) < 2:
                continue

            # Find carrier (closest attacker to ball)
            dists_to_ball = [np.hypot(p[0] - bx_m, p[1] - by_m) for p in att_m]
            carrier_idx = int(np.argmin(dists_to_ball))
            c_pos = np.array(att_m[carrier_idx])

            # Evaluate each off-ball teammate
            for t_idx, t_pos in enumerate(att_m):
                if t_idx == carrier_idx:
                    continue

                # Speed calculation
                if t_idx < len(prev_att_m):
                    speed = np.hypot(
                        t_pos[0] - prev_att_m[t_idx][0],
                        t_pos[1] - prev_att_m[t_idx][1]
                    ) * self.fps
                    if speed >= self.run_thresh:
                        if lbl == "H":
                            barca_offball_runs += 1
                        else:
                            athletic_offball_runs += 1

                # Passing lane clearance check
                t_arr = np.array(t_pos)
                lane_vec = t_arr - c_pos
                lane_dist = np.linalg.norm(lane_vec)
                if lane_dist < 3.0:
                    continue

                lane_open = True
                for d_pos in def_m:
                    d_arr = np.array(d_pos)
                    # Project defender onto line segment
                    t_proj = np.dot(d_arr - c_pos, lane_vec) / (lane_dist ** 2 + 1e-5)
                    if 0.1 <= t_proj <= 0.9:
                        perp_dist = np.linalg.norm(d_arr - (c_pos + t_proj * lane_vec))
                        if perp_dist < self.lane_thresh:
                            lane_open = False
                            break

                if lbl == "H":
                    barca_total_eval_lanes += 1
                    if lane_open:
                        barca_open_lanes_count += 1
                else:
                    athletic_total_eval_lanes += 1
                    if lane_open:
                        athletic_open_lanes_count += 1

        return {
            "barca_high_intensity_runs_count": barca_offball_runs,
            "barca_passing_lane_permeability": float(barca_open_lanes_count / max(1, barca_total_eval_lanes)),
            "barca_total_evaluated_lanes": barca_total_eval_lanes,
            "athletic_high_intensity_runs_count": athletic_offball_runs,
            "athletic_passing_lane_permeability": float(athletic_open_lanes_count / max(1, athletic_total_eval_lanes)),
            "athletic_total_evaluated_lanes": athletic_total_eval_lanes
        }
