from pathlib import Path
import json

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr


# ============================================================
# CONFIG
# ============================================================

BASE = Path("/root/earthtrend-detective")

SMAP_FILE = BASE / "data/analysis/smap_anomalies_jharkhand.csv"
GPM_FILE = BASE / "data/analysis/gpm_cell_anomalies_jharkhand.csv"
MAPPING_FILE = BASE / "data/analysis/smap_gpm_spatial_mapping.csv"

OUTPUT_FILE = BASE / "data/analysis/smap_gpm_spatial_correlation.csv"
JSON_FILE = BASE / "data/analysis/smap_gpm_spatial_correlation.json"

ALPHA = 0.05


# ============================================================
# BENJAMINI-HOCHBERG FDR
# ============================================================

def benjamini_hochberg(pvalues, alpha=0.05):
    """
    Benjamini-Hochberg false-discovery-rate correction.
    """

    pvalues = np.asarray(pvalues, dtype=float)

    n = len(pvalues)

    order = np.argsort(pvalues)

    sorted_p = pvalues[order]

    adjusted_sorted = np.empty(n, dtype=float)

    running = 1.0

    for i in range(n - 1, -1, -1):

        rank = i + 1

        value = sorted_p[i] * n / rank

        running = min(running, value)

        adjusted_sorted[i] = running

    adjusted_p = np.empty(n, dtype=float)

    adjusted_p[order] = np.minimum(
        adjusted_sorted,
        1.0,
    )

    reject = adjusted_p < alpha

    return reject, adjusted_p


# ============================================================
# LOAD SMAP
# ============================================================

print("\nLoading SMAP anomaly data...")

smap = pd.read_csv(SMAP_FILE)

smap["date"] = pd.to_datetime(smap["date"])

required_smap = {
    "date",
    "latitude",
    "longitude",
    "standardized_anomaly",
    "anomaly",
}

missing = required_smap - set(smap.columns)

if missing:
    raise ValueError(
        f"SMAP file missing columns: {sorted(missing)}"
    )

print(f"SMAP rows: {len(smap):,}")


# ============================================================
# LOAD GPM CELL ANOMALIES
# ============================================================

print("Loading GPM cell anomaly data...")

gpm = pd.read_csv(GPM_FILE)

gpm["date"] = pd.to_datetime(gpm["date"])

required_gpm = {
    "date",
    "latitude",
    "longitude",
    "rainfall_mm_month",
    "rainfall_anomaly_mm",
    "standardized_rainfall_anomaly",
}

missing = required_gpm - set(gpm.columns)

if missing:
    raise ValueError(
        f"GPM file missing columns: {sorted(missing)}"
    )

print(f"GPM rows: {len(gpm):,}")


# ============================================================
# LOAD SPATIAL MAPPING
# ============================================================

print("Loading spatial mapping...")

mapping = pd.read_csv(MAPPING_FILE)

required_mapping = {
    "smap_latitude",
    "smap_longitude",
    "gpm_latitude",
    "gpm_longitude",
}

missing = required_mapping - set(mapping.columns)

if missing:
    raise ValueError(
        f"Mapping file missing columns: {sorted(missing)}"
    )

print(f"Mapping rows: {len(mapping):,}")


# ============================================================
# BUILD CELL IDS
# ============================================================

smap["smap_cell"] = (
    smap["latitude"].round(6).astype(str)
    + "_"
    + smap["longitude"].round(6).astype(str)
)

gpm["gpm_cell"] = (
    gpm["latitude"].round(6).astype(str)
    + "_"
    + gpm["longitude"].round(6).astype(str)
)

mapping["smap_cell"] = (
    mapping["smap_latitude"].round(6).astype(str)
    + "_"
    + mapping["smap_longitude"].round(6).astype(str)
)

mapping["gpm_cell"] = (
    mapping["gpm_latitude"].round(6).astype(str)
    + "_"
    + mapping["gpm_longitude"].round(6).astype(str)
)


# ============================================================
# VALIDATE MAPPING
# ============================================================

print("\nValidating spatial mapping...")

smap_cells = smap["smap_cell"].nunique()
gpm_cells = gpm["gpm_cell"].nunique()

mapping_smap_cells = mapping["smap_cell"].nunique()
mapping_gpm_cells = mapping["gpm_cell"].nunique()

