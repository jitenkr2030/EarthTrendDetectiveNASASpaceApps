# 🌍 EarthTrend Detective

### Detecting Soil Moisture Trends Across Jharkhand, India Using NASA SMAP Data

**NASA Space Apps Challenge 2026 Project**

EarthTrend Detective is a scientific data-analysis project that uses **NASA SMAP (Soil Moisture Active Passive)** satellite observations to study how surface soil moisture varies across **Jharkhand, India** over time and space.

The project transforms large-scale NASA satellite observations into a validated, analysis-ready dataset covering **984 spatial cells across Jharkhand**, with the goal of identifying seasonal patterns, anomalies, spatial differences, and eventually statistically robust long-term trends.

---

## 🎯 Problem

Soil moisture is an important indicator of environmental and agricultural conditions.

Changes in soil moisture can be associated with:

* rainfall and monsoon variability
* drought conditions
* agricultural water availability
* seasonal changes
* land-surface processes
* hydrological variability
* extreme wet or dry periods

Satellite observations allow us to study these changes over large geographic areas without relying only on ground-based measurement stations.

The challenge is to convert large volumes of satellite observations into reliable information that can be analyzed at the regional and local level.

---

## 🛰️ NASA Data

This project uses the **NASA SMAP Level-4 Global 3-hourly 9 km Surface and Root-Zone Soil Moisture product (SPL4SMGP)**.

### Dataset

* **NASA mission:** SMAP
* **Collection:** SPL4SMGP
* **Version:** 008
* **Variable:** `sm_surface`
* **Depth:** approximately 0–5 cm surface layer
* **Temporal resolution:** 3-hourly
* **Spatial resolution:** approximately 9 km
* **Unit:** `m³/m³`
* **Data access:** NASA Earthdata / OPeNDAP

The project does not download every large NASA granule unnecessarily. Instead, the pipeline accesses the required observations and extracts the cells covering Jharkhand.

---

# 🗺️ Study Area

The current study focuses on:

**Jharkhand, India**

The Jharkhand administrative boundary is used to identify SMAP grid cells whose centers fall inside the state boundary.

### Spatial grid

The final study area contains:

> **984 SMAP grid cells**

Each cell is represented by its latitude and longitude.

This allows the project to move beyond a single state-level average and investigate spatial differences across Jharkhand.

---

# 🔬 Research Methodology

The project follows a reproducible scientific workflow:

```text
NASA SMAP Data
      │
      ▼
NASA Earthdata / CMR Inventory
      │
      ▼
SMAP Granules
      │
      ▼
Jharkhand Spatial Mask
      │
      ▼
984 Grid Cells
      │
      ▼
3-hourly Observations
      │
      ▼
Monthly Aggregation
      │
      ▼
Data Validation
      │
      ▼
Quality Gate
      │
      ├───────────────┐
      ▼               ▼
Seasonality      Spatial Analysis
      │               │
      └───────┬───────┘
              ▼
        Anomaly Analysis
              │
              ▼
      Long-term Trend Analysis
              │
              ▼
       Scientific Interpretation
```

---

# 📊 Current Dataset

The current validated dataset covers:

**April 2015 → December 2016**

This currently represents:

* **21 monthly datasets**
* **984 spatial cells per month**
* **20,664 cell-month observations**
* **100% spatial coverage for completed months**
* validated observation counts
* validated coordinates
* validated soil-moisture ranges
* no duplicate grid cells

The dataset will be extended to additional years before making long-term trend conclusions.

---

# ✅ Data Quality Gate

Data quality is treated as a core part of the project rather than an afterthought.

The automated quality gate checks:

* required columns
* expected number of spatial cells
* duplicate grid cells
* month/file consistency
* missing soil-moisture values
* valid soil-moisture range
* valid coordinates
* observation counts
* spatial coverage
* consistency with the reference spatial grid
* missing months

### Current result

```text
Expected months : 21
Files inspected : 21
PASS             : 21
FAIL             : 0
Missing months   : 0
```

**Current quality gate: PASS**

---

# 🌦️ Initial Findings

The first 21 months provide an exploratory picture of seasonal soil-moisture behavior.

The current analysis shows:

### Monsoon

Surface soil moisture is substantially higher during the monsoon period, particularly during July–September.

### Pre-monsoon

Lower soil moisture values are generally observed during the pre-monsoon period.

### Available-period extremes

The current dataset identifies:

* **Wettest available month:** September 2016
* **Driest available month:** April 2016

These observations describe the current dataset and are **not yet interpreted as long-term climate trends**.

---

# 📈 Seasonal Analysis

For exploratory analysis, the project currently groups months into:

| Season       | Months           |
| ------------ | ---------------- |
| Winter       | January–February |
| Pre-monsoon  | March–May        |
| Monsoon      | June–September   |
| Post-monsoon | October–December |

This grouping is used for exploratory comparison and does not by itself represent a formal climatological classification.

Current available-period results indicate substantially higher surface soil moisture during the monsoon compared with the pre-monsoon period.

---

# 🧪 Scientific Approach

A key principle of EarthTrend Detective is:

> **Do not call a short-term seasonal pattern a long-term climate trend.**

The current 21-month dataset is useful for:

* validating the processing pipeline
* understanding seasonal behavior
* identifying spatial variability
* testing anomaly calculations
* developing visualization methods

However, it is not sufficient by itself for robust long-term trend conclusions.

The project therefore plans to extend the dataset across multiple years before performing final trend analysis.

---

# 📐 Planned Trend Detection

Once a sufficiently long time series has been processed, the project will investigate:

### Cell-level trends

Each of the 984 spatial cells will be analyzed independently.

Potential methods include:

