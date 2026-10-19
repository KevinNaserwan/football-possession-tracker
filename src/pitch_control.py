import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from scipy.special import expit

class PitchControlEngine:
    """
    Spearman-based Pitch Control Field & Transition Probability Model.
    Calculates the spatial surface of pitch control across a 105m x 68m pitch
    for two competing teams based on player velocity, reaction latency,
    and physical time-to-intercept.
    """
    def __init__(
        self,
        pitch_length: float = 105.0,
        pitch_width: float = 68.0,
        grid_cells_x: int = 50,
        grid_cells_y: int = 32,
        max_player_speed: float = 7.5,
        reaction_time: float = 0.7,
        lambda_intercept: float = 4.3
    ):
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width
        self.grid_cells_x = grid_cells_x
        self.grid_cells_y = grid_cells_y
        self.max_player_speed = max_player_speed
        self.reaction_time = reaction_time
        self.lambda_intercept = lambda_intercept

        # Precompute pitch spatial grid coordinates
        self.x_grid = np.linspace(0, pitch_length, grid_cells_x)
        self.y_grid = np.linspace(0, pitch_width, grid_cells_y)
        self.X, self.Y = np.meshgrid(self.x_grid, self.y_grid)
        self.grid_points = np.stack([self.X.ravel(), self.Y.ravel()], axis=1) # [N_points, 2]

    def compute_player_time_to_target(
        self,
        player_pos: np.ndarray,
        player_vel: np.ndarray,
        target_points: np.ndarray
    ) -> np.ndarray:
        """
        Calculates time required for a player to reach target points.
        Incorporates reaction time delay and directional momentum.
        """
        # Projected starting position after reaction time with current velocity
        r_react = player_pos + player_vel * self.reaction_time

        # Distance from reaction position to target points
        dist = np.linalg.norm(target_points - r_react, axis=1)

        # Total time = reaction time + time to cover remaining distance at max speed
        time_to_target = self.reaction_time + (dist / self.max_player_speed)
        return time_to_target

    def calculate_pitch_control_surface(
        self,
        home_players: List[Dict[str, Any]],
        away_players: List[Dict[str, Any]],
        ball_pos: Optional[Tuple[float, float]] = None
    ) -> Dict[str, Any]:
        """
        Computes 2D probability surface of pitch control for Home vs Away team.
        Returns:
            - home_control_surface: 2D array [grid_cells_y, grid_cells_x] in [0, 1]
            - away_control_surface: 2D array [grid_cells_y, grid_cells_x] in [0, 1]
            - home_total_control_pct: float (0.0 to 100.0)
            - away_total_control_pct: float (0.0 to 100.0)
        """
        if not home_players or not away_players:
            neutral = np.full((self.grid_cells_y, self.grid_cells_x), 0.5)
            return {
                "home_surface": neutral,
                "away_surface": neutral,
                "home_pct": 50.0,
                "away_pct": 50.0
            }

        # Vectorized computation of minimum time-to-intercept for Home team
        home_times = []
        for p in home_players:
            p_pos = np.array([p["x"], p["y"]])
            p_vel = np.array([p.get("vx", 0.0), p.get("vy", 0.0)])
            t = self.compute_player_time_to_target(p_pos, p_vel, self.grid_points)
            home_times.append(t)
        min_home_time = np.min(np.array(home_times), axis=0) # [N_points]

        # Vectorized computation of minimum time-to-intercept for Away team
        away_times = []
        for p in away_players:
            p_pos = np.array([p["x"], p["y"]])
            p_vel = np.array([p.get("vx", 0.0), p.get("vy", 0.0)])
            t = self.compute_player_time_to_target(p_pos, p_vel, self.grid_points)
            away_times.append(t)
        min_away_time = np.min(np.array(away_times), axis=0) # [N_points]

        # Delta t = time_away - time_home
        # If Home arrives faster, delta_t > 0 -> P(Home) > 0.5
        delta_t = min_away_time - min_home_time

        # Sigmoid probability surface
        home_prob = expit(self.lambda_intercept * delta_t)
        away_prob = 1.0 - home_prob

        # Reshape to grid matrix
        home_surface = home_prob.reshape((self.grid_cells_y, self.grid_cells_x))
        away_surface = away_prob.reshape((self.grid_cells_y, self.grid_cells_x))

        home_pct = float(np.mean(home_surface) * 100.0)
        away_pct = float(np.mean(away_surface) * 100.0)

        return {
            "home_surface": home_surface,
            "away_surface": away_surface,
            "home_pct": home_pct,
            "away_pct": away_pct
        }

# Auto-generated incremental update
import numpy as np

def calculate_reaction_time_vector(vx, vy, reaction_s=0.7):
    return np.array([vx * reaction_s, vy * reaction_s])


# Auto-generated incremental update
import numpy as np

def calculate_reaction_time_vector(vx, vy, reaction_s=0.7):
    return np.array([vx * reaction_s, vy * reaction_s])


# Auto-generated incremental update
import numpy as np

def calculate_reaction_time_vector(vx, vy, reaction_s=0.7):
    return np.array([vx * reaction_s, vy * reaction_s])

