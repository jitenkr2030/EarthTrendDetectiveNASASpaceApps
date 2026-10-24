# EarthTrend Detective — Judge Q&A

## What problem does the project address?

It investigates how NASA satellite-derived surface soil moisture varies over time and space across Jharkhand, India, and whether the analyzed record supports a statistically significant long-term trend.

## What is the main finding?

The first-pass state-level trend estimate is slightly negative but not statistically significant (Sen's slope approximately -0.000140 m³/m³/year; p approximately 0.931). The analysis did not detect a significant monotonic state-wide drying trend. It also found a strong same-month rainfall/soil-moisture anomaly association and episodic extremes.

## Does that mean Jharkhand has no drought risk?

No. A non-significant trend test is not proof of no risk. Drought can be local, seasonal, episodic, or driven by factors not captured by this single trend test. The project reports what the tested record supports and does not claim that drought risk is absent.

## Why use NASA SMAP?

The project uses NASA SMAP Level-4 SPL4SMGP Version 008, variable `sm_surface`, an estimated surface soil-moisture variable representing approximately the top 0–5 cm. It provides a consistent satellite-derived record for regional analysis.

## How much data was analyzed?

The SMAP analysis spans April 2015 through September 2026: 138 monthly periods, 984 Jharkhand grid cells, and 135,792 cell-month records. The common GPM rainfall comparison covers 126 months through September 2025.

## What does r approximately 0.714 mean?

It indicates a strong positive linear association between standardized monthly soil-moisture and rainfall anomalies in the analyzed common period. The project reports that this association remains statistically significant after its autocorrelation-aware effective-sample-size adjustment. It does not establish causation.

## What do 5,917 extremes mean?

They are extreme cell-month observations under the study's selected thresholds: 1,656 dry and 4,261 wet. They are not 5,917 separate droughts, floods, or independent events.

## Are the 984 spatial correlations independent?

No. The mapping relates 984 SMAP cells to 703 coarser GPM cells. Spatial dependence and shared rainfall cells limit interpreting these correlations as independent experiments. FDR correction does not remove every spatial-dependence concern.

## Is the trend analysis fully corrected for seasonality and autocorrelation?

No. The long-term trend analysis is a first-pass Kendall/Mann-Kendall-style assessment. The seasonal analysis is also not a fully autocorrelation-corrected Seasonal Mann-Kendall implementation. This is an explicit limitation and a target for further sensitivity assessment.

## Can this predict drought or crop yield?

The current prototype is a retrospective soil-moisture analysis, not an operational drought-warning system or crop-yield model. It does not directly measure crop outcomes, groundwater, or impacts on individual farms.

## What is the next improvement?

Improve trend sensitivity analysis for seasonality and serial autocorrelation, handle spatial dependence more carefully, and compare with independent ground observations where suitable data are available.

## What is reproducible?

The repository includes the research workflow, evidence summary, analysis outputs, and a live dashboard. Re-running protected NASA data acquisition may require authorized NASA Earthdata access.

## Are you claiming NASA endorsement or competition success?

No. The project uses NASA Earth observation data and is being developed for the NASA Space Apps Challenge 2026. Data use and participation do not imply NASA endorsement, finalist status, or winning status.
