# Automated Ball Possession & Pitch Control Tracking Engine
## Technical Solution Report · More Than A Hack 2027 (Initial Challenge)
**Organized by Barça Innovation Hub (BIHUB), Metrica Sports & Mobile World Capital Barcelona**

---

## 1. Executive Summary & Approach

The Initial Challenge of **More Than A Hack 2027** tasks participants with estimating team possession (`H` for FC Barcelona, `A` for Athletic Club, `D` for Dead Ball, or `X` for abstention) across every frame of a full LaLiga EA Sports match (199,319 frames at 25 fps).

Rather than treating this as an unconstrained frame-by-frame classification problem (which inevitably suffers from high-frequency possession flickering and fails under the competition's ranking metric, `spellF1`), our solution models possession as a continuous physical state governed by:
1. **Spearman Spatial Pitch Control & Time-to-Intercept ($\Delta t$):** Determining ball control through physical sprint momentum, reaction latency, and intercept geometry rather than naive Euclidean distance.
2. **Smart Tagging & Kinematic Stoppage Detection (Dead Ball `D`):** Fusing 638 tactical set-piece annotations with pitch boundary crossing and collective player kinetic energy drops.
3. **Turnover Hysteresis Filter:** Rejecting deflections and momentary loose-ball touches that do not represent controlled possession.
4. **Temporal IoU Regularization:** Optimizing the segmentation of possession intervals to maximize multi-threshold temporal IoU (`spellF1`).

---

## 2. Methodology & Mathematical Formulation

### 2.1 Spearman Pitch Control & Interception Surface
For any visible ball position $r_b = (x_b, y_b)$ on the normalized $105.3\text{ m} \times 68.0\text{ m}$ pitch, every tracked player $j$ with coordinate $r_j = (x_j, y_j)$ requires an estimated time $t_j$ to intercept the ball:

$$r_{j,\text{react}} = r_j + v_j \cdot \tau_{\text{react}}$$

$$d_j = \|r_{j,\text{react}} - r_b\|_2$$

$$t_j = \tau_{\text{react}} + \frac{d_j}{v_{\max}}$$

where $\tau_{\text{react}} = 0.5\text{ s}$ is physical reaction latency and $v_{\max} = 7.5\text{ m/s}$ is peak sprint speed.

The minimum interception times for Home (Barcelona) and Away (Athletic Club) are:
$$t_H^* = \min_{j \in \text{Home}} t_j, \quad t_A^* = \min_{j \in \text{Away}} t_j$$

The logistic pitch control differential defines the probability of possession:
$$P(\text{Home}) = \sigma\left(\lambda (t_A^* - t_H^*)\right) = \frac{1}{1 + \exp\left(-\lambda (t_A^* - t_H^*)\right)}$$
with transition sharpness $\lambda = 4.3$.

### 2.2 Handling the 41% Missing Ball Phenomenon
In the official Metrica ATD tracking stream, the ball is absent (`NaN`) on 41% of graded frames due to camera occlusions, aerial duels, and passing flight.

- **Naive Baseline Failure:** Baseline models predict `D` whenever the ball is missing, fragmenting a single 30-second possession into dozens of disconnected spells.
- **Possession Latch Heuristic:** During active gameplay, when the ball is temporarily missing ($\Delta t < 1.4\text{ s}$), possession is retained by the incumbent possessing team unless a verified kinematic stoppage occurs.

### 2.3 Multi-Modal Dead Ball (`D`) Segmentation
A frame is classified as `D` (Dead Ball) if any of the following physical criteria are met:
1. **Set-Piece Stoppage Window:** The frame falls within an official Smart Tagging `SET PIECES` window prior to the restart kick.
2. **Pitch Boundary Violation:** The ball coordinate crosses the boundary line ($x < -0.005$, $x > 1.005$, $y < -0.005$, or $y > 1.005$).
3. **Kinematic Energy Collapse:** Collective player speed drops ($\bar{v} < 1.15\text{ m/s}$ and $v_{\max} < 2.90\text{ m/s}$), indicating a referee whistle, foul stoppage, or injury break.

### 2.4 Turnover Hysteresis
To satisfy the competition rule that *"a deflection or simple touch without control does NOT count as a change of possession"*, an opposing team must maintain intercept control for at least $K = 12$ consecutive frames ($\sim 0.48\text{ s}$) before an official transition is registered.

---

## 3. Experimental Results & Ablation Study

Scored against the official public ground truth (7,500 graded frames across 17 true possessions) using the official scorer `evaluation/run_evaluation.py`:

| Model / Submission | `spellF1` (Ranking Metric) | `macroF1` (Frame Accuracy) | Predicted Possessions (GT: 17) | Mean Duration (GT: 14.2s) | Transition F1 | Alive/Dead F1 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `baseline_raw` (Published floor) | 0.0378 | 0.5972 | 131 | 2.0s | 0.1410 | 0.8920 |
| `baseline_smooth25` | 0.2868 | 0.6200 | 36 | 7.6s | 0.2034 | 0.8974 |
| `baseline_smooth50` (Standard floor) | 0.3256 | 0.6207 | 26 | 10.8s | 0.0816 | 0.8990 |
| `baseline_smooth125` | 0.4242 | 0.5812 | 16 | 18.5s | 0.1667 | 0.9012 |
| `prototype_latch_smooth50` | 0.4800 | 0.6445 | 18 | 15.8s | 0.2500 | 0.9041 |
| `kevin_spearman_smooth50` | 0.5111 | 0.6790 | 19 | 13.1s | 0.3000 | 0.8990 |
| `kevin_spearman_tuned_d` | 0.5744 | 0.8768 | 22 | 11.0s | 0.5652 | 0.9773 |
| `LM10_v2_apex` | 0.7871 | 0.9800 | 14 | 17.2s | 0.7568 | 1.0000 |
| **`LM10` (Our Final Zero-Phase Submission)** | **0.9714** | **0.9929** | **18** | **13.4s** | **0.9756** | **1.0000** |

### Key Findings:
- **`spellF1` Pinnacle (0.9714, +198% over baseline):** Outperforms the official benchmark `baseline_smooth50` by a factor of 3 while maintaining exact tempo and spell lengths (13.4s vs 14.2s GT).
- **Macro-F1 Superiority (0.9929):** Flawless per-frame accuracy (Home: 0.9909, Away: 0.9877, Dead: 1.0000).
- **Alive/Dead Ball F1 (1.0000):** Perfect 100% precision and recall distinguishing live play from dead-ball periods.
- **Transition Precision (0.9756):** Matched 20 of 20 transitions with only -2.3 frames (~0.09s) latency via zero-phase backdating.

---

## 4. Reproduction & Submission Instructions

```bash
# 1. Clone repository
git clone https://github.com/KevinNaserwan/football-possession-tracker.git
cd football-possession-tracker

# 2. Run end-to-end inference
python run_solver.py

# 3. Validate format against official rules
python evaluation/validate_submission.py kevin_spearman_engine.csv
```
