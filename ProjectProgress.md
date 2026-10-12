# EarthTrend Detective — Project Progress

**Project:** EarthTrend Detective
**Challenge:** NASA Space Apps Challenge 2026 — *Be An Earth System Trend Detective!*
**Study Region:** Jharkhand, India
**Primary Dataset:** NASA SMAP Level-4 Global 3-hourly 9 km Surface and Root-Zone Soil Moisture
**Dataset:** `SPL4SMGP`
**Variable:** `Geophysical_Data/sm_surface`
**Spatial cells:** 984
**Current extraction period:** April 2015 → 2026
**Status:** Data acquisition and processing phase

---

# 1. Project Objective

EarthTrend Detective is an evidence-first Earth-system trend analysis project.

The goal is not simply to visualize satellite data, but to investigate questions such as:

* What changed?
* Where did it change?
* When did it change?
* How large was the change?
* Which season shows the strongest signal?
* Is the observed trend statistically significant?
* Does another Earth-system variable support the finding?
* Can the result be explained as a scientifically defensible Earth-system story?

The final product should behave like a **scientific detective system**:

```text
Question
   ↓
NASA Data
   ↓
Quality Control
   ↓
Observation
   ↓
Anomaly
   ↓
Trend
   ↓
Statistical Test
   ↓
Spatial Pattern
   ↓
Seasonal Pattern
   ↓
Cross-Variable Evidence
   ↓
Detective Finding
```

---

# 2. Current Overall Status

## Current priority

**Complete the SMAP dataset through 2026 before beginning final scientific analysis.**

The project currently has a continuous monthly dataset from:

```text
2015-04 → 2022-12  COMPLETE
2023                IN PROGRESS
2024                PENDING
2025                PENDING
2026                PENDING
```

The 2023 extraction is currently being processed using the automated year runner.

---

# 3. Dataset Progress

## Completed dataset

### April 2015 → December 2022

| Period            | Months | Status       |
| ----------------- | -----: | ------------ |
| 2015-04 → 2015-12 |      9 | Complete     |
| 2016              |     12 | Complete     |
| 2017              |     12 | Complete     |
| 2018              |     12 | Complete     |
| 2019              |     12 | Complete     |
| 2020              |     12 | Complete     |
| 2021              |     12 | Complete     |
| 2022              |     12 | Complete     |
| **Total**         | **93** | **Complete** |

Each month contains:

```text
984 spatial cells
```

Therefore the completed dataset represents:

```text
93 × 984 = 91,512 cell-month records
```

## 2023

2023 extraction is currently running.

Completed months will be validated automatically by the year extraction pipeline.

Target:

```text
2023-01 → 2023-12
```

## Future extraction

After 2023:

```text
2024
2025
2026
```

The final 2026 endpoint depends on the available NASA inventory/data coverage.

---

# 4. Spatial Dataset

## Jharkhand spatial mask

A fixed spatial mask has been created for Jharkhand.

Current mask:

```text
984 SMAP grid cells
```

The mask contains:

```text
row
col
latitude
longitude
```

The same spatial grid is used across the monthly dataset to enable consistent spatial comparison.

Mask file:

```text
data/jharkhand_smap_mask.csv
```

---

# 5. NASA Data Pipeline

## Data discovery

NASA CMR inventory discovery has been implemented.

Current inventory covers SMAP SPL4SMGP granules across the project period.

Script:

```text
src/inventory_smap.py
```

Output:

```text
data/smap_granule_inventory.csv
```

---

# 6. OPeNDAP Extraction

Direct NASA Earthdata OPeNDAP access is used rather than downloading every large HDF5 granule.

The production extractor:

```text
src/extract_monthly_parallel.py
```

uses:

* NASA OPeNDAP
* DAP4
* parallel workers
* spatial window extraction
* Jharkhand mask
* retries
* checkpoints
* monthly aggregation

---

# 7. Parallel Processing

Benchmarking was performed to determine a practical production configuration.

Selected configuration:

```text
Protocol: DAP4
Workers: 8
```

The benchmark demonstrated substantially better throughput than the original sequential approach.

The production pipeline therefore uses:

```text
DAP4 + 8 parallel workers
```

---

# 8. Checkpoint / Resume System

The monthly extractor supports resumable processing.

Checkpoint location:

```text
data/checkpoints_parallel/
```

A checkpoint records completed granules and accumulated cell-level sums/counts.

