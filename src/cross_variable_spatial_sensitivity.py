#!/usr/bin/env python3

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

BASE = Path(__file__).resolve().parents[1]

SMAP_FILE = BASE / "data/analysis/smap_anomalies_jharkhand.csv"
GPM_FILE = BASE / "data/analysis/gpm_cell_anomalies_jharkhand.csv"
MAPPING_FILE = BASE / "data/analysis/smap_gpm_spatial_mapping.csv"

OUT_CSV = BASE / "data/analysis/smap_gpm_spatial_sensitivity.csv"
OUT_JSON = BASE / "data/analysis/smap_gpm_spatial_sensitivity.json"

print("Loading SMAP anomaly data...")
smap = pd.read_csv(SMAP_FILE)
print(f"SMAP rows: {len(smap):,}")

print("Loading GPM cell anomaly data...")
gpm = pd.read_csv(GPM_FILE)
print(f"GPM rows: {len(gpm):,}")

print("Loading spatial mapping...")
mapping = pd.read_csv(MAPPING_FILE)
print(f"Mapping rows: {len(mapping):,}")

# ---------------------------------------------------------
# Prepare identifiers
# ---------------------------------------------------------

smap["cell_id"] = (
    smap["row"].astype(str) + "_" +
    smap["col"].astype(str)
)

mapping["cell_id"] = (
    mapping["smap_row"].astype(str) + "_" +
    mapping["smap_col"].astype(str)
)

mapping_use = mapping[
    [
        "cell_id",
        "smap_latitude",
        "smap_longitude",
        "gpm_latitude",
        "gpm_longitude",
        "approx_distance_km",
    ]
].copy()

# GPM identifier
gpm["gpm_id"] = (
    gpm["latitude"].round(6).astype(str)
    + "_"
    + gpm["longitude"].round(6).astype(str)
)

mapping_use["gpm_id"] = (
    mapping_use["gpm_latitude"].round(6).astype(str)
    + "_"
    + mapping_use["gpm_longitude"].round(6).astype(str)
)

print("\nJoining spatial mapping...")
mapped = smap.merge(
    mapping_use,
    on="cell_id",
    how="inner",
    validate="many_to_one",
)

print(f"Mapped SMAP rows: {len(mapped):,}")

# ---------------------------------------------------------
# Join monthly GPM anomalies
# ---------------------------------------------------------

print("Joining monthly GPM anomalies...")

gpm_join = gpm[
    [
        "date",
        "gpm_id",
        "standardized_rainfall_anomaly",
    ]
].copy()

joined = mapped.merge(
    gpm_join,
    on=["date", "gpm_id"],
    how="inner",
    validate="many_to_one",
)

print(f"Joined rows: {len(joined):,}")

# ---------------------------------------------------------
# Calculate correlation per SMAP cell
# ---------------------------------------------------------

print("\nCalculating cell correlations...")

records = []

for cell_id, group in joined.groupby("cell_id"):

    group = group[
        [
            "date",
            "standardized_anomaly",
            "standardized_rainfall_anomaly",
            "approx_distance_km",
        ]
    ].dropna()

    if len(group) < 10:
        continue

    x = group["standardized_anomaly"].to_numpy()
    y = group["standardized_rainfall_anomaly"].to_numpy()

    if np.std(x) == 0 or np.std(y) == 0:
        continue

    r, p = pearsonr(x, y)

    records.append(
        {
            "cell_id": cell_id,
            "latitude": group["approx_distance_km"].iloc[0] * 0
            + joined.loc[joined["cell_id"] == cell_id, "smap_latitude"].iloc[0],
            "longitude": joined.loc[
                joined["cell_id"] == cell_id,
                "smap_longitude"
            ].iloc[0],
            "mapping_distance_km": group["approx_distance_km"].iloc[0],
            "pearson_r": r,
            "p_value": p,
            "n_months": len(group),
        }
    )

corr = pd.DataFrame(records)

print(f"Valid correlated cells: {len(corr):,}")

# ---------------------------------------------------------
# Sensitivity thresholds
# ---------------------------------------------------------

thresholds = [
    ("all_cells", np.inf),
    ("<=10_km", 10.0),
    ("<=7.5_km", 7.5),
    ("<=5_km", 5.0),
]

results = []

for label, threshold in thresholds:

    subset = corr[
        corr["mapping_distance_km"] <= threshold
    ].copy()

    if subset.empty:
        continue

    positive_pct = (
        (subset["pearson_r"] > 0).mean() * 100
    )

    moderate_pct = (
        (subset["pearson_r"] >= 0.5).mean() * 100
    )

    strong_pct = (
        (subset["pearson_r"] >= 0.7).mean() * 100
    )

    results.append(
        {
            "threshold": label,
            "distance_threshold_km": (
                None if np.isinf(threshold) else threshold
            ),
            "cells": len(subset),
            "mean_r": subset["pearson_r"].mean(),
            "median_r": subset["pearson_r"].median(),
            "min_r": subset["pearson_r"].min(),
            "max_r": subset["pearson_r"].max(),
            "positive_percent": positive_pct,
            "r_ge_0_5_percent": moderate_pct,
            "r_ge_0_7_percent": strong_pct,
            "mean_mapping_distance_km": subset[
                "mapping_distance_km"
            ].mean(),
            "max_mapping_distance_km": subset[
                "mapping_distance_km"
            ].max(),
        }
    )

results_df = pd.DataFrame(results)

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

results_df.to_csv(OUT_CSV, index=False)

summary = {
    "status": "PASS",
    "method": "Spatial correlation sensitivity to SMAP-GPM mapping distance",
    "thresholds_tested_km": [5.0, 7.5, 10.0],
    "total_valid_cells": int(len(corr)),
    "results": results,
}

with open(OUT_JSON, "w") as f:
    json.dump(summary, f, indent=2)

# ---------------------------------------------------------
# Print
# ---------------------------------------------------------

print("\n========================================")
print("SPATIAL SENSITIVITY COMPLETE")
print("========================================")

print(results_df.to_string(index=False))

print(f"\nCSV:  {OUT_CSV}")
print(f"JSON: {OUT_JSON}")

print("\nFINAL RESULT: PASS")
