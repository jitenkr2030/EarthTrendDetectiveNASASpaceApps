# Data Documentation

## Primary Dataset

NASA SMAP L4 Global 3-hourly 9 km EASE-Grid Surface and
Root Zone Soil Moisture Geophysical Data.

Collection short name:

SPL4SMGP

Version:

008

## Variable

`/Geophysical_Data/sm_surface`

Description:

Top layer soil moisture (0–5 cm).

Unit:

m3 m-3

## Temporal Resolution

SMAP L4 observations are approximately 3-hourly.

For April 2015:

240 granules were identified.

30 days × 8 observations/day = 240 expected observations.

## Spatial Grid

SMAP uses the EASE-Grid 2.0 global grid.

The analysis extracts only the grid region covering Jharkhand.

## Jharkhand Spatial Mask

Initial geographic bounding box:

Latitude: approximately 21.9–25.3
Longitude: approximately 83.3–87.9

This produced 2200 candidate grid cells.

A Jharkhand ADM1 polygon was then used to identify cells
whose centers fall inside the state boundary.

Final master mask:

984 cells.

File:

`data/jharkhand_smap_mask.csv`

Columns:

- row
- col
- latitude
- longitude

## Data Access

NASA Earthdata OPeNDAP is used instead of downloading complete
HDF5 granules.

Only the required spatial subset is requested from each
granule.

## Important Timestamp Note

CMR inventory timestamps are used for granule discovery.

The internal SMAP dataset `time` variable represents the
observation timestamp and should be preferred for scientific
time-series construction.

## Data Quality

SMAP fill/invalid values are excluded from calculations.

Valid surface soil moisture values are restricted to the
dataset's physical valid range.
