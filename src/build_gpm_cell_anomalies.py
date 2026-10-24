from pathlib import Path
import json
import re

import h5py
import numpy as np
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

BASE = Path("/root/earthtrend-detective")

GPM_DIR = BASE / "data" / "gpm_monthly"
MASK_FILE = BASE / "data" / "gpm_jharkhand_mask.csv"

OUTPUT_FILE = BASE / "data" / "analysis" / "gpm_cell_anomalies_jharkhand.csv"
MANIFEST_FILE = BASE / "data" / "analysis" / "gpm_cell_anomalies_manifest.json"

EXPECTED_CELLS = 703
EXPECTED_MONTHS = 126

FILL_VALUE = -9990.0


# ============================================================
# HELPERS
# ============================================================

def extract_date_from_filename(filename):
    """
    Extract YYYYMMDD from a GPM monthly filename.
    Example:
    3B-MO.MS.MRG.3IMERG.20150401-S000000...
    """
    match = re.search(r"\.(\d{8})-S", filename)

    if not match:
        raise ValueError(f"Could not extract date from filename: {filename}")

    return pd.to_datetime(match.group(1), format="%Y%m%d")


def calendar_hours(year, month):
    """
    Number of hours in a calendar month.
    """
    start = pd.Timestamp(year=year, month=month, day=1)

    if month == 12:
        end = pd.Timestamp(year=year + 1, month=1, day=1)
    else:
        end = pd.Timestamp(year=year, month=month + 1, day=1)

    return int((end - start).total_seconds() / 3600)


def nearest_index(values, target):
    """
    Return index of nearest coordinate.
    """
    values = np.asarray(values)

    return int(np.abs(values - target).argmin())


# ============================================================
# LOAD MASK
# ============================================================

print("\nLoading GPM Jharkhand mask...")

mask = pd.read_csv(MASK_FILE)

required_mask_columns = {
    "latitude",
    "longitude",
}

missing = required_mask_columns - set(mask.columns)

if missing:
    raise ValueError(
        f"Mask missing required columns: {sorted(missing)}"
    )

if len(mask) != EXPECTED_CELLS:
    raise ValueError(
        f"Expected {EXPECTED_CELLS} mask cells, found {len(mask)}"
    )

mask = mask.reset_index(drop=True)

print(f"Mask cells: {len(mask)}")


# ============================================================
# FIND PRODUCTION FILES
# ============================================================

files = sorted(GPM_DIR.glob("*.HDF5"))

print(f"Production HDF5 files found: {len(files)}")

if len(files) != EXPECTED_MONTHS:
    raise ValueError(
        f"Expected {EXPECTED_MONTHS} HDF5 files, found {len(files)}"
    )


# ============================================================
# EXTRACT CELL-LEVEL MONTHLY RAINFALL
# ============================================================

records = []

reference_lat = None
reference_lon = None

for file_index, file_path in enumerate(files, start=1):

    date = extract_date_from_filename(file_path.name)

    print(
        f"[{file_index:03d}/{len(files):03d}] "
        f"{date.strftime('%Y-%m')}"
    )

    with h5py.File(file_path, "r") as h5:

        grid = h5["Grid"]

        precipitation = grid["precipitation"][0]
        latitudes = grid["lat"][:]
        longitudes = grid["lon"][:]

        # ----------------------------------------------------
        # Coordinate validation
        # ----------------------------------------------------

        if reference_lat is None:
            reference_lat = latitudes.copy()
            reference_lon = longitudes.copy()

        else:

            if not np.allclose(
                reference_lat,
                latitudes,
                atol=1e-6,
                equal_nan=True,
            ):
                raise ValueError(
                    f"Latitude grid changed in {file_path.name}"
                )

            if not np.allclose(
                reference_lon,
                longitudes,
                atol=1e-6,
                equal_nan=True,
            ):
                raise ValueError(
                    f"Longitude grid changed in {file_path.name}"
                )

        hours = calendar_hours(date.year, date.month)

        # ----------------------------------------------------
        # Extract 703 mask cells
        # ----------------------------------------------------

        for _, cell in mask.iterrows():

            target_lat = float(cell["latitude"])
            target_lon = float(cell["longitude"])

            lat_idx = nearest_index(latitudes, target_lat)
            lon_idx = nearest_index(longitudes, target_lon)

            value = float(precipitation[lon_idx, lat_idx])

            if value <= FILL_VALUE:
                value = np.nan

            rainfall_mm_month = (
                value * hours
                if np.isfinite(value)
                else np.nan
            )

            records.append(
                {
                    "date": date,
                    "year": date.year,
                    "month_number": date.month,
                    "latitude": target_lat,
                    "longitude": target_lon,
                    "precipitation_rate_mm_hr": value,
                    "rainfall_mm_month": rainfall_mm_month,
                    "source_file": file_path.name,
                }
            )


# ============================================================
# BUILD DATAFRAME
# ============================================================

print("\nBuilding cell-level dataframe...")

df = pd.DataFrame(records)

df["date"] = pd.to_datetime(df["date"])

df = df.sort_values(
    ["date", "latitude", "longitude"]
).reset_index(drop=True)


# ============================================================
# BASIC QA
# ============================================================

expected_rows = EXPECTED_CELLS * EXPECTED_MONTHS

print(f"Rows created: {len(df)}")
print(f"Expected rows: {expected_rows}")

