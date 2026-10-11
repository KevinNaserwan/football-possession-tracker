import cv2
import numpy as np
from typing import Tuple, List

class PitchHomographyTransformer:
    """
    Transforms pixel coordinates from broadcast camera space into
    standard 2D pitch coordinates (105m x 68m) using planar homography.
    """
    def __init__(self, pitch_length: float = 105.0, pitch_width: float = 68.0):
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width
        self.homography_matrix = None

    def compute_homography(self, src_pts: np.ndarray, dst_pts: np.ndarray) -> np.ndarray:
        """
        Calculates homography matrix H using 4 or more corresponding landmark points.
        """
        if len(src_pts) < 4 or len(dst_pts) < 4:
            raise ValueError("At least 4 correspondence points are required for homography estimation.")
        
        H, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        self.homography_matrix = H
        return H

    def transform_points(self, points: np.ndarray) -> np.ndarray:
        """
        Transforms 2D points [N, 2] from camera pixel plane to pitch coordinates.
        """
        if self.homography_matrix is None:
            raise ValueError("Homography matrix has not been computed yet.")

        # Reshape to (N, 1, 2) for cv2.perspectiveTransform
        pts_reshaped = points.reshape(-1, 1, 2).astype(np.float32)
        transformed = cv2.perspectiveTransform(pts_reshaped, self.homography_matrix)
        return transformed.reshape(-1, 2)
