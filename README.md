<div align="center">

# ⚽ Football Possession Tracker
### Automated Frame-by-Frame Ball Possession & Spatial Pitch Control Engine
**Tailored for More Than a Hack 2027 · Barça Innovation Hub & Metrica Sports**

[![Python CI](https://github.com/KevinNaserwan/football-possession-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/KevinNaserwan/football-possession-tracker/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Barça Innovation Hub](https://img.shields.io/badge/Competition-Bar%C3%A7a%20Innovation%20Hub-ED1B24.svg)](https://talentarena.barcainnovationhub.com)

</div>

---

## 📌 Executive Summary & Hackathon Context

This repository hosts a production-grade football spatial tracking engine specifically engineered for the **More Than a Hack 2027 Hackathon**, organized by **Mobile World Capital Barcelona**, **Barça Innovation Hub (BIHUB)**, and **Metrica Sports**.

### Initial Challenge Objective:
> *"Estimate team possession for every frame of a football match working with provided automatic tracking data (ATD) and homography."*

Rather than relying purely on Euclidean distance to the ball (which fails during passes, aerial duels, and loose-ball scrambles), this engine combines:
1. **Planar Homography Calibration & Kalman Smoothing**: Converts broadcast video pixel coordinates into a normalized $105\text{ m} \times 68\text{ m}$ pitch surface.
2. **Spearman Pitch Control Modeling**: Calculates each player's dynamic *time-to-intercept* ($\Delta t$) based on instantaneous speed, reaction latency, and physical momentum.
3. **Temporal Consistency (Markov Filtering)**: Prevents high-frequency possession flickering across consecutive frames.

---

## 🏛️ System Architecture

```
+-------------------------------------------------------------------------+
|                       VIDEO & DATA INGESTION ENGINE                     |
|                 Broadcast Video Stream / ATD Tracking Feed              |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                    CALIBRATION & SPATIAL PROJECTION                     |
|     Pitch Landmark Detection  --->  Planar Homography Transformation (H) |
|                                     |                                   |
|                                     v                                   |
|                        Kalman Trajectory Smoother                       |
|                                     |                                   |
|                                     v                                   |
|                   Pitch Plane Coordinates (105m x 68m)                  |
+------------------------------------+------------------------------------+
                                     |
                   +-----------------+-----------------+
                   |                                   |
                   v                                   v
+------------------------------------+ +----------------------------------+
|    BALL TRAJECTORY STATE MACHINE   | |    PLAYER KINEMATICS ENGINE      |
|    Flight / Ground / Loose Ball    | |    Velocity & Acceleration Vector|
+------------------+-----------------+ +-----------------+----------------+
                   |                                     |
                   +-----------------+-------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                       SPEARMAN PITCH CONTROL MODEL                      |
|             Dynamic Time-to-Intercept (Delta t) Calculation             |
|             Continuous Ball Control Probability Surface                 |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                   FRAME-BY-FRAME POSSESSION EVALUATOR                   |
|                                    |                                    |
|                                    v                                    |
|                  HMM Temporal Consistency Markov Filter                 |
|                                    |                                    |
|         +--------------------------+--------------------------+         |
|         |                                                     |         |
|         v                                                     v         |
|  Official Match Tagging Output                      2D Tactical Visualizer|
|  (Time Series CSV / JSON Feeds)                     & Video Overlay Pipe|
+-------------------------------------------------------------------------+
```

---

## 📐 Mathematical Formulation

### 1. Planar Homography Transformation
Coordinates in pixel space $\mathbf{x} = [u, v, 1]^T$ are projected to pitch coordinates $\mathbf{X} = [X, Y, 1]^T$ via homography matrix $\mathbf{H} \in \mathbb{R}^{3 \times 3}$:

$$\mathbf{X} \sim \mathbf{H} \, \mathbf{x}$$

$$\begin{bmatrix} X' \\ Y' \\ w \end{bmatrix} = \begin{bmatrix} h_{11} & h_{12} & h_{13} \\ h_{21} & h_{22} & h_{23} \\ h_{31} & h_{32} & h_{33} \end{bmatrix} \begin{bmatrix} u \\ v \\ 1 \end{bmatrix}, \quad X = \frac{X'}{w}, \quad Y = \frac{Y'}{w}$$

### 2. Time-to-Intercept ($\tau$) & Pitch Control
For each player $j$ with position $\mathbf{p}_j$, velocity $\mathbf{v}_j$, and reaction time $t_{\text{react}}$:

$$\tau_j = t_{\text{react}} + \frac{\|\mathbf{p}_{\text{ball}} - (\mathbf{p}_j + \mathbf{v}_j \cdot t_{\text{react}})\| - r_{\text{ctrl}}}{v_{\max}}$$

Probability of team possession $P(\text{Team}_A)$ is derived from the logistic differential:

$$P(\text{Team}_A) = \frac{1}{1 + \exp\left(-\lambda (\tau_B^* - \tau_A^*)\right)}$$

where $\tau_A^*$ and $\tau_B^*$ are the minimum intercept times for Team A and Team B.

---

## 📂 Project Structure

```
football-possession-tracker/
├── data/                      # Sample tracking datasets (Metrica ATD) & pitch calibration points
├── docs/                      # Scientific documentation, pitch control formulas & pitch deck
├── notebooks/                 # Exploratory data analysis & validation experiments
│   └── 01_baseline_possession.ipynb
├── src/
│   ├── homography.py          # Planar homography perspective calibration
│   ├── kalman_smoother.py     # Kalman filter for camera jitter reduction
│   ├── metrica_parser.py      # Metrica Sports tracking CSV/JSON parser
│   ├── pitch_control.py       # Spearman Pitch Control implementation
│   ├── possession_estimator.py# Multi-factor frame possession evaluator
│   └── visualizer.py          # 2D pitch animations & tactical overlays
├── tests/                     # Automated pytest test suites
└── requirements.txt           # Production dependencies
```

---

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Clone the repository
git clone git@github.com:KevinNaserwan/football-possession-tracker.git
cd football-possession-tracker

# Install required dependencies
pip install -r requirements.txt
```

### 2. Run Possession Evaluation
```bash
python -c "from src.possession_estimator import PossessionEstimator; print('Possession Engine Ready!')"
```

### 3. Run Test Suite
```bash
pytest tests/ -v
```

---

## 📊 Evaluation & Verification Metrics

Submissions are evaluated against ground-truth manual annotations provided by Barça match analysts:
- **Frame-level Accuracy**: Percentage of in-play frames where calculated team possession matches ground truth.
- **Turnover Detection Precision / Recall**: Accuracy in pinpointing exact frame indices where possession switches occur.
- **Inference Throughput**: Target latency $\le 25\text{ ms/frame}$ on standard compute.

---

## 👥 Author & Acknowledgements
- **Author**: Kevin Putrayudha Naserwan ([@KevinNaserwan](https://github.com/KevinNaserwan))
- **Competition**: More Than a Hack 2027 · Barça Innovation Hub & Metrica Sports.
