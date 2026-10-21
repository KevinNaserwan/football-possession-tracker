"""
Unit tests for Feature Extractor and Viterbi Sequence Decoder (Option B).
"""

import os
import pytest
import numpy as np
import pandas as pd
from src.feature_extractor import TacticalFeatureExtractor
from src.sequence_viterbi_model import ViterbiSequenceDecoder, LightGBMPossessionClassifier


def test_viterbi_decoder_synthetic():
    decoder = ViterbiSequenceDecoder(mean_possession_seconds=5.0, fps=25.0)

    # Synthetic probabilities: 50 frames of H, 10 frames of noisy flicker, 50 frames of A
    T = 110
    probs = np.zeros((T, 3))
    probs[:50] = [0.8, 0.1, 0.1]
    # In middle, noisy 2-frame flicker towards A
    probs[50:52] = [0.3, 0.6, 0.1]
    probs[52:60] = [0.8, 0.1, 0.1]
    probs[60:] = [0.1, 0.8, 0.1]

    path = decoder.decode(probs)
    assert len(path) == T
    # Viterbi should suppress the 2-frame flicker due to transition penalty
    assert path[50] == "H"
    assert path[51] == "H"
    assert path[0] == "H"
    assert path[-1] == "A"


def test_feature_extractor_initialization():
    fe = TacticalFeatureExtractor(pitch_length=105.3, pitch_width=68.0)
    assert fe.pitch_length == 105.3
    assert fe.pitch_width == 68.0