print(f"Unique SMAP cells: {smap_cells}")
print(f"Unique GPM cells: {gpm_cells}")
print(f"Mapped SMAP cells: {mapping_smap_cells}")
print(f"Mapped GPM cells: {mapping_gpm_cells}")

if mapping_smap_cells != smap_cells:
    raise ValueError(
        "Not every SMAP cell has a spatial mapping"
    )


# ============================================================
# KEEP REQUIRED GPM COLUMNS
# ============================================================

gpm = gpm[
    [
        "date",
        "gpm_cell",
        "latitude",
        "longitude",
        "rainfall_mm_month",
        "rainfall_anomaly_mm",
        "standardized_rainfall_anomaly",
    ]
].copy()

gpm = gpm.rename(
    columns={
        "latitude": "gpm_latitude",
        "longitude": "gpm_longitude",
        "standardized_rainfall_anomaly":
            "gpm_standardized_anomaly",
        "rainfall_anomaly_mm":
            "gpm_anomaly_mm",
    }
)


# ============================================================
# KEEP REQUIRED SMAP COLUMNS
# ============================================================

smap = smap[
    [
        "date",
        "smap_cell",
        "latitude",
        "longitude",
        "soil_moisture",
        "anomaly",
        "standardized_anomaly",
    ]
].copy()

smap = smap.rename(
    columns={
        "latitude": "smap_latitude",
        "longitude": "smap_longitude",
        "standardized_anomaly":
            "smap_standardized_anomaly",
        "anomaly":
            "smap_anomaly",
    }
)


# ============================================================
# MAP EACH SMAP CELL TO ITS GPM CELL
# ============================================================

mapping_use = mapping[
    [
        "smap_cell",
        "gpm_cell",
    ]
].copy()

if "approx_distance_km" in mapping.columns:

    mapping_use["mapping_distance_km"] = (
        mapping["approx_distance_km"].values
    )

elif "distance_deg" in mapping.columns:

    mapping_use["mapping_distance_km"] = (
        mapping["distance_deg"].values * 111.0
    )

else:

    mapping_use["mapping_distance_km"] = np.nan


# ============================================================
# JOIN SMAP WITH MAPPING
# ============================================================

print("\nJoining SMAP cells to mapped GPM cells...")

smap_mapped = smap.merge(
    mapping_use,
    on="smap_cell",
    how="left",
    validate="many_to_one",
)

if smap_mapped["gpm_cell"].isna().any():
    raise ValueError(
        "Some SMAP cells have no GPM mapping"
    )


# ============================================================
# JOIN MONTHLY GPM DATA
# ============================================================

print("Joining monthly GPM anomalies...")

merged = smap_mapped.merge(
    gpm,
    on=["date", "gpm_cell"],
    how="inner",
    validate="many_to_one",
)

print(f"Joined rows: {len(merged):,}")

expected_rows = smap_cells * min(
    smap["date"].nunique(),
    gpm["date"].nunique(),
)

print(f"Expected approximately: {expected_rows:,}")


# ============================================================
# BASIC JOIN QA
# ============================================================

if merged.empty:
    raise ValueError(
        "Spatial SMAP-GPM join produced zero rows"
    )

if merged["smap_standardized_anomaly"].isna().any():
    raise ValueError(
        "Missing SMAP anomaly values after join"
    )

if merged["gpm_standardized_anomaly"].isna().any():
    raise ValueError(
        "Missing GPM anomaly values after join"
    )


# ============================================================
# CORRELATION PER SMAP CELL
# ============================================================

print("\nCalculating spatial correlations...")

results = []

for cell, group in merged.groupby("smap_cell"):

    group = group.sort_values("date")

    x = group["smap_standardized_anomaly"].to_numpy(
        dtype=float
    )

    y = group["gpm_standardized_anomaly"].to_numpy(
        dtype=float
    )

    valid = np.isfinite(x) & np.isfinite(y)

    x = x[valid]
    y = y[valid]

    n = len(x)

    if n < 3:
        continue

    pearson_r, pearson_p = pearsonr(x, y)

    spearman_rho, spearman_p = spearmanr(x, y)

    first = group.iloc[0]

    results.append(
        {
            "smap_cell": cell,
            "smap_latitude": first["smap_latitude"],
            "smap_longitude": first["smap_longitude"],
            "gpm_cell": first["gpm_cell"],
            "gpm_latitude": first["gpm_latitude"],
            "gpm_longitude": first["gpm_longitude"],
            "mapping_distance_km":
                first["mapping_distance_km"],
            "n": n,
            "pearson_r": pearson_r,
            "pearson_p": pearson_p,
            "spearman_rho": spearman_rho,
            "spearman_p": spearman_p,
        }
    )


