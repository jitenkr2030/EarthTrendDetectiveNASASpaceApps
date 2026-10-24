from pathlib import Path
import json

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr


# ============================================================
# CONFIG
# ============================================================

SMAP_FILE = Path(
    "data/analysis/smap_anomalies_jharkhand.csv"
)

GPM_FILE = Path(
    "data/analysis/gpm_anomalies_jharkhand.csv"
)

OUTPUT_FILE = Path(
    "data/analysis/smap_gpm_common_months.csv"
)

RESULT_FILE = Path(
    "data/analysis/smap_gpm_same_month_correlation.json"
)


# ============================================================
# LOAD
# ============================================================

print("=" * 70)
print("SMAP + GPM — SAME-MONTH CROSS-VARIABLE ANALYSIS")
print("=" * 70)

smap = pd.read_csv(SMAP_FILE)
gpm = pd.read_csv(GPM_FILE)

smap["date"] = pd.to_datetime(smap["date"])
gpm["date"] = pd.to_datetime(gpm["date"])


# ============================================================
# SMAP STATE-WIDE MONTHLY AGGREGATION
# ============================================================
#
# The SMAP anomaly file is cell-month level.
# We calculate the state-wide mean standardized anomaly
# for each month before joining with GPM.
# ============================================================

smap_required = {
    "date",
    "soil_moisture",
    "anomaly",
    "standardized_anomaly",
}

missing_smap = (
    smap_required - set(smap.columns)
)

if missing_smap:
    raise RuntimeError(
        "SMAP file missing columns: "
        f"{sorted(missing_smap)}"
    )


smap_monthly = (
    smap.groupby("date")
    .agg(
        smap_soil_moisture_mean=(
            "soil_moisture",
            "mean",
        ),
        smap_anomaly_mean=(
            "anomaly",
            "mean",
        ),
        smap_standardized_anomaly_mean=(
            "standardized_anomaly",
            "mean",
        ),
        smap_cells=("soil_moisture", "count"),
    )
    .reset_index()
)


# ============================================================
# GPM STATE-WIDE MONTHLY DATA
# ============================================================

gpm_required = {
    "date",
    "rainfall_mm_month",
    "rainfall_anomaly_mm",
    "standardized_rainfall_anomaly",
}

missing_gpm = (
    gpm_required - set(gpm.columns)
)

if missing_gpm:
    raise RuntimeError(
        "GPM file missing columns: "
        f"{sorted(missing_gpm)}"
    )


gpm_monthly = gpm[
    [
        "date",
        "rainfall_mm_month",
        "rainfall_anomaly_mm",
        "standardized_rainfall_anomaly",
        "coverage_fraction",
    ]
].copy()


# ============================================================
# MERGE COMMON PERIOD
# ============================================================

merged = pd.merge(
    smap_monthly,
    gpm_monthly,
    on="date",
    how="inner",
    validate="one_to_one",
)

merged = (
    merged
    .sort_values("date")
    .reset_index(drop=True)
)


# ============================================================
# VALIDATE COMMON PERIOD
# ============================================================

expected_start = pd.Timestamp("2015-04-01")
expected_end = pd.Timestamp("2025-09-01")

expected_dates = pd.date_range(
    expected_start,
    expected_end,
    freq="MS",
)

if len(merged) != 126:
    raise RuntimeError(
        f"Expected 126 common months, "
        f"found {len(merged)}"
    )

if not merged["date"].equals(
    pd.Series(expected_dates)
):
    raise RuntimeError(
        "Common-period dates are not exactly "
        "2015-04 through 2025-09."
    )

if merged["date"].duplicated().any():
    raise RuntimeError(
        "Duplicate dates detected."
    )


# ============================================================
# VALID NUMERIC DATA
# ============================================================

x = merged[
    "standardized_rainfall_anomaly"
].to_numpy(dtype=float)

y = merged[
    "smap_standardized_anomaly_mean"
].to_numpy(dtype=float)


if not np.isfinite(x).all():
    raise RuntimeError(
        "Invalid GPM standardized anomalies."
    )

if not np.isfinite(y).all():
    raise RuntimeError(
        "Invalid SMAP standardized anomalies."
    )


# ============================================================
# CORRELATIONS
# ============================================================

pearson_r, pearson_p = pearsonr(
    x,
    y,
)

spearman_rho, spearman_p = spearmanr(
    x,
    y,
)


# ============================================================
# RAW-VARIABLE CORRELATIONS
# ============================================================

rainfall_raw = merged[
    "rainfall_mm_month"
].to_numpy(dtype=float)

soil_raw = merged[
    "smap_soil_moisture_mean"
].to_numpy(dtype=float)

raw_pearson_r, raw_pearson_p = pearsonr(
    rainfall_raw,
    soil_raw,
)

raw_spearman_rho, raw_spearman_p = spearmanr(
    rainfall_raw,
    soil_raw,
)


# ============================================================
# EXTREME CO-OCCURRENCE
# ============================================================

rainfall_z = merged[
    "standardized_rainfall_anomaly"
]

soil_z = merged[
    "smap_standardized_anomaly_mean"
]


both_dry = (
    (rainfall_z <= -1)
    & (soil_z <= -1)
)

both_very_dry = (
    (rainfall_z <= -1.5)
    & (soil_z <= -1.5)
)

