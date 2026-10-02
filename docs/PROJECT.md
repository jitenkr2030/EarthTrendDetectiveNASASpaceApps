# EarthTrend Detective

## NASA Space Apps 2026

Challenge:

**Be An Earth System Trend Detective!**

## Project Goal

Earth observation data ka use karke Jharkhand, India mein
soil moisture ke long-term spatial aur temporal changes ko
scientifically investigate karna.

## Core Research Question

> Is surface soil moisture changing over time in Jharkhand?
> If it is changing, where, by how much, and is the change
> statistically significant?

## Important Principle

Project kisi predetermined result ko prove karne ke liye nahi hai.

Possible outcomes:

- Increasing trend
- Decreasing trend
- No statistically significant trend

No significant trend is also a valid scientific result.

## Study Region

Jharkhand, India.

The analysis uses the official state boundary to identify
SMAP grid cells whose cell centers fall inside Jharkhand.

## Primary Earth Observation Dataset

NASA SMAP L4 Global 3-hourly 9 km EASE-Grid Surface and
Root Zone Soil Moisture Geophysical Data.

Collection:

SPL4SMGP

Version:

008

Primary variable:

sm_surface

Meaning:

Top-layer surface soil moisture, approximately 0–5 cm.

Unit:

m3/m3

Approximate spatial resolution:

9 km

## Current Status

The spatial extraction pipeline has been validated for
April 2015.

Results:

- Jharkhand SMAP cells: 984
- April 2015 granules: 240
- Observations per cell: 240
- Cells with valid monthly data: 984
- Missing monthly cells: 0
- Validation status: PASS

## Current Scientific Limitation

April 2015 is only a pipeline validation month.

No long-term soil-moisture trend has been claimed yet.

The next stage is to build a consistent monthly time series
across the complete study period and then apply statistical
trend analysis.