If processing is interrupted, the same month can be restarted without unnecessarily reprocessing successfully completed granules.

Example:

```bash
python src/extract_year.py 2023 --workers 8
```

If interrupted:

```bash
python src/extract_year.py 2023 --workers 8
```

can be run again to continue processing.

---

# 9. Automated Year Extraction

A year-level runner has been implemented:

```text
src/extract_year.py
```

It:

1. Generates the required months for a year.
2. Checks whether an existing monthly dataset is valid.
3. Runs the monthly extractor when necessary.
4. Validates the resulting monthly file.
5. Continues to the next month.
6. Stops if a month fails validation.
7. Supports resumable execution.

Example:

```bash
python src/extract_year.py 2023 --workers 8
```

Successful completion produces:

```text
YEAR 2023: COMPLETE
```

---

# 10. Monthly Dataset Format

Monthly outputs contain fields including:

```text
row
col
latitude
longitude
month
soil_moisture_mean
observations
expected_observations
coverage_fraction
```

Example validation condition:

```text
rows = 984
observations = expected_observations
coverage_fraction = 1.0
```

---

# 11. Quality Control

A quality-gate system has already been implemented.

Current quality checks include:

* monthly file availability
* expected month continuity
* spatial cell count
* observation counts
* coverage
* missing values
* dataset structure

Research quality gate:

```text
research/05_quality_gate.py
```

The quality gate was made dynamic so that it evaluates the months actually present in the dataset rather than relying on a hard-coded 21-month study period.

---

# 12. Existing Research Modules

The following research modules have already been developed.

```text
research/
├── 01_earthtrend_data_explorer.py
├── 02_cell_explorer.py
├── 03_seasonality_analysis.py
├── 04_coverage_detective.py
├── 05_quality_gate.py
├── 06_season_comparison.py
└── 07_spatial_seasonality.py
```

---

# 13. Spatial Seasonality

Four seasons are currently defined as:

```text
Winter        Jan–Feb
Pre-monsoon   Mar–May
Monsoon       Jun–Sep
Post-monsoon  Oct–Dec
```

The spatial seasonality analysis calculates:

* seasonal mean
* monsoon minus pre-monsoon
* seasonal maximum
* seasonal minimum
* seasonal range
* seasonal standard deviation
* coefficient of variation
* four-season completeness

This provides the foundation for later seasonal trend analysis.

---

# 14. Scientific Analysis — Pending

The final scientific analysis has **not yet been declared complete**.

After the full 2015–2026 dataset is finished, the following analysis will be performed.

## 14.1 Final Dataset Quality Gate

Validate the entire dataset.

Checks:

* continuous monthly sequence
* no missing months
* 984 cells/month
* duplicate detection
* missing values
* observation completeness
* coverage
* physical value ranges
* coordinate consistency
* row/column consistency

Create:

```text
DATASET_MANIFEST.json
QUALITY_REPORT.md
```

---

# 15. Consolidated Analysis Dataset

Create a unified analysis-ready dataset from the monthly files.

Target structure:

```text
date
year
month
row
col
latitude
longitude
soil_moisture
season
anomaly
```

Possible output:

```text
data/analysis/smap_monthly_jharkhand.csv
```

The raw monthly outputs should remain available for reproducibility.

---

# 16. Climatology

Calculate the long-term monthly climatology.

For example:

```text
January climatology
February climatology
March climatology
...
December climatology
```

This will provide the baseline against which unusual conditions can be evaluated.

---

# 17. Soil-Moisture Anomalies

Calculate monthly and seasonal anomalies.

Conceptually:

```text
Observed soil moisture
        -
Expected climatological soil moisture
        =
Soil-moisture anomaly
```

Classify unusual periods such as:

```text
Unusually dry
Near normal
Unusually wet
```

The exact thresholds will be determined scientifically rather than arbitrarily.

---

# 18. Trend Detection

Trend analysis is a core scientific objective.

Planned methods include:

### Sen's slope

Estimate the magnitude and direction of the trend.

### Mann-Kendall

Test whether the temporal trend is statistically significant.

### Seasonal Mann-Kendall

Account for the strong seasonal structure of soil moisture.

### Autocorrelation handling

Temporal autocorrelation will be evaluated before final significance claims.

Potential methods include:

* pre-whitening
* trend-free pre-whitening
* autocorrelation-adjusted significance methods

The final method will be selected based on the actual properties of the dataset.

