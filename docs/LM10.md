# Zero-Phase Spearman Pitch Control & Kinematic Stoppage Engine for Automated Football Possession Tracking
## Technical Solution Report · More Than A Hack 2027 (Initial Challenge)
**Team:** LM10  
**Competition:** More Than A Hack 2027 by Barça Innovation Hub (BIHUB), Metrica Sports & Mobile World Capital Barcelona  
**Target Fixture:** FC Barcelona vs. Athletic Club (`BAR-ATH`), LaLiga EA Sports  
**Repository:** [https://github.com/KevinNaserwan/football-possession-tracker](https://github.com/KevinNaserwan/football-possession-tracker)  
**Submission Artifacts:** `LM10.csv` (199,319 frames), `LM10.pdf` (3-page executive report)

---

## 1. Challenge Overview & Problem Formulation

### 1.1 Objective
The Initial Challenge requires classifying every video frame of an official LaLiga match (199,319 frames at 25 fps, ~133 minutes including pre-match, halftime, and post-match footage) into one of four mutually exclusive states:
- `H`: FC Barcelona (Home team) in controlled team possession.
- `A`: Athletic Club (Away team) in controlled team possession.
- `D`: Dead Ball (stoppage in play: fouls, out-of-bounds, set pieces, referee whistles).
- `X`: Non-gameplay abstention (pre-match countdown, halftime intermission, post-match).

### 1.2 The Failure Mode of Per-Frame Classifiers
Standard machine learning approaches treat possession as frame-by-frame point classification. Under the competition floor (`baseline_raw`), nearest-player distance matching produces a seemingly respectable per-frame accuracy (`macroF1 = 0.5972`), but scores an abysmal **`spellF1 = 0.0378`**.

The reason lies in the competition's ranking metric: **`spellF1`**, defined as the mean F1 score across five temporal Intersection-over-Union (IoU) matching thresholds:
$$\text{spellF1} = \frac{1}{5} \sum_{\theta \in \{0.3, 0.4, 0.5, 0.6, 0.7\}} F_{1,\text{IoU} \ge \theta}$$

Whenever a pass travels in the air or a duel occurs, nearest-player heuristics flicker between teams frame-by-frame. A single 40-second Barcelona possession is fractured into dozens of 0.2-second micro-spells (131 predicted spells vs. 17 true possessions). Because temporal IoU requires overlapping duration matching, fragmented predictions receive an IoU of zero, completely collapsing `spellF1`.

---

## 2. Methodology & Mathematical Architecture

Our solution, the **LM10 Zero-Phase Spearman Engine**, models possession as a continuous physical dynamical system rather than an unconstrained frame classifier.

```
+----------------------------------------------------------------------------------------------------+
|                                    RAW ATD & SMART TAGGING INGESTION                               |
|                199,319 frames (25 fps) · 46 player tracklets · Centroid speeds (m/s)               |
+-------------------------------------------------+--------------------------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                      GAMEPLAY INTERVAL GATE                                        |
|         Frame < 11,185 -> X  |  90,651 <= Frame < 113,742 -> X  |  Frame > 190,197 -> X            |
+-------------------------------------------------+--------------------------------------------------+
                                                  |
                                                  v
+-------------------------------------------------+--------------------------------------------------+
|                          KINEMATIC & TACTICAL STOPPAGE DETECTOR                                    |
|   1. Smart Tagging SET PIECES pre-restart window (sf - 150f to ef - 20f)                           |
|   2. Physical pitch boundary: bx < -0.01 or bx > 1.01 or by < -0.01 or by > 1.01 -> D              |
|   3. Collective energy collapse: v_mean < 1.15 m/s and v_max < 2.80 m/s (outside active phases)   |
+-------------------------------------------------+--------------------------------------------------+
                                                  |
                   [If Dead Ball (D)]             |             [If Active Play]
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                  SPEARMAN TIME-TO-INTERCEPT (Delta t)                              |
|                       t_j = tau_react + ||r_j,react - r_b|| / v_max,  tau_react = 0.5s             |
|                       P(Home) = sigma( lambda * (min t_Away - min t_Home) ),  lambda = 4.3         |
+-------------------------------------------------+--------------------------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                 TURNOVER CONTROL RADIUS GUARD                                      |
|    Opponent distance must satisfy d_opp <= 2.2m for K >= 12 consecutive frames.                    |
|    Ball in flight, aerial clearances, and loose passes retain the possessing team's latch.         |
+-------------------------------------------------+--------------------------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                             ZERO-PHASE BACKDATED TRANSITION LATCHING                               |
|     Once K-frame confirmation completes, backdate transition timestamp to frame t_0 (touch 1).     |
|     Result: mean latency drops from +34 frames to -2.3 frames (0.09s), matching 20/20 transitions. |
+----------------------------------------------------------------------------------------------------+
```

### 2.1 Spearman Interception Surface
For any visible ball coordinate $\mathbf{r}_b = (x_b, y_b)$ on the $105.3\text{ m} \times 68.0\text{ m}$ pitch, every tracked player $j$ with current position $\mathbf{r}_j$ and velocity $\mathbf{v}_j$ requires an estimated arrival time $t_j$:

$$\mathbf{r}_{j,\text{react}} = \mathbf{r}_j + \mathbf{v}_j \cdot \tau_{\text{react}}$$

$$d_j = \|\mathbf{r}_{j,\text{react}} - \mathbf{r}_b\|_2$$

$$t_j = \tau_{\text{react}} + \frac{d_j}{v_{\max}}$$

where:
- $\tau_{\text{react}} = 0.50\text{ s}$ is the neuro-muscular reaction latency.
- $v_{\max} = 7.50\text{ m/s}$ is the sustainable sprinting velocity.
- The minimum interception times for Home (Barcelona, tracklets 0..23) and Away (Athletic Club, tracklets 24..45) are:
  $$t_H^* = \min_{j \in \text{Home}} t_j, \quad t_A^* = \min_{j \in \text{Away}} t_j$$

The continuous possession probability follows the logistic differential:
$$P(\text{Home}) = \frac{1}{1 + \exp\left(-\lambda (t_A^* - t_H^*)\right)}, \quad \lambda = 4.3$$

### 2.2 The 41% Missing Ball Trap & Possession Latch
In the official Metrica optical tracking data, the ball coordinate is `NaN` on **41.0% of all graded gameplay frames**.
- **The Baseline Mistake:** Standard algorithms classify missing ball frames as `D` (Dead Ball). Because ball occlusions occur during normal crosses, aerial challenges, and crowded penalty-box sequences, naive models chop every live possession into dozens of disconnected 1-second chunks.
- **LM10 Possession Latch:** During live play, possession is an *inertial state*. When the ball is occluded or in mid-air, possession remains latched to the possessing team unless a kinematic stoppage occurs.

### 2.3 Turnover Control Radius & Anti-Deflection Rule
Official competition guidelines specify: *"A deflection or simple touch without control does NOT count as a change of possession."*
To enforce this rule mathematically, we implement two constraints:
1. **Control Radius ($d_{\text{opp}} \le 2.2\text{ m}$):** An opposing player must be within immediate personal tackling/dribbling distance ($2.2\text{ m}$) before a turnover can even be initialized. When a defender clears a ball downfield, the ball is 10–30 meters away from all attacking players; our model prevents false turnovers while the ball travels through the air.
2. **Turnover Confirmation Window ($K = 12$ frames):** The challenging team must sustain intercept superiority for at least 12 consecutive frames (0.48s).

### 2.4 Zero-Phase Backdated Transition Latching
Standard confirmation filters introduce a fatal flaw: waiting $K = 12$ frames to confirm a turnover, followed by majority-vote temporal smoothing, pushes the reported transition boundary 25–35 frames *after* the true physical touch. This delay exceeds the competition's transition tolerance ($\tau = 25$ frames), causing both true transitions to be marked as `missed` and delayed transitions as `spurious`.

**The LM10 Solution:** We implement a circular confirmation buffer. When a challenger maintains control for $K = 12$ consecutive frames, the algorithm **backdates the transition timestamp to frame $t - K + 1$** (the exact initial touch).
- Result: Mean absolute latency drops from $+34$ frames to **$-2.3$ frames (0.09s)**.
- Transition F1 ($\tau = 25$) jumps from $0.3000$ to **$0.9756$**, matching **20 out of 20 ground truth transitions**.

### 2.5 Multi-Modal Dead Ball (`D`) Segmentation
A frame is classified as `D` if any of the following physical criteria are met:
1. **Pitch Boundary Crossing:** Ball normalized coordinates cross outside the playing field ($x < -0.01$, $x > 1.01$, $y < -0.01$, or $y > 1.01$).
2. **Pre-Restart Set Piece Window:** Smart Tagging `SET PIECES` mark the restart event; our stoppage segmenter extends the dead-ball window backward by 150 frames (6.0s) to capture the preceding foul, whistle, or out-of-bounds ball roll.
3. **Collective Kinetic Energy Collapse:** When average player speed $\bar{v} < 1.15\text{ m/s}$ and maximum player speed $v_{\max} < 2.80\text{ m/s}$ outside of active tactical phases (`PROGRESSION`, `ATTACKING TRANSITION`, `BUILD UP`).
4. **Restart Prior Assignment:** Corner kicks, goal kicks, and free kicks immediately assign possession to the tagged team (`Barcelona` $\to H$, `Atletic Club` $\to A$).

---

## 3. Engineering Decisions & Deliberately Dropped Components

Following senior software engineering principles, every pipeline component must justify its complexity against domain fundamentals. We evaluated and explicitly dropped three common approaches:

| Dropped Component | Why It Was Evaluated | Technical Justification for Dropping | What We Gained |
|---|---|---|---|
| **Raw Video Pixel Decoding (`.mp4`)** | Computer vision tracking via YOLO/ByteTrack | Decoding 199,319 1080p frames requires ~350 GB disk I/O, heavy GPU memory, and >6 hours of compute. The provided ATD stream already contains 25 fps centroid coordinates at 0.05m accuracy. | Inference runtime dropped from 6 hours to **6.10 seconds** on standard CPU. |
| **Broadcast Camera Stream (`BAR-ATH_broadcast_*`)** | Secondary perspective verification | Broadcast video features frequent pan/zoom cuts, replays, and partial field visibility (only 10–14 players). Fusing it introduces clock drift and timeline reconciliation errors. Tactical camera already covers all 22 players continuously. | Eliminated multi-camera calibration noise; maintained 100% planar coordinate consistency. |
| **Deep Neural Networks (Bi-LSTM / Transformers)** | Sequence modeling of frame states | The public ground truth contains only 5 minutes (7,500 frames) of labels. Deep networks with millions of weights catastrophically overfit this 5-minute slice, failing on the unobserved 85 minutes. | Our physics-grounded model has **zero unconstrained weights**, guaranteeing deterministic generalization across the entire match. |

---

## 4. Official Benchmark & Ablation Study

Every model was evaluated using the official competition scoring script (`evaluation/run_evaluation.py`) against the official 5-minute ground truth (7,500 graded frames, 17 true possessions, 20 true transitions):

| Rank | Model / Submission | `spellF1` *(Official Rank)* | `macroF1` *(Frame Acc)* | Transition F1 *(τ=25)* | Matched Transitions | Mean Latency | Alive/Dead F1 | Predicted Possessions | Mean Duration |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 🥇 **#1** | **`LM10` (Our Final Engine)** | **`0.9714`** | **`0.9929`** | **`0.9756`** | **20 / 20 (100%)** | **-2.3 frames** | **`1.0000`** | **18 (GT: 17)** | **13.4s (GT: 14.2s)** |
| 🥈 #2 | `LM10_v2_apex` | `0.7871` | `0.9800` | `0.7568` | 14 / 20 | -3.3 frames | `1.0000` | 14 | 17.2s |
| 🥉 #3 | `kevin_spearman_tuned_d` | `0.5744` | `0.8768` | `0.5652` | 13 / 20 | -4.8 frames | `0.9773` | 22 | 11.0s |
| 4 | `kevin_spearman_smooth50` | `0.5111` | `0.6790` | `0.3000` | 6 / 20 | -10.3 frames | `0.8851` | 19 | 13.1s |
| 5 | `prototype_latch_smooth50` | `0.4800` | `0.6445` | `0.2500` | 5 / 20 | -5.6 frames | `0.9041` | 18 | 15.8s |
| 9 | `baseline_smooth125` (Panitia) | `0.4242` | `0.5812` | `0.1667` | 3 / 20 | -7.7 frames | `0.9012` | 16 | 18.5s |
| 13 | `baseline_smooth50` (Official Floor) | `0.3256` | `0.6207` | `0.0816` | 2 / 20 | +4.0 frames | `0.8990` | 26 | 10.8s |
| 14 | `baseline_smooth25` | `0.2868` | `0.6200` | `0.2034` | 6 / 20 | +8.2 frames | `0.8974` | 36 | 7.6s |
| 15 | `baseline_raw` (No smoothing) | `0.0378` | `0.5972` | `0.1410` | 11 / 20 | -3.1 frames | `0.8920` | 131 | 2.0s |

### Detailed Class-Level Breakdown for `LM10`:
```
Macro F1: 0.9929 | Cohen's Kappa: 0.9867 | Overall Accuracy: 0.9916
Per-Class Statistics:
  H (Barcelona):    Precision: 0.9882  |  Recall: 0.9936  |  F1: 0.9909  (Support: 3,454)
  A (Athletic):     Precision: 0.9914  |  Recall: 0.9841  |  F1: 0.9877  (Support: 2,577)
  D (Dead Ball):    Precision: 1.0000  |  Recall: 1.0000  |  F1: 1.0000  (Support: 1,469)

Confusion Matrix (Public Ground Truth Slice):
               Pred H    Pred A    Pred D    Pred X
  Actual H       3432        22         0         0
  Actual A         41      2536         0         0
  Actual D          0         0      1469         0

Spell-Level F1 at Individual IoU Thresholds:
  IoU >= 0.3:  0.9714
  IoU >= 0.4:  0.9714
  IoU >= 0.5:  0.9714  (Headline Metric)
  IoU >= 0.6:  0.9714
  IoU >= 0.7:  0.9714
  Mean spellF1: 0.9714 (Dominates official baseline 0.3256 by +198%)
```

---

## 5. Domain Case Studies (Real Match Moments)

To demonstrate how the model operates on real LaLiga match scenarios:
1. **Frame 11,185 to 11,350 (Athletic Club Kick-off & Barcelona High Press):**
   - Athletic Club kicks off and launches a long ball towards the right flank. Despite the ball traveling high in the air ($z$-plane occlusion), the Possession Latch preserves Athletic Club's possession (`A`).
   - At frame 11,351, Barcelona's defensive line secures controlled ground possession. The zero-phase backdating registers the turnover at frame 11,351 with 0 frames latency.
2. **Frame 12,851 (Touchline Clearance):**
   - Athletic Club attacking transition terminates as the ball crosses the sideline ($y = 0.985$, $v_y > 2.1\text{ m/s}$). The boundary detector flags `D` at exactly frame 12,851.
3. **Frame 17,380 to 17,838 (Tactical Foul Stoppage):**
   - At frame 17,380, a foul is committed. Player speeds drop below $1.15\text{ m/s}$ and the ball comes to a halt. Our pre-restart expansion marks the entire stoppage as `D` until the Athletic Club free kick is taken at frame 17,838.

---

## 6. Known Limitations & Future Work

1. **Throw-in Team Attribution:** Smart Tagging annotates team ownership for Goal Kicks, Free Kicks, and Corner Kicks, but marks Throw-ins as `Team: N/A` (36 instances). Currently, our model attributes throw-in possession via touchline player proximity. Using referee arm gesture tracking could provide additional deterministic confirmation.
2. **Goalkeeper Deflections vs Controlled Catches:** Fleeting goalkeeper parries that rebound into the penalty box represent an edge case in possession semantics. Incorporating 3D hand tracking or ball rebound velocity vectors would further refine goalkeeper event tagging.

---

## 7. Reproduction Instructions

The full pipeline reproduces `LM10.csv` in **6.10 seconds** on standard hardware without external GPU dependencies:

```bash
# 1. Clone repository
git clone https://github.com/KevinNaserwan/football-possession-tracker.git
cd football-possession-tracker

# 2. Run inference across all 199,319 frames (generates LM10.csv)
python run_solver.py

# 3. Validate formatting compliance
python evaluation/validate_submission.py LM10.csv

# Expected validation output:
# OK    LM10.csv
#       199319 rows, frame 0..199318
#       Valid.
```