results_df = pd.DataFrame(results)

print(
    f"Cells with valid correlations: "
    f"{len(results_df)}"
)


# ============================================================
# FDR CORRECTION
# ============================================================

print("\nApplying Benjamini-Hochberg FDR...")

reject, fdr_p = benjamini_hochberg(
    results_df["pearson_p"].to_numpy(),
    alpha=ALPHA,
)

results_df["pearson_fdr_p"] = fdr_p

results_df["fdr_significant"] = reject


# ============================================================
# CORRELATION CATEGORIES
# ============================================================

def correlation_class(r):

    if r >= 0.7:
        return "strong positive"

    if r >= 0.4:
        return "moderate positive"

    if r >= 0.2:
        return "weak positive"

    if r > -0.2:
        return "near zero"

    if r > -0.4:
        return "weak negative"

    if r > -0.7:
        return "moderate negative"

    return "strong negative"


results_df["correlation_class"] = (
    results_df["pearson_r"]
    .apply(correlation_class)
)


# ============================================================
# SORT
# ============================================================

results_df = results_df.sort_values(
    ["fdr_significant", "pearson_r"],
    ascending=[False, False],
).reset_index(drop=True)


# ============================================================
# SAVE CSV
# ============================================================

results_df.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# SUMMARY
# ============================================================

summary = {
    "status": "PASS",
    "method": (
        "SMAP standardized soil-moisture anomaly "
        "vs nearest-GPM standardized rainfall anomaly"
    ),
    "smap_cells": int(smap_cells),
    "gpm_cells": int(gpm_cells),
    "mapped_smap_cells": int(mapping_smap_cells),
    "joined_rows": int(len(merged)),
    "correlated_cells": int(len(results_df)),
    "alpha": ALPHA,
    "fdr_method": "Benjamini-Hochberg",
    "fdr_significant_cells": int(
        results_df["fdr_significant"].sum()
    ),
    "pearson_r_min": float(
        results_df["pearson_r"].min()
    ),
    "pearson_r_max": float(
        results_df["pearson_r"].max()
    ),
    "pearson_r_mean": float(
        results_df["pearson_r"].mean()
    ),
    "pearson_r_median": float(
        results_df["pearson_r"].median()
    ),
    "mapping_distance_km_mean": float(
        results_df["mapping_distance_km"].mean()
    ),
    "mapping_distance_km_max": float(
        results_df["mapping_distance_km"].max()
    ),
}

with open(JSON_FILE, "w") as f:
    json.dump(
        summary,
        f,
        indent=2,
    )


# ============================================================
# PRINT RESULTS
# ============================================================

print("\n========================================")
print("SPATIAL CORRELATION COMPLETE")
print("========================================")

print(f"Output: {OUTPUT_FILE}")
print(f"JSON:   {JSON_FILE}")

print(
    f"\nCorrelated SMAP cells: "
    f"{len(results_df)}"
)

print(
    f"FDR-significant cells: "
    f"{results_df['fdr_significant'].sum()}"
)

print(
    "\nPearson r:"
)

print(
    f"  Min:    {results_df['pearson_r'].min():.4f}"
)

print(
    f"  Median: {results_df['pearson_r'].median():.4f}"
)

print(
    f"  Mean:   {results_df['pearson_r'].mean():.4f}"
)

print(
    f"  Max:    {results_df['pearson_r'].max():.4f}"
)

print("\nCorrelation classes:")

print(
    results_df["correlation_class"]
    .value_counts()
    .sort_index()
)

print("\nTop 10 positive correlations:")

print(
    results_df[
        [
            "smap_latitude",
            "smap_longitude",
            "pearson_r",
            "pearson_fdr_p",
            "fdr_significant",
            "mapping_distance_km",
        ]
    ]
    .head(10)
    .to_string(index=False)
)

print("\nFINAL RESULT: PASS")