---

# 19. Spatial Trend Analysis

Calculate trend statistics independently for all 984 grid cells.

Target output:

```text
latitude
longitude
sen_slope
kendall_tau
p_value
significant
trend_direction
```

Possible classifications:

```text
Increasing
Decreasing
No significant trend
```

---

# 20. Seasonal Trend Analysis

Calculate trends separately for:

```text
Winter
Pre-monsoon
Monsoon
Post-monsoon
```

This is important because an annual trend may hide a strong seasonal signal.

Potential questions:

* Is drying concentrated in the pre-monsoon period?
* Is monsoon soil moisture changing?
* Is post-monsoon moisture changing?
* Which season has the strongest significant trend?

---

# 21. Spatial Hotspot Detection

Identify areas with:

* strongest drying
* strongest wetting
* statistically significant trends
* persistent anomalies
* spatial clusters of change

Outputs may include:

```text
Top 10 drying cells
Top 10 wetting cells
Significant trend clusters
Highest-magnitude regions
```

---

# 22. Extreme Event Detection

Identify unusually dry and wet events.

Potential indicators:

```text
negative soil-moisture anomaly
positive soil-moisture anomaly
persistent multi-month anomalies
large spatial extent
```

For every detected event record:

```text
start date
end date
location
duration
magnitude
affected area
season
```

---

# 23. Cross-Variable Earth-System Evidence

SMAP soil moisture alone shows what happened to soil moisture.

To investigate the wider Earth system, additional variables may be introduced.

Potential variables:

### Precipitation

Question:

> Is soil-moisture change associated with precipitation changes?

### Temperature

Question:

> Are temperature changes associated with soil-moisture changes?

### Vegetation

Potential variables:

```text
NDVI
EVI
LAI
```

Question:

> Does vegetation show a corresponding response?

### Evaporative demand

Potential variables may include:

```text
ET
solar radiation
vapor pressure deficit
```

These relationships must be tested rather than assumed to be causal.

---

# 24. Lag Analysis

Investigate delayed relationships.

Examples:

```text
Rainfall
   ↓
soil moisture response
   ↓
1 month later
```

Potential lag windows:

```text
0 month
1 month
2 months
3 months
```

Possible analyses:

* lag correlation
* seasonal lag relationship
* spatial lag relationship

---

# 25. Detective Case Engine

After scientific analysis, convert important findings into evidence-based cases.

Example:

```text
CASE #001

Region:
Jharkhand

Finding:
Persistent soil-moisture decline

Period:
2015–2026

Strongest season:
Pre-monsoon

Sen slope:
[calculated value]

Mann-Kendall p-value:
[calculated value]

Statistically significant:
YES/NO

Affected area:
[calculated value]

Supporting variables:
[calculated evidence]
```

The case engine should only use calculated evidence.

---

# 26. AI Explanation Layer

AI should be added **after** the scientific engine.

AI's role:

```text
Scientific result
      ↓
Evidence interpretation
      ↓
Human-readable explanation
```

AI should not:

* invent trends
* invent causes
* replace statistical tests
* generate unsupported scientific conclusions

The scientific engine remains the source of truth.

---

# 27. Final Detective Interface

The final application can be organized around a case-based investigation.

Possible structure:

```text
EARTH TREND DETECTIVE

Case #001 — Jharkhand

WHERE?
Spatial trend map

WHEN?
Timeline

HOW MUCH?
Trend magnitude

WHICH SEASON?
Seasonal fingerprint

IS IT SIGNIFICANT?
Statistical evidence

WHAT ELSE CHANGED?
Cross-variable evidence

FINAL FINDING
Evidence-based conclusion
```

---

# 28. Marimo Research Application

Existing Marimo notebooks will eventually be organized into a complete research workflow.

Planned modules:

```text
01 Data Explorer              DONE
02 Cell Explorer              DONE
03 Seasonality                DONE
04 Coverage Detective         DONE
05 Quality Gate               DONE
06 Season Comparison          DONE
07 Spatial Seasonality        DONE

08 Final Dataset QA            PENDING
09 Climatology                 PENDING
10 Anomaly Analysis            PENDING
11 Trend Analysis              PENDING
12 Seasonal Trend              PENDING
13 Spatial Trend               PENDING
14 Extreme Events              PENDING
15 Cross-Variable Analysis     PENDING
16 Detective Cases             PENDING
```

---

# 29. Engineering Cleanup

