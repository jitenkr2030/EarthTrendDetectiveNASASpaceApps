# EarthTrend Detective — Development Progress

## Project

NASA Space Apps 2026

Challenge:

**Be An Earth System Trend Detective!**

Study region:

**Jharkhand, India**

Primary variable:

**SMAP L4 `sm_surface`**

---

# Phase 1 — Project Definition

Status: **COMPLETE**

Defined the initial research question:

> Is surface soil moisture changing over time in Jharkhand?
> If it is changing, where, by how much, and is the change
> statistically significant?

Important scientific rule:

The analysis must not assume that a trend exists.

Possible result:

- Increasing
- Decreasing
- No statistically significant trend

---

# Phase 2 — NASA Dataset Discovery

Status: **COMPLETE**

Dataset:

NASA SMAP L4 Global 3-hourly 9 km EASE-Grid Surface and
Root Zone Soil Moisture Geophysical Data.

Collection:

`SPL4SMGP`

Version:

`008`

Collection concept:

`C3480440870-NSIDC_CPRD`

Primary variable:

`/Geophysical_Data/sm_surface`

Description:

Top layer soil moisture, approximately 0–5 cm.

Unit:

`m3 m-3`

Access method:

NASA Earthdata OPeNDAP.

Reason:

Avoid downloading complete large HDF5 granules when only a
small spatial subset is required.

---

# Phase 3 — SMAP Spatial Grid Investigation

Status: **COMPLETE**

SMAP grid dimensions identified:

- Y dimension: 1624
- X dimension: 3856

Approximate Jharkhand bounding box:

Latitude:

21.9–25.3

Longitude:

83.3–87.9

Bounding-box extraction produced:

**2200 candidate cells**

This was only an initial spatial selection.

---

# Phase 4 — Jharkhand Boundary Mask

Status: **COMPLETE**

A state-level India ADM1 boundary dataset was used.

The Jharkhand polygon was selected from the ADM1 boundary data.

SMAP cell centers were tested against the Jharkhand polygon.

Result:

- Bounding-box cells: 2200
- Cells inside Jharkhand: 984
- Cells outside Jharkhand: 1216

Final percentage of candidate cells inside Jharkhand:

44.73%

A reusable master mask was created:

`data/jharkhand_smap_mask.csv`

Master mask columns:

- row
- col
- latitude
- longitude

Master mask validation:

- Cells: 984
- Unique cells: 984
- Duplicate cells: 0

---

# Phase 5 — April 2015 Extraction Test

Status: **COMPLETE**

Test month:

`2015-04`

April 2015 inventory:

**240 granules**

Expected approximately:

30 days × 8 observations/day = 240 observations.

The monthly extraction used the 984-cell Jharkhand master mask.

Output:

`data/smap_jharkhand_2015_04_masked_v2.csv`

Result:

- Rows: 984
- Unique cells: 984
- Duplicate cells: 0
- Cells with data: 984
- Observations per cell: 240
- Missing soil moisture cells: 0

Spatial range:

Latitude:

22.026018–25.256832

Longitude:

83.418053–87.899384

Soil moisture:

Mean: 0.12465333 m3/m3

Minimum: 0.06156727 m3/m3

Maximum: 0.23643617 m3/m3

Validation status:

**PASS**

---

# Phase 6 — Network Reliability Observation

Status: **IDENTIFIED**

During OPeNDAP processing a temporary DNS/network failure
occurred while accessing:

`opendap.earthdata.nasa.gov`

The pipeline subsequently completed successfully after retrying.

This demonstrated that the long-running production pipeline
should include:

- Automatic retry
- Checkpointing
- Failed-granule logging
- Resume capability

These features will be implemented before processing the
complete long-term dataset.

---

# Phase 7 — Long-Term Monthly Dataset

Status:

**NOT STARTED**

Planned study period:

2015–2026, subject to final inventory boundaries.

Target structure:

One record per:

`month × SMAP cell`

Expected approximately:

984 cells × number of valid months.

The exact number will be determined from the final inventory.

---

# Phase 8 — Trend Analysis

Status:

**NOT STARTED**

Planned analysis:

- Monthly time series
- Seasonal handling
- Missing-data/coverage checks
- Autocorrelation consideration
- Trend significance
- Sen's slope
- Confidence interval

No trend conclusion has been made yet.

---

# Phase 9 — Earth System Context

Status:

**PLANNED**

Potential additional variables:

- Rainfall
- Vegetation
- Temperature
- Evapotranspiration

These will be used to investigate relationships and divergent
regional behaviour.

Correlation will not automatically be interpreted as causation.

---

# Phase 10 — Final Visualization

Status:

**PLANNED**

Planned outputs:

- Jharkhand soil-moisture trend map
- Cell-level trend statistics
- Regional time-series plots
- Significant/non-significant trend visualization
- Earth-system comparison
- Scientific explanation layer

---

# Current Milestone

**April 2015 spatial extraction and validation completed successfully.**

The project has moved from:

NASA data discovery

to:

validated Jharkhand spatial data extraction.

Next engineering milestone:

**Reliable long-term monthly extraction pipeline.**

---

# Phase 7A — Production Monthly Extraction Test

Status: **COMPLETE**

Month tested:

**2015-05**

Production extractor successfully processed the May 2015
SMAP L4 granules for the 984-cell Jharkhand mask.

Expected granules:

**248**

Initial run:

- Successful: 247
- Failed: 1
- Failure type: temporary connection abort

The failed granule was:

`SMAP_L4_SM_gph_20150526T163000_Vv8010_001.h5`

The granule was independently retried and successfully
accessed through NASA Earthdata OPeNDAP.

Recovery validation:

- Grid shape: 44 × 50
- Selected Jharkhand cells: 984
- Valid cells: 984
- Invalid cells: 0

The recovered observation was added to the existing
checkpoint without reprocessing the entire month.

Final May 2015 dataset:

- Cells: 984
- Observations per cell: 248
- Expected observations: 248
- Coverage: 100%
- Missing monthly values: 0
- Validation: PASS

Output:

`data/monthly/2015-05.csv`

Checkpoint:

`data/checkpoints/2015-05.npz`

This milestone demonstrates that the production extraction
pipeline can recover from a transient network failure while
preserving the accumulated processing state.

Important:

This validation establishes data extraction and quality
control for May 2015. It does not establish a long-term
soil-moisture trend.

## Phase 7B — 2015 Monthly Production Dataset

**Status: COMPLETE for April–December 2015**

Validated monthly production datasets currently available:

- 2015-04 — 240 observations/cell — PASS
- 2015-05 — 248 observations/cell — PASS
- 2015-06 — 240 observations/cell — PASS
- 2015-07 — available
- 2015-08 — available
- 2015-09 — available
- 2015-10 — available
- 2015-11 — available
- 2015-12 — available

The April–June datasets were independently validated through the production validation pipeline.

The September–December datasets are present in `data/monthly/` and should be independently validated before being treated as final scientific inputs.

### Marimo research layer

Initial research notebooks created:

- `research/01_earthtrend_data_explorer.py`
- `research/02_cell_explorer.py`
- `research/03_seasonality_analysis.py`

These notebooks provide interactive exploration but do not replace the validated data-processing pipeline.

### Scientific status

No long-term soil-moisture trend has been claimed.

Seasonality must be characterized using a sufficiently long multi-year record before final trend inference.

