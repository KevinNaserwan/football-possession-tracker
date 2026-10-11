# Football Possession Tracker (More Than a Hack 2027)

Automated frame-by-frame ball possession estimation and pitch tracking system tailored for **More Than a Hack 2027** (organized by Mobile World Capital Barcelona, Barça Innovation Hub & Metrica Sports).

## Challenge Alignment
- **Initial Challenge Target**: Estimate team possession for every frame of a football match using provided automatic tracking data (ATD) and homography calibration.
- **Key Techniques**: Planar homography perspective transformation, spatial player-ball proximity modeling, and dynamic pitch control metrics.

## Project Structure
```
├── data/              # Tracking data samples and homography calibration targets
├── src/
│   ├── homography.py          # Planar homography transformations (camera -> pitch)
│   ├── possession_estimator.py# Frame-by-frame ball control & possession evaluation
│   └── visualizer.py          # 2D pitch animations & tactical overlays
├── notebooks/         # Exploratory analysis & validation benchmarks
└── requirements.txt   # Core analytical dependencies
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run unit tests
pytest tests/
```

## Roadmap & Progress Checklist
- [x] Initial homography transformer and spatial coordinate normalization
- [x] Proximity-based frame possession estimator
- [ ] Integration with Metrica Sports open tracking format
- [ ] Gaussian Pitch Control Model (Spearman model)
- [ ] Automated evaluation metric pipeline against ground truth annotations

## License
MIT