* Seasonal Mann-Kendall analysis
* Sen's slope
* autocorrelation-aware significance testing
* seasonal anomaly analysis
* trend magnitude estimation

The exact statistical method will be selected based on the properties of the final time series.

The goal is to distinguish:

```text
Seasonal variability
        ↓
Year-to-year variability
        ↓
Persistent anomalies
        ↓
Long-term trend
```

rather than treating every increase or decrease as a trend.

---

# 🗺️ Planned Spatial Analysis

Future analysis will generate spatial maps showing:

* mean surface soil moisture
* seasonal soil moisture
* spatial variability
* anomalies
* dry/wet areas
* trend magnitude
* statistical significance
* persistent change hotspots

This will allow the project to answer questions such as:

> Which parts of Jharkhand are consistently wetter or drier?

> Which areas show unusual soil-moisture anomalies?

> Are changes spatially uniform or concentrated in specific regions?

> Which locations show statistically significant long-term changes?

---

# 🧰 Technology Stack

### Programming

* Python 3
* NumPy
* Pandas
* SciPy
* Xarray
* NetCDF4
* H5py
* GeoPandas
* Shapely
* Rasterio
* Matplotlib

### NASA / Earth Observation

* NASA Earthdata
* NASA CMR
* NASA SMAP
* OPeNDAP

### Research Environment

* Marimo
* Jupyter-compatible Python ecosystem

### Development Environment

The current development environment is Ubuntu running inside a Termux/PRoot environment.

---

# 📁 Project Structure

```text
EarthTrendDetective/
│
├── data/
│   ├── jharkhand_smap_mask.csv
│   ├── smap_granule_inventory.csv
│   └── monthly/
│       └── YYYY-MM.csv
│
├── src/
│   ├── inventory_smap.py
│   ├── extract_monthly_production.py
│   ├── recover_failed_granules.py
│   ├── run_monthly_pipeline.py
│   └── trend_engine.py
│
├── research/
│   ├── 01_earthtrend_data_explorer.py
│   ├── 02_cell_explorer.py
│   ├── 03_seasonality_analysis.py
│   ├── 04_coverage_detective.py
│   ├── 05_quality_gate.py
│   └── 06_season_comparison.py
│
├── docs/
│   ├── PROJECT.md
│   ├── DATA.md
│   ├── PROGRESS.md
│   └── VALIDATION.md
│
├── .gitignore
├── README.md
└── requirements.txt
```

---

# ⚙️ Reproducibility

The project is designed so that the data-processing workflow can be reproduced.

Typical workflow:

```bash
# Clone repository
git clone https://github.com/jitenkr2030/EarthTrendDetectiveNASASpaceApps.git

cd EarthTrendDetectiveNASASpaceApps

# Create environment
python3 -m venv .venv

# Activate
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

NASA Earthdata authentication is required for accessing protected NASA data services.

Credentials should **never** be committed to GitHub.

---

# 🚧 Current Development Status

### Completed

* [x] Project research design
* [x] NASA SMAP dataset identification
* [x] NASA CMR inventory
* [x] Jharkhand spatial boundary
* [x] 984-cell study grid
* [x] Monthly extraction pipeline
* [x] Failed-granule recovery
* [x] Monthly validation
* [x] Automated quality gate
* [x] Seasonality analysis
* [x] Seasonal comparison

### In Progress

* [ ] Spatial baseline analysis
* [ ] Per-cell statistics
* [ ] Spatial seasonality
* [ ] Multi-year data processing
* [ ] Cell-level anomaly analysis

### Planned

* [ ] Long-term trend detection
* [ ] Seasonal Mann-Kendall analysis
* [ ] Sen's slope estimation
* [ ] Autocorrelation-aware significance testing
* [ ] Spatial trend maps
* [ ] Dry/wet hotspot detection
* [ ] Final scientific interpretation
* [ ] NASA Space Apps presentation/demo

---

# ⚠️ Scientific Limitations

The project is still under development.

Important limitations include:

1. The currently processed record is only 21 months long.
2. A 21-month record cannot establish a reliable long-term climate trend.
3. Seasonal patterns should not be confused with climate trends.
4. Some calendar months currently contain observations from only one year.
5. Statistical significance testing will require a substantially longer time series.
6. Satellite observations represent modeled/assimilated soil-moisture estimates and should be interpreted with appropriate uncertainty.
7. The current study uses the surface soil-moisture variable and does not represent the entire soil profile.

These limitations will be explicitly considered in the final analysis.

---

# 🌎 Vision

EarthTrend Detective aims to turn complex satellite observations into an understandable environmental monitoring system.

The long-term objective is to build a framework that can answer:

> **Where is the land getting wetter, drier, or more variable — and how confident are we in that change?**

Although the current study focuses on Jharkhand, the processing architecture can eventually be adapted to other regions.

---

# 🏆 NASA Space Apps Challenge 2026

EarthTrend Detective is being developed for the **NASA Space Apps Challenge 2026**.

The project combines:

* NASA Earth observation data
* geospatial analysis
* statistical analysis
* reproducible scientific workflows
* data visualization
* environmental research

The emphasis is on making scientifically defensible conclusions rather than simply producing visualizations.

---

# 👨‍💻 Author

**Jitender Kumar**

GitHub: `jitenkr2030`

Project:

**EarthTrend Detective — NASA Space Apps 2026**

---

## 📜 License

This project is intended for research, educational, and open-source development purposes.

NASA datasets remain subject to their respective NASA data-use and distribution policies.

---

## ⭐ Project Status

**Research prototype — actively developing**

Current milestone:

> **21 validated monthly datasets × 984 Jharkhand cells = 20,664 cell-month observations**

Next major milestone:

> **Extend the time series and perform scientifically robust spatial trend analysis.**