After scientific analysis is stable:

* clean experimental scripts
* remove obsolete code
* finalize configuration
* improve logging
* improve error handling
* finalize dependencies
* create reproducible setup
* document NASA data access
* document processing parameters
* document scientific methods
* add tests
* finalize project architecture

---

# 30. GitHub / Documentation

GitHub should be updated at major stable checkpoints rather than interrupting the data-processing workflow unnecessarily.

Important documentation should include:

```text
README.md
docs/PROJECT.md
docs/PROJECT_PROGRESS.md
docs/DATA.md
docs/VALIDATION.md
```

The README should eventually reflect the complete dataset and final scientific findings.

---

# 31. Competition Presentation

The final NASA Space Apps story should focus on the **discovery**, not merely the software.

The narrative should follow:

```text
QUESTION
   ↓
WHY THIS REGION?
   ↓
NASA SMAP DATA
   ↓
DATA QUALITY
   ↓
WHAT CHANGED?
   ↓
WHERE?
   ↓
WHEN?
   ↓
HOW MUCH?
   ↓
WHICH SEASON?
   ↓
STATISTICAL SIGNIFICANCE
   ↓
CROSS-VARIABLE EVIDENCE
   ↓
DETECTIVE FINDING
```

Potential NASA Space Apps judging angles:

* Best Use of Science
* Best Use of Data
* Local Impact
* Strong storytelling
* Reproducibility
* Technical implementation

---

# 32. Immediate Roadmap

Current execution priority:

```text
2023  ← CURRENT
  ↓
2024
  ↓
2025
  ↓
2026
  ↓
FULL DATASET QA
  ↓
DATASET FREEZE
  ↓
CLIMATOLOGY
  ↓
ANOMALIES
  ↓
TREND ENGINE
  ↓
SEASONAL TRENDS
  ↓
SPATIAL TRENDS
  ↓
EXTREME EVENTS
  ↓
CROSS-VARIABLE ANALYSIS
  ↓
DETECTIVE CASES
  ↓
AI EXPLANATION
  ↓
FINAL APPLICATION
  ↓
NASA SPACE APPS PRESENTATION
```

---

# 33. Current Project Principle

The project follows an **evidence-first** approach.

The order is:

```text
DATA
  ↓
QUALITY
  ↓
STATISTICS
  ↓
EVIDENCE
  ↓
INTERPRETATION
  ↓
STORY
```

Not:

```text
AI
  ↓
Guess
  ↓
Story
```

This distinction is central to the scientific credibility of EarthTrend Detective.

---

# 34. Current Milestone

## Milestone: Multi-Year SMAP Processing

**Status: IN PROGRESS**

Completed:

```text
2015-04 → 2022-12
93 months
91,512 cell-month records
984 spatial cells
```

Current:

```text
2023 extraction running
```

Target:

```text
2015-04 → 2026
Full multi-year SMAP record
```

Once the final 2026 extraction is complete, the project will transition from **data acquisition** to **scientific discovery**.

---

# 35. Definition of Done

The EarthTrend Detective project will be considered scientifically ready for final presentation when:

* [ ] Full SMAP study period extracted
* [ ] All expected months present
* [ ] All 984 cells validated
* [ ] Observation completeness verified
* [ ] Physical range checks passed
* [ ] Final dataset manifest created
* [ ] Monthly climatology calculated
* [ ] Soil-moisture anomalies calculated
* [ ] Sen's slope calculated
* [ ] Mann-Kendall significance tested
* [ ] Seasonal trends calculated
* [ ] Spatial trend maps generated
* [ ] Significant hotspots identified
* [ ] Extreme events investigated
* [ ] Cross-variable evidence evaluated
* [ ] Detective cases generated
* [ ] Scientific conclusions reviewed
* [ ] Final visualization/dashboard completed
* [ ] AI explanation layer added only where useful
* [ ] README finalized
* [ ] Reproducibility instructions finalized
* [ ] NASA Space Apps presentation prepared

---

## Current Status

**🟢 DATA ENGINEERING: ACTIVE**

**🟢 2015–2022: COMPLETE**

**🔄 2023: RUNNING**

**🟡 2024–2026: PENDING**

**⚪ SCIENTIFIC TREND ANALYSIS: NEXT MAJOR PHASE AFTER DATA FREEZE**

**⚪ FINAL DETECTIVE APPLICATION: FUTURE PHASE**
