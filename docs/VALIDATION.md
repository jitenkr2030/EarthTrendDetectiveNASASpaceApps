# EarthTrend Detective — Validation Record

This document records reproducible validation checks performed
during development.

---

# Validation 01 — NASA Dataset Access

Status: **PASS**

NASA SMAP L4 granules were successfully accessed through
Earthdata OPeNDAP.

Dataset:

`SPL4SMGP`

Version:

`008`

Primary variable:

`/Geophysical_Data/sm_surface`

The variable was confirmed to exist inside the
`Geophysical_Data` group.

---

# Validation 02 — SMAP Grid Dimensions

Status: **PASS**

Confirmed grid dimensions:

- Y: 1624
- X: 3856

Latitude and longitude coordinate arrays were successfully
read from the dataset.

---

# Validation 03 — Jharkhand Bounding Box

Status: **PASS**

Initial bounding box:

Latitude:

21.9–25.3

Longitude:

83.3–87.9

Candidate cells:

**2200**

This stage is considered a broad spatial filter only and is
not treated as the final Jharkhand boundary.

---

# Validation 04 — Jharkhand Polygon Mask

Status: **PASS**

An India ADM1 boundary dataset was used to identify the
Jharkhand state polygon.

SMAP cell-center point-in-polygon filtering produced:

- Input cells: 2200
- Inside Jharkhand: 984
- Outside Jharkhand: 1216

Inside percentage:

44.73%

Master mask:

`data/jharkhand_smap_mask.csv`

---

# Validation 05 — Master Mask Integrity

Status: **PASS**

File:

`data/jharkhand_smap_mask.csv`

Checks:

- Total rows: 984
- Unique `(row, col)` cells: 984
- Duplicate cells: 0
- Latitude values present
- Longitude values present

Spatial range:

Latitude:

22.026018–25.256832

Longitude:

83.418053–87.899384

---

# Validation 06 — April 2015 Granule Inventory

Status: **PASS**

Month:

April 2015

Granules:

**240**

Expected approximate temporal sampling:

3-hourly

Expected observations:

30 × 8 = 240

The inventory contained 240 April 2015 granules.

---

# Validation 07 — April 2015 Spatial Extraction

Status: **PASS**

Output:

`data/smap_jharkhand_2015_04_masked_v2.csv`

Results:

Rows:

984

Unique cells:

984

Duplicate cells:

0

Cells with valid monthly soil moisture:

984

Missing cells:

0

Observations per cell:

240

---

# Validation 08 — April 2015 Soil Moisture Range

Status: **PASS**

Mean:

0.12465333 m3/m3

Minimum:

0.06156727 m3/m3

Maximum:

0.23643617 m3/m3

All extracted values fall within the expected physical
valid range used by the extraction pipeline.

---

# Validation 09 — Complete April Month

Status: **PASS**

All 240 April granules were processed successfully.

No granule failure remained at the end of the successful run.

All 984 master-mask cells received 240 valid observations.

---

# Validation 10 — Network Failure Recovery

Status: **OBSERVED**

During one extraction attempt, the NASA OPeNDAP hostname
temporarily failed DNS resolution.

Error:

`Failed to resolve 'opendap.earthdata.nasa.gov'`

The issue was external to the spatial mask and data-processing
logic.

A later run completed all 240 granules successfully.

Engineering consequence:

The production pipeline must support retry and checkpointing.

---

# Scientific Interpretation of Current Validation

These validations establish that the data extraction pipeline
can successfully:

1. Access NASA SMAP data.
2. Identify the required soil-moisture variable.
3. Locate the Jharkhand spatial region.
4. Apply the actual Jharkhand state boundary.
5. Maintain a reusable 984-cell spatial mask.
6. Extract April 2015 SMAP observations.
7. Produce a complete cell-level monthly dataset.

These validations do NOT establish a long-term soil-moisture
trend.

Trend analysis requires a sufficiently long and consistently
processed time series.

---

# Current Validation Status

Overall:

**PHASE 1–5: PASS**

Long-term trend analysis:

**NOT YET VALIDATED**

---

# Validation 11 — May 2015 Production Extraction

Status: **PASS**

Month:

`2015-05`

Expected granules:

**248**

Initial extraction:

- Successful: 247
- Failed: 1

The failed granule produced:

`ConnectionAbortedError(103, 'Software caused connection abort')`

The granule was subsequently retried independently.

Recovery result:

- OPeNDAP access: PASS
- SMAP variable access: PASS
- Grid shape: 44 × 50
- Jharkhand cells selected: 984
- Valid cells: 984
- Invalid cells: 0

The recovered observation was incorporated into the
existing monthly checkpoint.

Final dataset validation:

- Rows: 984
- Unique cells: 984
- Duplicate cells: 0
- Observations per cell: 248
- Expected observations: 248
- Coverage: 100%
- Missing soil moisture: 0
- Soil moisture range: 0.03969914–0.25502342
- Spatial monthly mean: 0.10714572 m3 m-3
- Coordinate validation: PASS
- Overall dataset validation: PASS

Output:

`data/monthly/2015-05.csv`

Scientific note:

The recovery process changed the monthly spatial mean from
0.10717712 to 0.10714572 m3 m-3. The corrected value is retained
as the final May 2015 result.

This validation demonstrates successful recovery from a
transient network failure. It does not constitute evidence
of a long-term trend.