both_extreme_dry = (
    (rainfall_z <= -2)
    & (soil_z <= -2)
)

both_wet = (
    (rainfall_z >= 1)
    & (soil_z >= 1)
)

both_very_wet = (
    (rainfall_z >= 1.5)
    & (soil_z >= 1.5)
)

both_extreme_wet = (
    (rainfall_z >= 2)
    & (soil_z >= 2)
)


# ============================================================
# PRINT RESULTS
# ============================================================

print("\n" + "=" * 70)
print("COMMON DATASET")
print("=" * 70)

print("SMAP monthly records:", len(smap_monthly))
print("GPM monthly records:", len(gpm_monthly))
print("Common months:", len(merged))

print(
    "Period:",
    merged["date"].min().date(),
    "→",
    merged["date"].max().date(),
)


print("\n" + "=" * 70)
print("STANDARDIZED ANOMALY CORRELATION")
print("=" * 70)

print(
    f"Pearson r: {pearson_r:.6f}"
)

print(
    f"Pearson p-value: {pearson_p:.6g}"
)

print(
    f"Spearman rho: {spearman_rho:.6f}"
)

print(
    f"Spearman p-value: {spearman_p:.6g}"
)


print("\n" + "=" * 70)
print("RAW VARIABLE CORRELATION")
print("=" * 70)

print(
    f"Pearson r: {raw_pearson_r:.6f}"
)

print(
    f"Pearson p-value: {raw_pearson_p:.6g}"
)

print(
    f"Spearman rho: {raw_spearman_rho:.6f}"
)

print(
    f"Spearman p-value: {raw_spearman_p:.6g}"
)


print("\n" + "=" * 70)
print("SIMULTANEOUS ANOMALY EVENTS")
print("=" * 70)

print(
    "Both dry (<= -1σ):",
    int(both_dry.sum()),
)

print(
    "Both very dry (<= -1.5σ):",
    int(both_very_dry.sum()),
)

print(
    "Both extreme dry (<= -2σ):",
    int(both_extreme_dry.sum()),
)

print(
    "Both wet (>= +1σ):",
    int(both_wet.sum()),
)

print(
    "Both very wet (>= +1.5σ):",
    int(both_very_wet.sum()),
)

print(
    "Both extreme wet (>= +2σ):",
    int(both_extreme_wet.sum()),
)


# ============================================================
# CO-OCCURRING EXTREME MONTHS
# ============================================================

print("\n" + "=" * 70)
print("CO-OCCURRING EXTREME MONTHS")
print("=" * 70)

cooccurring = merged[
    (
        (rainfall_z <= -1)
        & (soil_z <= -1)
    )
    |
    (
        (rainfall_z >= 1)
        & (soil_z >= 1)
    )
].copy()

if cooccurring.empty:

    print("No simultaneous ±1σ events.")

else:

    print(
        cooccurring[
            [
                "date",
                "rainfall_mm_month",
                "rainfall_anomaly_mm",
                "standardized_rainfall_anomaly",
                "smap_soil_moisture_mean",
                "smap_anomaly_mean",
                "smap_standardized_anomaly_mean",
            ]
        ].to_string(index=False)
    )


# ============================================================
# SAVE MERGED DATASET
# ============================================================

merged.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# SAVE RESULTS
# ============================================================

results = {
    "analysis": "same-month SMAP-GPM cross-variable relationship",
    "period_start": str(
        merged["date"].min().date()
    ),
    "period_end": str(
        merged["date"].max().date()
    ),
    "common_months": int(len(merged)),

    "standardized_anomaly_correlation": {
        "pearson_r": float(pearson_r),
        "pearson_p": float(pearson_p),
        "spearman_rho": float(spearman_rho),
        "spearman_p": float(spearman_p),
    },

    "raw_variable_correlation": {
        "pearson_r": float(raw_pearson_r),
        "pearson_p": float(raw_pearson_p),
        "spearman_rho": float(raw_spearman_rho),
        "spearman_p": float(raw_spearman_p),
    },

    "simultaneous_events": {
        "both_dry_1sigma": int(both_dry.sum()),
        "both_very_dry_1_5sigma": int(
            both_very_dry.sum()
        ),
        "both_extreme_dry_2sigma": int(
            both_extreme_dry.sum()
        ),
        "both_wet_1sigma": int(
            both_wet.sum()
        ),
        "both_very_wet_1_5sigma": int(
            both_very_wet.sum()
        ),
        "both_extreme_wet_2sigma": int(
            both_extreme_wet.sum()
        ),
    },

    "interpretation_rule": (
        "Correlation describes association, not causation. "
        "Lagged and seasonality/autocorrelation-aware analysis "
        "is required before stronger Earth-system interpretation."
    ),

    "status": "SAME-MONTH ANALYSIS COMPLETE",
}


with open(
    RESULT_FILE,
    "w",
) as f:
    json.dump(
        results,
        f,
        indent=2,
    )


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("OUTPUT")
print("=" * 70)

print(
    "Merged dataset:",
    OUTPUT_FILE,
)

print(
    "Correlation results:",
    RESULT_FILE,
)

print(
    "\nFINAL RESULT: PASS — "
    "same-month SMAP-GPM relationship calculated"
)

print("=" * 70)
