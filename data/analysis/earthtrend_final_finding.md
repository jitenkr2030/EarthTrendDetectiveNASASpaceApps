# EarthTrend Detective — Final Finding

## Case #001 — Jharkhand

## Final detective finding

Across the analyzed Jharkhand SMAP record, no statistically significant long-term monotonic soil-moisture decline was detected. The state-level trend was slightly negative but highly non-significant, and none of the 984 SMAP cells had a statistically significant long-term trend in the first-pass cell analysis. Seasonal analysis also found no significant state-level seasonal trends, while the seven raw significant cell-season results disappeared after Benjamini-Hochberg FDR correction, leaving no statistically robust spatial-seasonal hotspots. At the same time, the record contains widespread episodic soil-moisture extremes. Soil-moisture and rainfall anomalies show a strong positive same-month association, and that overall association remains significant after an autocorrelation-aware effective-sample-size adjustment. The spatial rainfall relationship is also consistently positive across the mapped SMAP cells and remains stable when the analysis is restricted to closer SMAP-GPM matches. Together, the evidence supports strong rainfall-linked variability and episodic extremes, rather than a simple state-wide long-term drying claim.

## 1. Data

- SMAP product: **SPL4SMGP Version 008**
- SMAP variable: **/Geophysical_Data/sm_surface**
- Analysis period: **2015-04-01 → 2026-09-01**
- Monthly periods: **138**
- SMAP cells: **984**
- Cell-month records: **135,792**
- GPM comparison period: **2015-04-01 → 2025-09-01**
- Common GPM months: **126**

## 2. Long-term trend evidence

- Sen slope: **-0.0001399279 soil-moisture units/year**
- Kendall tau: **-0.004972**
- p-value: **0.931059**
- Significant at 0.05: **False**
- Significant cells: **0 / 984**

**Interpretation:** The analyzed record does not show a statistically significant state-wide monotonic drying trend.

## 3. Seasonal and spatial trend evidence

- Significant state seasonal trends: **0 / 4**
- Raw significant cell-season results: **7**
- FDR-significant spatial trend results: **0**
- Spatial hotspots: **0**

After FDR correction, no statistically robust spatial-seasonal trend hotspot was identified.

## 4. Extreme-event evidence

- Extreme dry cell-months: **1,656**
- Extreme wet cell-months: **4,261**
- Total extreme cell-months: **5,917**
- Event episodes: **9** (4 dry, 5 wet)
- Cells experiencing at least one extreme: **984**

## 5. Rainfall relationship

- Same-month standardized Pearson r: **0.713536**
- Same-month Pearson p: **6.877e-21**
- Strongest tested lag: **0 month**
- Pearson r at strongest lag: **0.713536**
- Autocorrelation-adjusted effective N: **84.46**
- Autocorrelation-adjusted p: **2.200e-14**
- Significant after adjustment: **True**

## 6. Spatial rainfall relationship

- Mapped SMAP cells: **984**
- GPM cells: **703**
- Pearson r range: **0.5431 → 0.7903**
- Mean Pearson r: **0.6724**
- Median Pearson r: **0.6791**
- Mean mapping distance: **4.29 km**
- Maximum mapping distance: **13.60 km**

### Distance sensitivity

- **all_cells**: 984 cells, mean r = 0.672448, median r = 0.679120
- **<=10_km**: 983 cells, mean r = 0.672451, median r = 0.679177
- **<=7.5_km**: 960 cells, mean r = 0.672552, median r = 0.679193
- **<=5_km**: 625 cells, mean r = 0.673158, median r = 0.678574

This shows that the spatial relationship remains stable when restricting matches to closer distances.

## 7. Scientific interpretation

The central result is not evidence of a simple long-term drying trend across Jharkhand. Instead, the analyzed SMAP record shows substantial temporal variability, widespread extreme soil-moisture events, and a strong statistical association between soil-moisture and rainfall anomalies. The association is strongest in the same month among the tested lags and remains significant after the autocorrelation-aware adjustment applied here.

The rainfall relationship should be interpreted as statistical association rather than proof of a causal mechanism.

## 8. Limitations

- The primary long-term SMAP trend test is a first-pass Kendall/Mann-Kendall-style analysis and is not a fully seasonality- and autocorrelation-corrected trend model.
- The seasonal trend analysis explicitly states that it is not an autocorrelation-corrected Seasonal Mann-Kendall implementation.
- Seasonal rainfall-soil-moisture analyses use relatively small complete season-year sample sizes; therefore seasonal estimates should be interpreted cautiously.
- The GPM comparison period ends in September 2025, whereas the SMAP analysis continues through September 2026.
- The spatial cross-variable analysis maps 984 SMAP cells to 703 coarser GPM cells, so the 984 spatial correlations are not 984 independent spatial experiments.
- FDR significance in the spatial cross-variable analysis is a multiple-testing screening result and does not remove all spatial-dependence concerns.
- Extreme-event thresholds and the minimum 5 percent affected-cell criterion are analytical definitions used by this study.
- Correlation and lagged association establish statistical association, not physical causality.

## 9. Reproducibility

Generated automatically by `src/15_final_evidence_synthesis.py` from the frozen analysis outputs and evidence manifests.
