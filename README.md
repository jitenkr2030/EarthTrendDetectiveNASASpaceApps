# EarthTrend Detective

**Exploring soil-moisture variability across Jharkhand, India, using NASA SMAP data and GPM rainfall observations.**

EarthTrend Detective is a data-analysis and visualization project developed for the NASA Space Apps Challenge 2026. It explores multi-year surface soil-moisture patterns, rainfall relationships, seasonal variability, and statistical extremes.

## Live Demo

- **Dashboard:** https://earthtrenddetectivenasaspaceapps-production.up.railway.app/
- **GitHub:** https://github.com/jitenkr2030/EarthTrendDetectiveNASASpaceApps

## Key Findings

The current analysis covers April 2015–September 2026.

| Measure | Result |
|---|---|
| Monthly SMAP periods | 138 |
| SMAP grid cells | 984 |
| Cell-month records | 135,792 |
| Monthly dataset quality checks | 138 PASS, 0 FAIL |
| First-pass state-level trend | Kendall tau ≈ −0.00497; p ≈ 0.931 |
| Same-month rainfall/soil-moisture anomaly association | Pearson r ≈ 0.714 |
| Threshold-classified extreme cell-months | 5,917: 1,656 dry and 4,261 wet |

### Interpretation

- The first-pass state-level trend test did not detect a statistically significant monotonic trend. The results do not support claiming a statistically significant state-wide drying trend.
- Soil-moisture and rainfall anomalies show a positive association during their common analysis period. Correlation does not establish causation.
- Extreme cell-months are classifications based on the study's selected thresholds. They are not independently verified drought or flood events.
- A non-significant trend does not prove that drought risk is absent.

## Data Sources

- **NASA SMAP SPL4SMGP, Version 008:** Surface soil moisture (`sm_surface`), measured in m³/m³.
- **NASA GPM IMERG Monthly, Version 07B:** Precipitation data used for rainfall comparisons.

The SMAP series extends through September 2026. The common SMAP–GPM comparison period ends in September 2025.

## Methodology

The project combines:

1. Monthly soil-moisture extraction and quality checks.
2. Spatial masking for the Jharkhand study area.
3. Monthly climatology and anomaly analysis.
4. First-pass state-level and grid-cell trend screening.
5. Seasonal comparisons and threshold-based extreme classification.
6. Comparison of standardized soil-moisture and rainfall anomalies.
7. Dashboard visualizations of the analysis results.

## Data Quality

The monthly QA report contains 138 rows, covering April 2015–September 2026, with 138 PASS and 0 FAIL. The report records 984 expected cells per month, with zero missing values and zero duplicate cells.

- [Monthly QA report](data/qa/final_dataset_qa_monthly.csv)
- [Validation record](docs/VALIDATION.md)
- [Final evidence summary](data/analysis/earthtrend_final_finding.md)
- [Machine-readable evidence](data/analysis/earthtrend_final_evidence.json)

## Scientific Limitations

- The state-level trend test is a first-pass analysis, not a fully seasonality- and autocorrelation-corrected trend model.
- None of the four state-level seasonal trend tests was statistically significant. No cell-season result remained significant after false-discovery-rate correction.
- SMAP and GPM have different spatial resolutions. Multiple SMAP cells can map to the same GPM cell, so spatial correlations are not fully independent.
- The rainfall comparison covers a shorter period than the SMAP-only analysis.
- Extreme classifications depend on the thresholds selected for this study.
- Correlation does not establish causation. This project is not an operational drought forecast.

## Challenge Presentation

- [Three-minute judge demo](docs/JUDGE_DEMO_SCRIPT.md)
- [Judge questions and answers](docs/JUDGE_QA.md)

## Technology

Python-based data processing and statistical analysis, NASA Earth-observation datasets, and a web dashboard deployed on Railway.

## Reproducibility

Clone the repository, create a Python virtual environment, and install the project dependencies:

```bash
git clone https://github.com/jitenkr2030/EarthTrendDetectiveNASASpaceApps.git
cd EarthTrendDetectiveNASASpaceApps
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Consult the project scripts and documentation for the analysis workflow. The dashboard's startup command may depend on its configured entry point and deployment environment.

## NASA Space Apps Challenge 2026

This is an independently developed challenge project using NASA Earth-observation data. It does not imply NASA endorsement or official validation of the findings.

## Author

**Jitender Kumar**
GitHub: [@jitenkr2030](https://github.com/jitenkr2030)

## License

See the repository's license file for applicable terms.
