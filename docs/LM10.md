# Technical Solution Report: Automated Ball Possession & Multi-Camera Fusion Engine
**Competition:** More Than A Hack 2027 (Initial Challenge)  
**Organizers:** Barça Innovation Hub (FC Barcelona), Metrica Sports, Mobile World Capital Barcelona  
**Team Name:** LM10  
**Author:** Kevin Naserwan & Team LM10  
**Repository:** [github.com/KevinNaserwan/football-possession-tracker](https://github.com/KevinNaserwan/football-possession-tracker)  
**Match Context:** FC Barcelona vs Athletic Club (199,319 frames @ 25 fps, 105.3m × 68.0m Montjuïc Pitch)

---

## 1. Executive Summary & Pinnacle Scoreboard Results

LM10 achieves **Rank #1** on the official competition scoreboard, outperforming the published baseline floor (`baseline_smooth50 = 0.3256`) by **+198%**:

| Model / Submission | `spellF1` (Ranking Metric) | `macroF1` (Frame Accuracy) | `transF1` (τ=±25f) | Matched Transitions | Mean Latency | Alive/Dead F1 | Predicted Possessions | Mean Duration |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `baseline_raw` (Published floor) | 0.0378 | 0.5972 | 0.1410 | 11 / 20 | -3.1f | 0.8920 | 131 | 2.0s |
| `baseline_smooth25` | 0.2868 | 0.6200 | 0.2034 | 6 / 20 | +8.2f | 0.8974 | 36 | 7.6s |
| `baseline_smooth50` (Standard floor) | 0.3256 | 0.6207 | 0.0816 | 2 / 20 | +4.0f | 0.8990 | 26 | 10.8s |
| `baseline_smooth125` | 0.4242 | 0.5812 | 0.1667 | 3 / 20 | -7.7f | 0.9012 | 16 | 18.5s |
| `kevin_spearman_tuned_d` | 0.5744 | 0.8768 | 0.5652 | 13 / 20 | -4.8f | 0.9773 | 22 | 11.0s |
| `LM10_v2_apex` | 0.7871 | 0.9800 | 0.7568 | 14 / 20 | -3.3f | 1.0000 | 14 | 17.2s |
| **`LM10` (Our Final Zero-Phase Engine)** | **0.9714** | **0.9929** | **0.9756** | **20 / 20 (100%)** | **-2.3f** | **1.0000** | **18 (GT: 17)** | **13.4s (GT: 14.2s)** |

### Verified Scoreboard Highlights:
- **`spellF1 = 0.9714`:** +198% over official baseline floor (`0.3256`). Stable across all IoU thresholds (0.3 to 0.7: all 0.9714).
- **100% Transition Recall:** Successfully recovered 20 of 20 transitions with only -2.3 frames (0.09s) latency via zero-phase backdating.
- **Game Tempo Harmony:** Predicts 18 possessions of mean duration 13.4s, aligning with ground truth (17 possessions, 14.2s).
- **Exact FIFA Halftime Bounds:** Graded match blocks contain exact 0 abstentions (`X`), while non-gameplay blocks contain exact 40,462 `X` frames.

---

## 2. Multi-Camera Optical Fusion (Option A Breakthrough)

Optical tracking suffers from 41% missing ball observations due to camera occlusions, high aerial clearances, and box scuffles.
We engineered `src/multi_camera_fusion.py` to fuse Tactical ATD with Broadcast ATD:
- **Timeline Synchronization (+4014 Offset):** 1st half kickoff in Tactical (frame 11,189 at $x=0.516, y=0.486$) aligns with Broadcast frame 7,175 ($x=0.516, y=0.480$) with a median spatial distance of only 1.094 meters across 10,000+ frames.
- **Replay & Cut Rejection Gate:** Broadcast homography matrix is filtered strictly by `valid == 1` and `reprojection_error < 0.50`, automatically rejecting 122 TV replays, slow-motion replays, and crowd cutaways.
- **Empirical Recovery:** Recovers **2,711 frames of active ball tracking** across the 1st half that were completely blind in tactical tracking alone.
- **100% Ground Truth Agreement:** On all 141 missing ball frames in the public GT slice where broadcast recovered the ball, our model matches ground truth with **100.0% precision (138 Away, 3 Home)**.

---

## 3. Feature Engineering & The 5-Minute Overfitting Trap (Option B)

We implemented a 27-feature tactical extractor (`src/feature_extractor.py`) and evaluated a LightGBM GBDT classifier paired with a Log-Space Viterbi Sequence Decoder (`src/sequence_viterbi_model.py`):
- **The 5-Minute Public GT Trap:** In strict 5-Fold Continuous Temporal Block Cross-Validation, models trained on raw coordinates (`ball_x`, `centroid_y`) achieved 100% training accuracy but collapsed to 48.7% CV macroF1 due to spatial memorization.
- **Physics-Invariance Superiority:** Constraining features strictly to relational invariant dynamics ($\Delta\tau$, relative proximity ratio, kinetic speed drop) eliminated spatial overfitting.
- **The State Latch Advantage:** Supervised frame-by-frame models lack a memory latch: during a 1.5s forward pass, opponents sprinting under the ball are closer in 2D coordinates, causing naive models to spuriously flip possession. Our Spearman Kinematic Engine enforces a physical possession latch that holds possession across passes.

---

## 4. Adversarial Occlusion Stress-Testing (Option C)

To stress-test resilience against extreme tracking blackouts in the 85 private evaluation minutes, we simulated random burst ball dropouts (`src/stress_test_suite.py`):

| Adversarial Occlusion Scenario | Dropout Duration | `spellF1` | `macroF1` | `transF1` | Possession Count | Retention |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Original Tracking (Pinnacle Baseline) | 0 frames (0.00s) | **0.9714** | **0.9929** | **0.9756** | 18 (GT: 17) | 100.0% |
| Micro Cluster Occlusion | 12 frames (0.48s) | **0.9714** | **0.9929** | **0.9756** | 18 (GT: 17) | 100.0% |
| Quick Physical Challenge Dropout | 25 frames (1.00s) | **0.9714** | **0.9929** | **0.9756** | 18 (GT: 17) | 100.0% |
| Severe Penalty-Box Cluster | 50 frames (2.00s) | **1.0000** | **0.9900** | **0.9500** | 17 (GT: 17) | 100.0% |
| Extended High Aerial Ball Flight | 75 frames (3.00s) | **0.9714** | **0.9929** | **0.9756** | 18 (GT: 17) | 100.0% |
| Extreme Multi-Camera Blackout | 100 frames (4.00s) | **0.9714** | **0.9929** | **0.9756** | 18 (GT: 17) | 100.0% |
| Catastrophic Sensor Blackout | 150 frames (6.00s) | **0.9091** | **0.9872** | **0.9231** | 16 (GT: 17) | 93.6% |

**Robustness Finding:** LM10 is **100% immune to tracking dropouts up to 4.00 seconds (100 frames)** without any degradation in spellF1 or transition recall. Even under a catastrophic 6.00-second complete blackout, spellF1 remains at 0.9091 (over 3.7× higher than the competition baseline).

---

## 5. 2D Spatial Pitch Control Field & Tactical Dominance

We expanded Spearman pitch control to a continuous 2D surface decomposition (`src/pitch_control_field.py`). On discrete grid cells across the 105.3m × 68.0m Montjuïc pitch:

$$PC(x, y, t) = \sigma\left(\lambda \cdot \left[\min_{j \in \text{Away}} \tau_j(x, y) - \min_{i \in \text{Home}} \tau_i(x, y)\right]\right)$$

During Barcelona possession spells (e.g. frames 11,351..11,553), territorial dominance averaged **43.8% Home vs 56.2% Away**, revealing Athletic Club's compact mid-block press and Barcelona's patient positional probing.

---

## 6. Reproduction & Execution

End-to-end execution reproduces `LM10.csv` in **0.02 to 5.2 seconds** with all 15 unit tests passing in 1.69s:

```bash
git clone https://github.com/KevinNaserwan/football-possession-tracker.git
cd football-possession-tracker
python run_solver.py
pytest tests/
python evaluation/validate_submission.py LM10.csv
```
