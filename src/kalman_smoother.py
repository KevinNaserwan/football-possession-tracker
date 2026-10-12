import numpy as np
from typing import Tuple, Optional

class KalmanTrajectorySmoother:
    """
    Constant-Velocity Kalman Filter for tracking position (x, y) and velocity (vx, vy).
    Reduces camera optical jitter and smooths noisy bounding box centers
    for both players and the ball across consecutive frames.
    
    State vector: [x, y, vx, vy]^T
    Measurement vector: [x, y]^T
    """
    def __init__(
        self,
        dt: float = 0.04,          # 25 FPS (40ms per frame)
        process_noise_std: float = 0.15,
        measurement_noise_std: float = 0.35
    ):
        self.dt = dt
        
        # State transition matrix F
        self.F = np.array([
            [1.0, 0.0, dt,  0.0],
            [0.0, 1.0, 0.0, dt ],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=np.float64)

        # Measurement matrix H (we measure x and y)
        self.H = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0]
        ], dtype=np.float64)

        # Process noise covariance Q
        q = process_noise_std ** 2
        self.Q = np.array([
            [0.25 * (dt**4) * q, 0.0,                0.5 * (dt**3) * q, 0.0               ],
            [0.0,                0.25 * (dt**4) * q, 0.0,               0.5 * (dt**3) * q],
            [0.5 * (dt**3) * q,  0.0,                (dt**2) * q,       0.0               ],
            [0.0,                0.5 * (dt**3) * q,  0.0,               (dt**2) * q       ]
        ], dtype=np.float64)

        # Measurement noise covariance R
        r = measurement_noise_std ** 2
        self.R = np.array([
            [r,   0.0],
            [0.0, r  ]
        ], dtype=np.float64)

        # State vector x and estimation error covariance P
        self.x = np.zeros(4, dtype=np.float64)
        self.P = np.eye(4, dtype=np.float64) * 1.0
        self.initialized = False

    def reset(self, initial_x: float = 0.0, initial_y: float = 0.0):
        self.x = np.array([initial_x, initial_y, 0.0, 0.0], dtype=np.float64)
        self.P = np.eye(4, dtype=np.float64) * 1.0
        self.initialized = True

    def predict(self) -> Tuple[float, float, float, float]:
        """Project state ahead: x_k|k-1 = F * x_k-1|k-1"""
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self.x[0], self.x[1], self.x[2], self.x[3]

    def update(self, measured_x: float, measured_y: float) -> Tuple[float, float, float, float]:
        """Incorporate new measurement z = [x, y]^T and compute Kalman Gain"""
        if not self.initialized:
            self.reset(measured_x, measured_y)
            return self.x[0], self.x[1], self.x[2], self.x[3]

        # Prediction step
        self.predict()

        # Innovation / Measurement residual y = z - H * x
        z = np.array([measured_x, measured_y], dtype=np.float64)
        y = z - (self.H @ self.x)

        # Innovation covariance S = H * P * H^T + R
        S = self.H @ self.P @ self.H.T + self.R

        # Optimal Kalman gain K = P * H^T * S^-1
        K = self.P @ self.H.T @ np.linalg.inv(S)

        # Updated state estimate x = x + K * y
        self.x = self.x + (K @ y)

        # Updated error covariance P = (I - K * H) * P
        I = np.eye(4, dtype=np.float64)
        self.P = (I - (K @ self.H)) @ self.P

        return float(self.x[0]), float(self.x[1]), float(self.x[2]), float(self.x[3])