if len(df) != expected_rows:
    raise ValueError(
        f"Row count mismatch: expected {expected_rows}, "
        f"found {len(df)}"
    )

unique_dates = df["date"].nunique()

if unique_dates != EXPECTED_MONTHS:
    raise ValueError(
        f"Expected {EXPECTED_MONTHS} dates, found {unique_dates}"
    )

unique_cells = df[
    ["latitude", "longitude"]
].drop_duplicates().shape[0]

if unique_cells != EXPECTED_CELLS:
    raise ValueError(
        f"Expected {EXPECTED_CELLS} cells, found {unique_cells}"
    )

duplicates = df.duplicated(
    subset=["date", "latitude", "longitude"]
).sum()

if duplicates != 0:
    raise ValueError(
        f"Duplicate cell-month records: {duplicates}"
    )


coverage = (
    df.groupby("date")["rainfall_mm_month"]
    .apply(lambda x: x.notna().mean())
)

print(
    f"Minimum monthly cell coverage: "
    f"{coverage.min():.6f}"
)

if coverage.min() < 0.95:
    raise ValueError(
        "Monthly cell coverage below 95%"
    )


# ============================================================
# CELL-LEVEL CLIMATOLOGY
# ============================================================

print("\nCalculating cell-level monthly climatology...")

climatology = (
    df.groupby(
        ["latitude", "longitude", "month_number"],
        as_index=False
    )
    .agg(
        climatology_mean_mm=(
            "rainfall_mm_month",
            "mean",
        ),
        climatology_std_mm=(
            "rainfall_mm_month",
            "std",
        ),
        climatology_n=(
            "rainfall_mm_month",
            "count",
        ),
    )
)


# ============================================================
# JOIN CLIMATOLOGY
# ============================================================

df = df.merge(
    climatology,
    on=[
        "latitude",
        "longitude",
        "month_number",
    ],
    how="left",
    validate="many_to_one",
)


# ============================================================
# CALCULATE ANOMALIES
# ============================================================

df["rainfall_anomaly_mm"] = (
    df["rainfall_mm_month"]
    - df["climatology_mean_mm"]
)

df["standardized_rainfall_anomaly"] = (
    df["rainfall_anomaly_mm"]
    / df["climatology_std_mm"]
)


# ============================================================
# CLASSIFY ANOMALIES
# ============================================================

def classify_anomaly(z):

    if not np.isfinite(z):
        return "missing"

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


df["rainfall_anomaly_class"] = (
    df["standardized_rainfall_anomaly"]
    .apply(classify_anomaly)
)


# ============================================================
# FINAL QA
# ============================================================

print("\nFinal QA...")

if df["climatology_mean_mm"].isna().any():
    raise ValueError(
        "Missing climatology values detected"
    )

zero_std = (
    df["climatology_std_mm"]
    .fillna(0)
    .eq(0)
    .sum()
)

print(f"Zero climatology std cells/months: {zero_std}")

if zero_std > 0:
    raise ValueError(
        "Zero climatology standard deviation detected"
    )

invalid_anomaly = (
    ~np.isfinite(
        df["standardized_rainfall_anomaly"]
    )
).sum()

print(f"Invalid standardized anomalies: {invalid_anomaly}")

if invalid_anomaly > 0:
    raise ValueError(
        "Invalid standardized anomalies detected"
    )


# ============================================================
# SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

df.to_csv(
    OUTPUT_FILE,
    index=False,
)

manifest = {
    "status": "PASS",
    "dataset": "NASA GPM IMERG Monthly V07B",
    "region": "Jharkhand",
    "cells": int(unique_cells),
    "months": int(unique_dates),
    "rows": int(len(df)),
    "period_start": str(df["date"].min().date()),
    "period_end": str(df["date"].max().date()),
    "climatology": "cell-specific calendar-month climatology",
    "anomaly": "rainfall_mm_month - cell/month climatology",
    "standardized_anomaly": (
        "rainfall_anomaly_mm / cell/month climatology std"
    ),
    "minimum_monthly_coverage": float(coverage.min()),
    "maximum_monthly_coverage": float(coverage.max()),
    "zero_climatology_std": int(zero_std),
    "invalid_standardized_anomalies": int(
        invalid_anomaly
    ),
}

with open(MANIFEST_FILE, "w") as f:
    json.dump(
        manifest,
        f,
        indent=2,
    )


# ============================================================
# SUMMARY
# ============================================================

print("\n========================================")
print("GPM CELL ANOMALY BUILD COMPLETE")
print("========================================")

print(f"Output: {OUTPUT_FILE}")
print(f"Manifest: {MANIFEST_FILE}")

print(f"\nRows: {len(df):,}")
print(f"Cells: {unique_cells}")
print(f"Months: {unique_dates}")

print(
    f"Period: "
    f"{df['date'].min().date()} → "
    f"{df['date'].max().date()}"
)

print(
    "\nRainfall anomaly range:",
    f"{df['rainfall_anomaly_mm'].min():.3f}",
    "→",
    f"{df['rainfall_anomaly_mm'].max():.3f}",
    "mm",
)

print(
    "Standardized anomaly range:",
    f"{df['standardized_rainfall_anomaly'].min():.3f}",
    "→",
    f"{df['standardized_rainfall_anomaly'].max():.3f}",
)

print("\nAnomaly classes:")
print(
    df["rainfall_anomaly_class"]
    .value_counts()
    .sort_index()
)

print("\nFINAL RESULT: PASS")
