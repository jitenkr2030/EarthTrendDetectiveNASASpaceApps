#!/usr/bin/env python3

"""
EarthTrend Detective
Phase 2 — Consolidated Analysis Dataset

Builds the canonical analysis dataset from the frozen
monthly SMAP Jharkhand dataset.

Source:
    data/monthly/*.csv

Output:
    data/analysis/smap_monthly_jharkhand.csv
    data/analysis/smap_analysis_manifest.json

Expected frozen dataset:
    2015-04 → 2026-09
    138 months
    984 cells/month
    135,792 records

The output becomes the canonical dataset for:
    - climatology
    - anomaly analysis
    - trend analysis
    - seasonal analysis
    - spatial trends
    - extreme events
    - cross-variable analysis
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MONTHLY_DIR = PROJECT_ROOT / "data" / "monthly"
ANALYSIS_DIR = PROJECT_ROOT / "data" / "analysis"

OUTPUT_FILE = (
    ANALYSIS_DIR / "smap_monthly_jharkhand.csv"
)

MANIFEST_FILE = (
    ANALYSIS_DIR / "smap_analysis_manifest.json"
)

START_MONTH = "2015-04"
END_MONTH = "2026-09"

EXPECTED_CELLS = 984
EXPECTED_MONTHS = 138

EXPECTED_RECORDS = (
    EXPECTED_CELLS * EXPECTED_MONTHS
)


# ============================================================
# SOURCE COLUMNS
# ============================================================

SOURCE_COLUMNS = [
    "row",
    "col",
    "latitude",
    "longitude",
    "month",
    "soil_moisture_mean",
    "observations",
    "expected_observations",
    "coverage_fraction",
]


# ============================================================
# OUTPUT COLUMNS
# ============================================================

OUTPUT_COLUMNS = [
    "date",
    "year",
    "month_number",
    "row",
    "col",
    "latitude",
    "longitude",
    "soil_moisture",
    "season",
    "observations",
    "expected_observations",
    "coverage_fraction",
]


# ============================================================
# SEASON DEFINITION
# ============================================================

def get_season(month: int) -> str:
    """
    Assign meteorological/agro-climatic season used by
    EarthTrend Detective.

    Jan-Feb   : Winter
    Mar-May   : Pre-monsoon
    Jun-Sep   : Monsoon
    Oct-Dec   : Post-monsoon
    """

    if month in (1, 2):
        return "winter"

    if month in (3, 4, 5):
        return "pre-monsoon"

    if month in (6, 7, 8, 9):
        return "monsoon"

    if month in (10, 11, 12):
        return "post-monsoon"

    raise ValueError(
        f"Invalid month number: {month}"
    )


# ============================================================
# HELPERS
# ============================================================

def print_header(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def fail(message: str) -> None:
    print()
    print(f"❌ FATAL: {message}")
    print()
    sys.exit(1)


def check(condition: bool, message: str) -> None:
    if condition:
        print(f"  PASS  {message}")
    else:
        print(f"  FAIL  {message}")


# ============================================================
# START
# ============================================================

start_time = time.time()

print_header(
    "EARTH TREND DETECTIVE — CONSOLIDATED ANALYSIS DATASET"
)

print(f"Project root      : {PROJECT_ROOT}")
print(f"Monthly source    : {MONTHLY_DIR}")
print(f"Analysis output   : {ANALYSIS_DIR}")
print(f"Period            : {START_MONTH} → {END_MONTH}")
print(f"Expected months   : {EXPECTED_MONTHS}")
print(f"Cells/month       : {EXPECTED_CELLS:,}")
print(f"Expected records  : {EXPECTED_RECORDS:,}")


# ============================================================
# 1. DIRECTORY CHECK
# ============================================================

print_header("1. SOURCE DIRECTORY")

if not MONTHLY_DIR.exists():
    fail(
        f"Monthly dataset directory does not exist:\n"
        f"{MONTHLY_DIR}"
    )

monthly_files = sorted(
    MONTHLY_DIR.glob("????-??.csv")
)

print(
    f"Monthly files found: {len(monthly_files)}"
)

expected_periods = pd.period_range(
    START_MONTH,
    END_MONTH,
    freq="M",
)

expected_months = [
    str(period)
    for period in expected_periods
]

actual_months = sorted(
    path.stem
    for path in monthly_files
)

missing_months = sorted(
    set(expected_months) - set(actual_months)
)

unexpected_months = sorted(
    set(actual_months) - set(expected_months)
)

check(
    len(monthly_files) == EXPECTED_MONTHS,
    f"Expected {EXPECTED_MONTHS} monthly files",
)

check(
    not missing_months,
    "No expected months are missing",
)

check(
    not unexpected_months,
    "No unexpected monthly files",
)

if missing_months:
    print("\nMissing:")
    for month in missing_months:
        print(f"  ❌ {month}")

if unexpected_months:
    print("\nUnexpected:")
    for month in unexpected_months:
        print(f"  ⚠️ {month}")

if (
    len(monthly_files) != EXPECTED_MONTHS
    or missing_months
    or unexpected_months
):
    fail(
        "Source monthly dataset does not match the "
        "frozen 2015-04 → 2026-09 dataset."
    )


# ============================================================
# 2. CREATE OUTPUT DIRECTORY
# ============================================================

ANALYSIS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# 3. LOAD MONTHLY FILES
# ============================================================

print_header("2. CONSOLIDATING MONTHLY DATA")

frames = []

reference_coordinates = None

total_source_records = 0

for index, month in enumerate(
    expected_months,
    start=1,
):

    file_path = MONTHLY_DIR / f"{month}.csv"

    print(
        f"[{index:03d}/{EXPECTED_MONTHS}] "
        f"Loading {month}...",
        end=" ",
        flush=True,
    )

    try:
        df = pd.read_csv(file_path)

    except Exception as exc:
        fail(
            f"Unable to read {file_path}: {exc}"
        )

    # --------------------------------------------------------
    # Column validation
    # --------------------------------------------------------

    missing_columns = [
        column
        for column in SOURCE_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        fail(
            f"{month} is missing columns: "
            + ", ".join(missing_columns)
        )

    # --------------------------------------------------------
    # Cell count
    # --------------------------------------------------------

    if len(df) != EXPECTED_CELLS:
        fail(
            f"{month}: expected "
            f"{EXPECTED_CELLS} rows, found {len(df)}"
        )

    # --------------------------------------------------------
    # Duplicate cell check
    # --------------------------------------------------------

    duplicate_cells = df.duplicated(
        subset=["row", "col"]
    ).sum()

    if duplicate_cells:
        fail(
            f"{month}: found "
            f"{duplicate_cells} duplicate cells"
        )

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    if df[SOURCE_COLUMNS].isna().any().any():

        missing_count = int(
            df[SOURCE_COLUMNS]
            .isna()
            .sum()
            .sum()
        )

        fail(
            f"{month}: found "
            f"{missing_count} missing values"
        )

    # --------------------------------------------------------
    # Month consistency
    # --------------------------------------------------------

    month_values = (
        df["month"]
        .astype(str)
        .str.strip()
    )

    if not (month_values == month).all():

        wrong_count = int(
            (month_values != month).sum()
        )

        fail(
            f"{month}: {wrong_count} rows "
            f"contain incorrect month values"
        )

    # --------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------

    numeric_columns = [
        "row",
        "col",
        "latitude",
        "longitude",
        "soil_moisture_mean",
        "observations",
        "expected_observations",
        "coverage_fraction",
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    if df[numeric_columns].isna().any().any():

        fail(
            f"{month}: non-numeric or invalid "
            f"numeric values detected"
        )

    # --------------------------------------------------------
    # Soil moisture range
    # --------------------------------------------------------

    sm = df["soil_moisture_mean"]

    if (
        (sm < 0).any()
        or (sm > 1).any()
    ):
        fail(
            f"{month}: soil moisture outside "
            f"physical range [0, 1]"
        )

    # --------------------------------------------------------
    # Coverage range
    # --------------------------------------------------------

    coverage = df["coverage_fraction"]

    if (
        (coverage < 0).any()
        or (coverage > 1).any()
    ):
        fail(
            f"{month}: coverage outside [0, 1]"
        )

    # --------------------------------------------------------
    # Observation validation
    # --------------------------------------------------------

    observations = df["observations"]

    expected_observations = (
        df["expected_observations"]
    )

    if (
        (observations < 0).any()
        or (expected_observations <= 0).any()
        or (
            observations
            > expected_observations
        ).any()
    ):
        fail(
            f"{month}: invalid observation counts"
        )

    # --------------------------------------------------------
    # Coordinate grid validation
    # --------------------------------------------------------

    current_coordinates = (
        df[
            [
                "row",
                "col",
                "latitude",
                "longitude",
            ]
        ]
        .sort_values(["row", "col"])
        .reset_index(drop=True)
    )

    if reference_coordinates is None:

        reference_coordinates = (
            current_coordinates.copy()
        )

    else:

        same_index = np.array_equal(
            current_coordinates[
                ["row", "col"]
            ].to_numpy(),
            reference_coordinates[
                ["row", "col"]
            ].to_numpy(),
        )

        same_latitude = np.allclose(
            current_coordinates[
                "latitude"
            ].to_numpy(dtype=float),
            reference_coordinates[
                "latitude"
            ].to_numpy(dtype=float),
            rtol=0,
            atol=1e-10,
        )

        same_longitude = np.allclose(
            current_coordinates[
                "longitude"
            ].to_numpy(dtype=float),
            reference_coordinates[
                "longitude"
            ].to_numpy(dtype=float),
            rtol=0,
            atol=1e-10,
        )

        if not (
            same_index
            and same_latitude
            and same_longitude
        ):
            fail(
                f"{month}: spatial coordinate grid "
                f"does not match the reference grid"
            )

    # --------------------------------------------------------
    # Create canonical fields
    # --------------------------------------------------------

    period = pd.Period(
        month,
        freq="M",
    )

    df["date"] = period.to_timestamp(
        how="start"
    )

    df["year"] = period.year

    df["month_number"] = period.month

    df["season"] = get_season(
        period.month
    )

    # --------------------------------------------------------
    # Rename source field
    # --------------------------------------------------------

    df = df.rename(
        columns={
            "soil_moisture_mean":
                "soil_moisture"
        }
    )

    # --------------------------------------------------------
    # Select canonical columns
    # --------------------------------------------------------

    df = df[
        OUTPUT_COLUMNS
    ]

    frames.append(df)

    total_source_records += len(df)

    print("PASS")


# ============================================================
# 4. CONCATENATE
# ============================================================

print_header("3. BUILDING CONSOLIDATED DATASET")

if not frames:
    fail(
        "No monthly datasets were loaded."
    )

combined = pd.concat(
    frames,
    ignore_index=True,
)

print(
    f"Combined records: "
    f"{len(combined):,}"
)

print(
    f"Expected records: "
    f"{EXPECTED_RECORDS:,}"
)

check(
    len(combined) == EXPECTED_RECORDS,
    "Total record count is correct",
)


# ============================================================
# 5. SORT DATASET
# ============================================================

print_header("4. SORTING CANONICAL DATASET")

combined = combined.sort_values(
    [
        "date",
        "row",
        "col",
    ]
).reset_index(drop=True)

print("Sorted by:")
print("  date")
print("  row")
print("  col")


# ============================================================
# 6. FINAL STRUCTURE CHECK
# ============================================================

print_header("5. FINAL STRUCTURE VALIDATION")

check(
    list(combined.columns) == OUTPUT_COLUMNS,
    "Output columns match canonical schema",
)

if list(combined.columns) != OUTPUT_COLUMNS:
    fail(
        "Output column structure does not match "
        "the canonical schema."
    )


# ============================================================
# 7. DATE VALIDATION
# ============================================================

print_header("6. DATE VALIDATION")

combined["date"] = pd.to_datetime(
    combined["date"],
    errors="coerce",
)

if combined["date"].isna().any():
    fail(
        "Invalid dates found in consolidated dataset."
    )

actual_min_date = (
    combined["date"].min()
)

actual_max_date = (
    combined["date"].max()
)

expected_min_date = pd.Timestamp(
    START_MONTH + "-01"
)

expected_max_date = (
    pd.Period(
        END_MONTH,
        freq="M"
    )
    .to_timestamp(
        how="start"
    )
)

print(
    f"Minimum date: "
    f"{actual_min_date.date()}"
)

print(
    f"Maximum date: "
    f"{actual_max_date.date()}"
)

check(
    actual_min_date == expected_min_date,
    "Minimum date is correct",
)

check(
    actual_max_date == expected_max_date,
    "Maximum date is correct",
)


# ============================================================
# 8. YEAR / MONTH CONSISTENCY
# ============================================================

print_header("7. YEAR / MONTH CONSISTENCY")

date_year = combined["date"].dt.year

date_month = combined["date"].dt.month

year_match = (
    combined["year"] == date_year
).all()

month_match = (
    combined["month_number"] == date_month
).all()

check(
    year_match,
    "Year matches date",
)

check(
    month_match,
    "Month number matches date",
)

if not year_match or not month_match:
    fail(
        "Year/month fields are inconsistent with date."
    )


# ============================================================
# 9. SEASON VALIDATION
# ============================================================

print_header("8. SEASON VALIDATION")

expected_seasons = (
    combined["month_number"]
    .map(get_season)
)

season_match = (
    combined["season"]
    == expected_seasons
).all()

check(
    season_match,
    "All season assignments are correct",
)

if not season_match:
    fail(
        "Season assignment validation failed."
    )

print()
print("Season distribution:")

season_counts = (
    combined["season"]
    .value_counts()
    .sort_index()
)

for season, count in season_counts.items():

    print(
        f"  {season:15s}: "
        f"{count:,}"
    )


# ============================================================
# 10. UNIQUE RECORD VALIDATION
# ============================================================

print_header("9. UNIQUE RECORD VALIDATION")

duplicate_records = combined.duplicated(
    subset=[
        "date",
        "row",
        "col",
    ]
).sum()

print(
    f"Duplicate date/cell records: "
    f"{duplicate_records}"
)

check(
    duplicate_records == 0,
    "No duplicate date/cell records",
)

if duplicate_records:
    fail(
        "Duplicate date/cell records detected."
    )


# ============================================================
# 11. MONTHLY CELL COUNTS
# ============================================================

print_header("10. MONTHLY CELL COUNT VALIDATION")

monthly_counts = (
    combined
    .groupby("date")
    .size()
)

wrong_month_counts = (
    monthly_counts[
        monthly_counts != EXPECTED_CELLS
    ]
)

print(
    f"Unique months: "
    f"{monthly_counts.size}"
)

print(
    f"Months with incorrect cell count: "
    f"{len(wrong_month_counts)}"
)

check(
    len(wrong_month_counts) == 0,
    f"Every month contains exactly "
    f"{EXPECTED_CELLS} cells",
)

if len(wrong_month_counts):

    print()

    for date, count in wrong_month_counts.items():

        print(
            f"  ❌ {date.date()}: "
            f"{count} cells"
        )

    fail(
        "Monthly cell-count validation failed."
    )


# ============================================================
# 12. GLOBAL MISSING VALUE CHECK
# ============================================================

print_header("11. MISSING VALUE VALIDATION")

missing_by_column = (
    combined[OUTPUT_COLUMNS]
    .isna()
    .sum()
)

total_missing = int(
    missing_by_column.sum()
)

print(
    f"Total missing values: "
    f"{total_missing}"
)

check(
    total_missing == 0,
    "No missing values",
)

if total_missing:

    print()

    print(
        missing_by_column[
            missing_by_column > 0
        ]
    )

    fail(
        "Missing values detected."
    )


# ============================================================
# 13. SOIL MOISTURE VALIDATION
# ============================================================

print_header("12. SOIL MOISTURE VALIDATION")

sm = combined[
    "soil_moisture"
]

print(
    f"Minimum: {sm.min():.6f}"
)

print(
    f"Maximum: {sm.max():.6f}"
)

print(
    f"Mean   : {sm.mean():.6f}"
)

invalid_sm = (
    (sm < 0)
    | (sm > 1)
).sum()

print(
    f"Invalid values: {invalid_sm}"
)

check(
    invalid_sm == 0,
    "All soil-moisture values are within [0, 1]",
)

if invalid_sm:
    fail(
        "Invalid soil-moisture values detected."
    )


# ============================================================
# 14. COVERAGE VALIDATION
# ============================================================

print_header("13. COVERAGE VALIDATION")

coverage = combined[
    "coverage_fraction"
]

print(
    f"Minimum: {coverage.min():.6f}"
)

print(
    f"Maximum: {coverage.max():.6f}"
)

print(
    f"Mean   : {coverage.mean():.6f}"
)

invalid_coverage = (
    (coverage < 0)
    | (coverage > 1)
).sum()

check(
    invalid_coverage == 0,
    "Coverage values are within [0, 1]",
)

check(
    np.isclose(
        coverage.min(),
        1.0,
    ),
    "Minimum coverage is 1.0",
)

if invalid_coverage:
    fail(
        "Invalid coverage values detected."
    )


# ============================================================
# 15. OBSERVATION VALIDATION
# ============================================================

print_header("14. OBSERVATION VALIDATION")

observations = combined[
    "observations"
]

expected_observations = combined[
    "expected_observations"
]

invalid_observations = (
    (observations < 0)
    | (expected_observations <= 0)
    | (
        observations
        > expected_observations
    )
).sum()

print(
    f"Minimum observations: "
    f"{observations.min()}"
)

print(
    f"Maximum observations: "
    f"{observations.max()}"
)

print(
    f"Invalid observation records: "
    f"{invalid_observations}"
)

check(
    invalid_observations == 0,
    "Observation counts are valid",
)

if invalid_observations:
    fail(
        "Invalid observation counts detected."
    )


# ============================================================
# 16. SPATIAL GRID VALIDATION
# ============================================================

print_header("15. SPATIAL GRID VALIDATION")

unique_cells = (
    combined[
        ["row", "col"]
    ]
    .drop_duplicates()
)

print(
    f"Unique spatial cells: "
    f"{len(unique_cells)}"
)

check(
    len(unique_cells) == EXPECTED_CELLS,
    f"Exactly {EXPECTED_CELLS} unique cells",
)

if len(unique_cells) != EXPECTED_CELLS:
    fail(
        "Unexpected number of spatial cells."
    )


# ============================================================
# 17. COORDINATE VALIDATION
# ============================================================

print_header("16. COORDINATE VALIDATION")

coordinate_counts = (
    combined[
        ["row", "col", "latitude", "longitude"]
    ]
    .drop_duplicates(
        subset=["row", "col"]
    )
)

coordinate_variation = (
    combined
    .groupby(["row", "col"])[
        ["latitude", "longitude"]
    ]
    .nunique()
)

coordinate_inconsistency = (
    coordinate_variation > 1
).any(axis=1).sum()

print(
    f"Cells with changing coordinates: "
    f"{coordinate_inconsistency}"
)

check(
    coordinate_inconsistency == 0,
    "Coordinates remain constant for every cell",
)

if coordinate_inconsistency:
    fail(
        "Spatial coordinates change across months."
    )


# ============================================================
# 18. YEAR SUMMARY
# ============================================================

print_header("17. YEAR SUMMARY")

year_summary = (
    combined
    .groupby("year")
    .agg(
        records=(
            "soil_moisture",
            "size",
        ),
        cells=(
            "row",
            "nunique",
        ),
        mean_soil_moisture=(
            "soil_moisture",
            "mean",
        ),
        min_soil_moisture=(
            "soil_moisture",
            "min",
        ),
        max_soil_moisture=(
            "soil_moisture",
            "max",
        ),
    )
    .reset_index()
)

for _, row in year_summary.iterrows():

    print(
        f"{int(row['year'])}: "
        f"{int(row['records']):,} records | "
        f"{int(row['cells'])} cells | "
        f"mean SM={row['mean_soil_moisture']:.6f}"
    )


# ============================================================
# 19. MONTHLY SUMMARY
# ============================================================

print_header("18. MONTHLY SUMMARY")

monthly_summary = (
    combined
    .groupby("date")
    .agg(
        records=(
            "soil_moisture",
            "size",
        ),
        mean_soil_moisture=(
            "soil_moisture",
            "mean",
        ),
        min_soil_moisture=(
            "soil_moisture",
            "min",
        ),
        max_soil_moisture=(
            "soil_moisture",
            "max",
        ),
    )
    .reset_index()
)

print(
    f"Monthly summary rows: "
    f"{len(monthly_summary)}"
)


# ============================================================
# 20. SAVE DATASET
# ============================================================

print_header("19. WRITING CONSOLIDATED DATASET")

# Explicit dtypes before saving.

combined["year"] = (
    combined["year"]
    .astype("int16")
)

combined["month_number"] = (
    combined["month_number"]
    .astype("int8")
)

combined["row"] = (
    combined["row"]
    .astype("int32")
)

combined["col"] = (
    combined["col"]
    .astype("int32")
)

combined["latitude"] = (
    combined["latitude"]
    .astype("float64")
)

combined["longitude"] = (
    combined["longitude"]
    .astype("float64")
)

combined["soil_moisture"] = (
    combined["soil_moisture"]
    .astype("float64")
)

combined["observations"] = (
    combined["observations"]
    .astype("int32")
)

combined["expected_observations"] = (
    combined["expected_observations"]
    .astype("int32")
)

combined["coverage_fraction"] = (
    combined["coverage_fraction"]
    .astype("float64")
)

# Use ISO-style date representation.

combined["date"] = (
    combined["date"]
    .dt.strftime("%Y-%m-%d")
)

# Atomic write:
# first write temporary file, then replace final file.

temporary_output = (
    OUTPUT_FILE.with_suffix(".tmp.csv")
)

combined.to_csv(
    temporary_output,
    index=False,
)

temporary_output.replace(
    OUTPUT_FILE
)

print(
    f"Output written to:\n"
    f"  {OUTPUT_FILE}"
)


# ============================================================
# 21. RELOAD OUTPUT FOR FINAL VALIDATION
# ============================================================

print_header(
    "20. RELOADING OUTPUT FOR FINAL VALIDATION"
)

try:

    verification = pd.read_csv(
        OUTPUT_FILE
    )

except Exception as exc:

    fail(
        f"Unable to reload output dataset: {exc}"
    )

print(
    f"Reloaded records: "
    f"{len(verification):,}"
)

print(
    f"Reloaded columns: "
    f"{len(verification.columns)}"
)

check(
    len(verification) == EXPECTED_RECORDS,
    "Reloaded record count is correct",
)

check(
    list(verification.columns)
    == OUTPUT_COLUMNS,
    "Reloaded schema is correct",
)

if len(verification) != EXPECTED_RECORDS:
    fail(
        "Reloaded dataset record count is incorrect."
    )

if (
    list(verification.columns)
    != OUTPUT_COLUMNS
):
    fail(
        "Reloaded dataset schema is incorrect."
    )


# ============================================================
# 22. GENERATE MANIFEST
# ============================================================

print_header("21. GENERATING DATASET MANIFEST")

elapsed_seconds = (
    time.time() - start_time
)

manifest = {
    "project": "EarthTrend Detective",

    "dataset": {
        "name":
            "SMAP Monthly Jharkhand Analysis Dataset",

        "source":
            "NASA SMAP SPL4SMGP",

        "variable":
            "/Geophysical_Data/sm_surface",

        "region":
            "Jharkhand, India",

        "period": {
            "start": START_MONTH,
            "end": END_MONTH,
            "months": EXPECTED_MONTHS,
        },

        "spatial_cells_per_month":
            EXPECTED_CELLS,

        "total_records":
            EXPECTED_RECORDS,

        "coverage":
            "100% for all monthly cell records",
    },

    "schema": OUTPUT_COLUMNS,

    "seasons": {
        "winter":
            "January-February",

        "pre-monsoon":
            "March-May",

        "monsoon":
            "June-September",

        "post-monsoon":
            "October-December",
    },

    "statistics": {
        "soil_moisture_min":
            float(sm.min()),

        "soil_moisture_max":
            float(sm.max()),

        "soil_moisture_mean":
            float(sm.mean()),

        "coverage_min":
            float(coverage.min()),

        "coverage_max":
            float(coverage.max()),

        "coverage_mean":
            float(coverage.mean()),
    },

    "validation": {
        "source_months_valid":
            True,

        "record_count_valid":
            True,

        "duplicate_records":
            int(duplicate_records),

        "missing_values":
            int(total_missing),

        "invalid_soil_moisture":
            int(invalid_sm),

        "invalid_coverage":
            int(invalid_coverage),

        "invalid_observations":
            int(invalid_observations),

        "coordinate_inconsistency":
            int(coordinate_inconsistency),

        "final_verdict":
            "PASS",
    },

    "outputs": {
        "dataset":
            str(OUTPUT_FILE),

        "manifest":
            str(MANIFEST_FILE),
    },

    "generated_at":
        pd.Timestamp.now(
            tz="UTC"
        ).isoformat(),

    "runtime_seconds":
        round(
            elapsed_seconds,
            3,
        ),
}


with open(
    MANIFEST_FILE,
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        manifest,
        file,
        indent=2,
    )


# ============================================================
# 23. FINAL RESULT
# ============================================================

print_header("22. FINAL RESULT")

print(
    "🎉 CONSOLIDATED ANALYSIS DATASET COMPLETE"
)

print()

print(
    f"Source period       : "
    f"{START_MONTH} → {END_MONTH}"
)

print(
    f"Months              : "
    f"{EXPECTED_MONTHS}"
)

print(
    f"Cells/month         : "
    f"{EXPECTED_CELLS:,}"
)

print(
    f"Total records       : "
    f"{EXPECTED_RECORDS:,}"
)

print(
    f"Columns             : "
    f"{len(OUTPUT_COLUMNS)}"
)

print()

print(
    "Dataset:"
)

print(
    f"  {OUTPUT_FILE}"
)

print()

print(
    "Manifest:"
)

print(
    f"  {MANIFEST_FILE}"
)

print()

print(
    "STATUS: PASS"
)

print(
    "🔒 Canonical analysis dataset is ready."
)

print()

print(
    "Next scientific phases:"
)

print(
    "  1. Climatology"
)

print(
    "  2. Anomaly analysis"
)

print(
    "  3. Trend analysis"
)

print(
    "  4. Seasonal trend analysis"
)

print(
    "  5. Spatial trend analysis"
)

print()

print(
    f"Runtime: {elapsed_seconds:.2f} seconds"
)

sys.exit(0)
