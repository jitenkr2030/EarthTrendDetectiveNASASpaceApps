from pathlib import Path
import json

import numpy as np
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = Path(
    "data/analysis/gpm_monthly_jharkhand.csv"
)

CLIMATOLOGY_FILE = Path(
    "data/analysis/gpm_climatology_jharkhand.csv"
)

ANOMALY_FILE = Path(
    "data/analysis/gpm_anomalies_jharkhand.csv"
)

MANIFEST_FILE = Path(
    "data/analysis/gpm_anomaly_manifest.json"
)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("GPM IMERG — RAINFALL CLIMATOLOGY & ANOMALY")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

df["date"] = pd.to_datetime(df["date"])

df = df.sort_values("date").reset_index(drop=True)

required_columns = {
    "date",
    "year",
    "month_number",
    "rainfall_mm_month",
    "precipitation_rate_mm_hr",
    "coverage_fraction",
}

missing = required_columns - set(df.columns)

if missing:
    raise RuntimeError(
        f"Missing required columns: {sorted(missing)}"
    )


# ============================================================
# BASIC VALIDATION
# ============================================================

expected_months = pd.date_range(
    "2015-04-01",
    "2025-09-01",
    freq="MS",
)

if len(df) != 126:
    raise RuntimeError(
        f"Expected 126 monthly rows, found {len(df)}"
    )

if df["date"].duplicated().any():
    raise RuntimeError("Duplicate dates detected.")

if not df["date"].equals(
    pd.Series(expected_months)
):
    raise RuntimeError(
        "Monthly date sequence is not exactly "
        "2015-04 through 2025-09."
    )

if not np.isfinite(
    df["rainfall_mm_month"]
).all():
    raise RuntimeError(
        "Invalid rainfall values detected."
    )

if (
    df["rainfall_mm_month"] < 0
).any():
    raise RuntimeError(
        "Negative rainfall values detected."
    )


print("\nInput validation: PASS")
print("Monthly records:", len(df))
print(
    "Period:",
    df["date"].min().date(),
    "→",
    df["date"].max().date(),
)


# ============================================================
# MONTHLY CLIMATOLOGY
# ============================================================

climatology = (
    df.groupby("month_number")[
        "rainfall_mm_month"
    ]
    .agg(
        climatology_mean_mm=("mean"),
        climatology_std_mm=("std"),
        climatology_min_mm=("min"),
        climatology_max_mm=("max"),
        years_available=("count"),
    )
    .reset_index()
)

# Add month names.
climatology["month_name"] = pd.to_datetime(
    climatology["month_number"],
    format="%m",
).dt.strftime("%B")


# ============================================================
# STANDARD DEVIATION VALIDATION
# ============================================================

if (
    climatology["climatology_std_mm"] <= 0
).any():

    bad_months = climatology.loc[
        climatology["climatology_std_mm"] <= 0,
        "month_number",
    ].tolist()

    raise RuntimeError(
        f"Zero/negative climatology std for months: {bad_months}"
    )


# ============================================================
# SAVE CLIMATOLOGY
# ============================================================

climatology = climatology[
    [
        "month_number",
        "month_name",
        "climatology_mean_mm",
        "climatology_std_mm",
        "climatology_min_mm",
        "climatology_max_mm",
        "years_available",
    ]
]

climatology.to_csv(
    CLIMATOLOGY_FILE,
    index=False,
)


# ============================================================
# MERGE CLIMATOLOGY WITH OBSERVATIONS
# ============================================================

result = df.merge(
    climatology[
        [
            "month_number",
            "climatology_mean_mm",
            "climatology_std_mm",
        ]
    ],
    on="month_number",
    how="left",
    validate="many_to_one",
)


# ============================================================
# ANOMALY CALCULATION
# ============================================================

result["rainfall_anomaly_mm"] = (
    result["rainfall_mm_month"]
    - result["climatology_mean_mm"]
)

result["standardized_rainfall_anomaly"] = (
    result["rainfall_anomaly_mm"]
    / result["climatology_std_mm"]
)


# ============================================================
# ANOMALY CLASSIFICATION
# ============================================================

def classify(z):

    if z <= -2:
        return "extremely dry"

    if z <= -1.5:
        return "very dry"

    if z <= -1:
        return "dry"

    if z < 1:
        return "near normal"

    if z < 1.5:
        return "wet"

    if z < 2:
        return "very wet"

    return "extremely wet"


result["rainfall_anomaly_class"] = (
    result["standardized_rainfall_anomaly"]
    .apply(classify)
)


