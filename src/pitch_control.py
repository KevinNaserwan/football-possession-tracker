
# Auto-generated incremental update
import numpy as np

def calculate_reaction_time_vector(vx, vy, reaction_s=0.7):
    return np.array([vx * reaction_s, vy * reaction_s])