# ============================================================
# VALIDATE RESULTS
# ============================================================

if result[
    "rainfall_anomaly_mm"
].isna().any():

    raise RuntimeError(
        "Missing rainfall anomaly values."
    )

if result[
    "standardized_rainfall_anomaly"
].isna().any():

    raise RuntimeError(
        "Missing standardized rainfall anomaly values."
    )


# ============================================================
# SAVE ANOMALIES
# ============================================================

result.to_csv(
    ANOMALY_FILE,
    index=False,
)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("RAINFALL CLIMATOLOGY")
print("=" * 70)

print(
    climatology[
        [
            "month_number",
            "month_name",
            "climatology_mean_mm",
            "climatology_std_mm",
            "years_available",
        ]
    ].to_string(index=False)
)


print("\n" + "=" * 70)
print("RAINFALL ANOMALY SUMMARY")
print("=" * 70)

print(
    "Anomaly range:",
    round(
        result["rainfall_anomaly_mm"].min(),
        3,
    ),
    "→",
    round(
        result["rainfall_anomaly_mm"].max(),
        3,
    ),
    "mm",
)

print(
    "Standardized anomaly range:",
    round(
        result[
            "standardized_rainfall_anomaly"
        ].min(),
        3,
    ),
    "→",
    round(
        result[
            "standardized_rainfall_anomaly"
        ].max(),
        3,
    ),
)


print("\nAnomaly classes:")

print(
    result[
        "rainfall_anomaly_class"
    ].value_counts().sort_index()
)


# ============================================================
# EXTREME MONTHS
# ============================================================

print("\n" + "=" * 70)
print("MOST EXTREME DRY MONTHS")
print("=" * 70)

dry = result.sort_values(
    "standardized_rainfall_anomaly"
).head(10)

print(
    dry[
        [
            "date",
            "rainfall_mm_month",
            "climatology_mean_mm",
            "rainfall_anomaly_mm",
            "standardized_rainfall_anomaly",
            "rainfall_anomaly_class",
        ]
    ].to_string(index=False)
)


print("\n" + "=" * 70)
print("MOST EXTREME WET MONTHS")
print("=" * 70)

wet = result.sort_values(
    "standardized_rainfall_anomaly",
    ascending=False,
).head(10)

print(
    wet[
        [
            "date",
            "rainfall_mm_month",
            "climatology_mean_mm",
            "rainfall_anomaly_mm",
            "standardized_rainfall_anomaly",
            "rainfall_anomaly_class",
        ]
    ].to_string(index=False)
)


# ============================================================
# MANIFEST
# ============================================================

manifest = {
    "source": str(INPUT_FILE),
    "climatology_output": str(
        CLIMATOLOGY_FILE
    ),
    "anomaly_output": str(
        ANOMALY_FILE
    ),
    "period_start": str(
        df["date"].min().date()
    ),
    "period_end": str(
        df["date"].max().date()
    ),
    "months": int(len(df)),
    "climatology_months": int(
        len(climatology)
    ),
    "method": (
        "Calendar-month climatology calculated "
        "from 2015-04 through 2025-09. "
        "Rainfall anomaly equals observed monthly "
        "rainfall minus calendar-month climatological "
        "mean. Standardized anomaly equals anomaly "
        "divided by calendar-month climatological "
        "standard deviation."
    ),
    "zero_std_months": int(
        (
            climatology[
                "climatology_std_mm"
            ] <= 0
        ).sum()
    ),
    "status": "FROZEN / ANALYSIS READY",
}

with open(
    MANIFEST_FILE,
    "w",
) as f:
    json.dump(
        manifest,
        f,
        indent=2,
    )


# ============================================================
# FINAL RESULT
# ============================================================

print("\n" + "=" * 70)
print("FINAL GPM ANOMALY QA")
print("=" * 70)

print(
    "Climatology months:",
    len(climatology),
)

print(
    "Anomaly records:",
    len(result),
)

print(
    "Zero-std months:",
    int(
        (
            climatology[
                "climatology_std_mm"
            ] <= 0
        ).sum()
    ),
)

print(
    "Missing anomaly values:",
    int(
        result[
            "rainfall_anomaly_mm"
        ].isna().sum()
    ),
)

print("\nClimatology:")
print(CLIMATOLOGY_FILE)

print("\nAnomalies:")
print(ANOMALY_FILE)

print("\nManifest:")
print(MANIFEST_FILE)

print(
    "\nFINAL RESULT: PASS — "
    "GPM rainfall anomaly dataset is ready"
)

print("=" * 70)
