#!/usr/bin/env python3

"""
EarthTrend Detective
Final Dataset Quality Assurance
--------------------------------

Validates the complete monthly SMAP dataset for Jharkhand.

Expected dataset:
    2015-04 through 2026-09
    138 months
    984 spatial cells per month
    135,792 cell-month records

Checks:
    1. Expected monthly files
    2. Unexpected monthly files
    3. CSV readability
    4. Required columns
    5. Exactly 984 cells/month
    6. Duplicate cells
    7. Missing values
    8. Coordinate consistency
    9. Soil-moisture physical range
   10. Observation completeness
   11. Coverage fraction
   12. Row/column coordinate consistency
   13. Duplicate month/cell records
   14. Total record count
   15. Generates detailed CSV + JSON QA reports
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

DATA_DIR = PROJECT_ROOT / "data" / "monthly"
REPORT_DIR = PROJECT_ROOT / "data" / "qa"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

START_MONTH = "2015-04"
END_MONTH = "2026-09"

EXPECTED_CELLS = 984

EXPECTED_MONTHS = pd.period_range(
    START_MONTH,
    END_MONTH,
    freq="M",
)

EXPECTED_MONTH_STRINGS = [str(x) for x in EXPECTED_MONTHS]

EXPECTED_MONTH_COUNT = len(EXPECTED_MONTHS)

EXPECTED_TOTAL_RECORDS = EXPECTED_MONTH_COUNT * EXPECTED_CELLS


# SMAP surface soil moisture is volumetric water content.
#
# The theoretically meaningful range is approximately:
#
#       0 <= soil moisture <= 1
#
# We use a slightly conservative scientific validation range here.
#
# Values outside this range are treated as errors.
MIN_SOIL_MOISTURE = 0.0
MAX_SOIL_MOISTURE = 1.0


REQUIRED_COLUMNS = [
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
# HELPERS
# ============================================================

def print_header(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def fail(message: str) -> None:
    print()
    print("❌ FATAL:", message)
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

print_header("EARTH TREND DETECTIVE — FINAL DATASET QA")

print(f"Project root       : {PROJECT_ROOT}")
print(f"Monthly data       : {DATA_DIR}")
print(f"Expected period    : {START_MONTH} → {END_MONTH}")
print(f"Expected months    : {EXPECTED_MONTH_COUNT}")
print(f"Expected cells/mo  : {EXPECTED_CELLS:,}")
print(f"Expected records   : {EXPECTED_TOTAL_RECORDS:,}")


# ============================================================
# 1. DATA DIRECTORY
# ============================================================

print_header("1. DATA DIRECTORY")

if not DATA_DIR.exists():
    fail(f"Dataset directory does not exist: {DATA_DIR}")

monthly_files = sorted(DATA_DIR.glob("????-??.csv"))

print(f"Monthly CSV files found: {len(monthly_files)}")

if not monthly_files:
    fail("No monthly CSV files found.")


# ============================================================
# 2. MONTHLY FILE INVENTORY
# ============================================================

print_header("2. MONTHLY FILE INVENTORY")

actual_months = sorted(
    p.stem for p in monthly_files
)

missing_months = sorted(
    set(EXPECTED_MONTH_STRINGS) - set(actual_months)
)

unexpected_months = sorted(
    set(actual_months) - set(EXPECTED_MONTH_STRINGS)
)

print(f"Expected months : {EXPECTED_MONTH_COUNT}")
print(f"Found months    : {len(actual_months)}")
print(f"Missing months  : {len(missing_months)}")
print(f"Unexpected      : {len(unexpected_months)}")

if missing_months:
    print("\nMissing months:")
    for month in missing_months:
        print(f"  ❌ {month}")

if unexpected_months:
    print("\nUnexpected months:")
    for month in unexpected_months:
        print(f"  ⚠️  {month}")

check(
    not missing_months,
    "All expected months are present",
)

check(
    not unexpected_months,
    "No unexpected monthly files found",
)


# ============================================================
# 3. GLOBAL VALIDATION VARIABLES
# ============================================================

qa_rows = []

global_errors = []

total_records = 0
total_duplicate_records = 0
total_missing_values = 0
total_invalid_sm = 0
total_invalid_coverage = 0
total_invalid_observations = 0
total_coordinate_errors = 0

reference_coordinates = None


# ============================================================
# 4. VALIDATE EACH MONTH
# ============================================================

print_header("3. MONTH-BY-MONTH VALIDATION")

for index, month in enumerate(EXPECTED_MONTH_STRINGS, start=1):

    file_path = DATA_DIR / f"{month}.csv"

    print(
        f"\n[{index:03d}/{EXPECTED_MONTH_COUNT}] "
        f"{month}",
        end=" "
    )

    month_result = {
        "month": month,
        "file_exists": False,
        "readable": False,
        "required_columns": False,
        "rows": 0,
        "expected_cells": EXPECTED_CELLS,
        "duplicate_cells": 0,
        "missing_values": 0,
        "invalid_soil_moisture": 0,
        "invalid_coverage": 0,
        "invalid_observations": 0,
        "coordinate_errors": 0,
        "mean_soil_moisture": np.nan,
        "min_soil_moisture": np.nan,
        "max_soil_moisture": np.nan,
        "mean_coverage": np.nan,
        "min_coverage": np.nan,
        "max_coverage": np.nan,
        "min_observations": np.nan,
        "max_observations": np.nan,
        "status": "FAIL",
        "error": "",
    }

    # --------------------------------------------------------
    # File exists
    # --------------------------------------------------------

    if not file_path.exists():
        month_result["error"] = "Missing file"
        qa_rows.append(month_result)

        global_errors.append(
            f"{month}: missing file"
        )

        print("❌ MISSING")
        continue

    month_result["file_exists"] = True

    # --------------------------------------------------------
    # Read CSV
    # --------------------------------------------------------

    try:
        df = pd.read_csv(file_path)
        month_result["readable"] = True
    except Exception as exc:
        month_result["error"] = (
            f"CSV read error: {exc}"
        )

        qa_rows.append(month_result)

        global_errors.append(
            f"{month}: CSV read error: {exc}"
        )

        print("❌ READ ERROR")
        continue

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    missing_columns = [
        col
        for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing_columns:
        month_result["error"] = (
            "Missing columns: "
            + ", ".join(missing_columns)
        )

        qa_rows.append(month_result)

        global_errors.append(
            f"{month}: missing columns {missing_columns}"
        )

        print("❌ COLUMNS")
        continue

    month_result["required_columns"] = True

    # --------------------------------------------------------
    # Row count
    # --------------------------------------------------------

    rows = len(df)

    month_result["rows"] = rows

    total_records += rows

    # --------------------------------------------------------
    # Month column
    # --------------------------------------------------------

    month_column_values = (
        df["month"]
        .astype(str)
        .str.strip()
    )

    wrong_month_count = (
        month_column_values != month
    ).sum()

    if wrong_month_count:
        global_errors.append(
            f"{month}: {wrong_month_count} rows "
            f"have incorrect month value"
        )

        month_result["error"] = (
            f"{wrong_month_count} incorrect month values"
        )

    # --------------------------------------------------------
    # Duplicate cells
    # --------------------------------------------------------

    duplicate_mask = df.duplicated(
        subset=["row", "col"],
        keep=False,
    )

    duplicate_cells = int(
        duplicate_mask.sum()
    )

    month_result["duplicate_cells"] = duplicate_cells

    total_duplicate_records += duplicate_cells

    if duplicate_cells:
        global_errors.append(
            f"{month}: {duplicate_cells} "
            f"duplicate cell records"
        )

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    relevant_df = df[REQUIRED_COLUMNS]

    missing_values = int(
        relevant_df.isna().sum().sum()
    )

    month_result["missing_values"] = missing_values

    total_missing_values += missing_values

    if missing_values:
        global_errors.append(
            f"{month}: {missing_values} missing values"
        )

    # --------------------------------------------------------
    # Soil moisture validation
    # --------------------------------------------------------

    sm = pd.to_numeric(
        df["soil_moisture_mean"],
        errors="coerce",
    )

    invalid_sm_mask = (
        sm.isna()
        | (sm < MIN_SOIL_MOISTURE)
        | (sm > MAX_SOIL_MOISTURE)
    )

    invalid_sm = int(
        invalid_sm_mask.sum()
    )

    month_result["invalid_soil_moisture"] = invalid_sm

    total_invalid_sm += invalid_sm

    if invalid_sm:
        global_errors.append(
            f"{month}: {invalid_sm} "
            f"invalid soil-moisture values"
        )

    if sm.notna().any():
        month_result["mean_soil_moisture"] = float(
            sm.mean()
        )

        month_result["min_soil_moisture"] = float(
            sm.min()
        )

        month_result["max_soil_moisture"] = float(
            sm.max()
        )

    # --------------------------------------------------------
    # Coverage validation
    # --------------------------------------------------------

    coverage = pd.to_numeric(
        df["coverage_fraction"],
        errors="coerce",
    )

    invalid_coverage_mask = (
        coverage.isna()
        | (coverage < 0)
        | (coverage > 1)
    )

    invalid_coverage = int(
        invalid_coverage_mask.sum()
    )

    month_result["invalid_coverage"] = invalid_coverage

    total_invalid_coverage += invalid_coverage

    if invalid_coverage:
        global_errors.append(
            f"{month}: {invalid_coverage} "
            f"invalid coverage values"
        )

    if coverage.notna().any():
        month_result["mean_coverage"] = float(
            coverage.mean()
        )

        month_result["min_coverage"] = float(
            coverage.min()
        )

        month_result["max_coverage"] = float(
            coverage.max()
        )

    # --------------------------------------------------------
    # Observation validation
    # --------------------------------------------------------

    observations = pd.to_numeric(
        df["observations"],
        errors="coerce",
    )

    expected_observations = pd.to_numeric(
        df["expected_observations"],
        errors="coerce",
    )

    invalid_observation_mask = (
        observations.isna()
        | expected_observations.isna()
        | (observations < 0)
        | (expected_observations <= 0)
        | (observations > expected_observations)
    )

    invalid_observations = int(
        invalid_observation_mask.sum()
    )

    month_result["invalid_observations"] = (
        invalid_observations
    )

    total_invalid_observations += (
        invalid_observations
    )

    if invalid_observations:
        global_errors.append(
            f"{month}: {invalid_observations} "
            f"invalid observation records"
        )

    if observations.notna().any():
        month_result["min_observations"] = float(
            observations.min()
        )

        month_result["max_observations"] = float(
            observations.max()
        )

    # --------------------------------------------------------
    # Coordinate validation
    # --------------------------------------------------------

    coordinates = df[
        ["row", "col", "latitude", "longitude"]
    ].copy()

    coordinates["row"] = pd.to_numeric(
        coordinates["row"],
        errors="coerce",
    )

    coordinates["col"] = pd.to_numeric(
        coordinates["col"],
        errors="coerce",
    )

    coordinates["latitude"] = pd.to_numeric(
        coordinates["latitude"],
        errors="coerce",
    )

    coordinates["longitude"] = pd.to_numeric(
        coordinates["longitude"],
        errors="coerce",
    )

    coordinate_errors = int(
        (
            coordinates[
                ["row", "col", "latitude", "longitude"]
            ].isna().any(axis=1)
        ).sum()
    )

    # --------------------------------------------------------
    # Coordinate consistency against first month
    # --------------------------------------------------------

    if (
        coordinate_errors == 0
        and len(df) == EXPECTED_CELLS
        and not duplicate_mask.any()
    ):

        current_coords = (
            df[
                ["row", "col", "latitude", "longitude"]
            ]
            .sort_values(["row", "col"])
            .reset_index(drop=True)
        )

        if reference_coordinates is None:

            reference_coordinates = current_coords.copy()

        else:

            try:

                same_rows_cols = np.array_equal(
                    current_coords[
                        ["row", "col"]
                    ].to_numpy(),
                    reference_coordinates[
                        ["row", "col"]
                    ].to_numpy(),
                )

                same_latitude = np.allclose(
                    current_coords["latitude"].to_numpy(
                        dtype=float
                    ),
                    reference_coordinates[
                        "latitude"
                    ].to_numpy(dtype=float),
                    rtol=0,
                    atol=1e-10,
                )

                same_longitude = np.allclose(
                    current_coords["longitude"].to_numpy(
                        dtype=float
                    ),
                    reference_coordinates[
                        "longitude"
                    ].to_numpy(dtype=float),
                    rtol=0,
                    atol=1e-10,
                )

                if not (
                    same_rows_cols
                    and same_latitude
                    and same_longitude
                ):
                    coordinate_errors += 1

            except Exception:
                coordinate_errors += 1

    month_result["coordinate_errors"] = coordinate_errors

    total_coordinate_errors += coordinate_errors

    if coordinate_errors:
        global_errors.append(
            f"{month}: coordinate consistency error"
        )

    # --------------------------------------------------------
    # Cell count
    # --------------------------------------------------------

    cell_count_ok = (
        rows == EXPECTED_CELLS
    )

    if not cell_count_ok:
        global_errors.append(
            f"{month}: expected "
            f"{EXPECTED_CELLS} cells, found {rows}"
        )

    # --------------------------------------------------------
    # Final month status
    # --------------------------------------------------------

    month_ok = (
        month_result["file_exists"]
        and month_result["readable"]
        and month_result["required_columns"]
        and rows == EXPECTED_CELLS
        and duplicate_cells == 0
        and missing_values == 0
        and invalid_sm == 0
        and invalid_coverage == 0
        and invalid_observations == 0
        and coordinate_errors == 0
        and wrong_month_count == 0
    )

    if month_ok:
        month_result["status"] = "PASS"
        print("✅ PASS")
    else:
        month_result["status"] = "FAIL"
        print("❌ FAIL")

    qa_rows.append(month_result)


# ============================================================
# 5. MONTHLY QA REPORT
# ============================================================

print_header("4. MONTHLY QA SUMMARY")

qa_df = pd.DataFrame(qa_rows)

qa_report_path = (
    REPORT_DIR / "final_dataset_qa_monthly.csv"
)

qa_df.to_csv(
    qa_report_path,
    index=False,
)

passed_months = int(
    (qa_df["status"] == "PASS").sum()
)

failed_months = int(
    (qa_df["status"] == "FAIL").sum()
)

print(f"Passed months : {passed_months}")
print(f"Failed months : {failed_months}")

print()
print(
    f"Monthly QA report written to:"
    f"\n  {qa_report_path}"
)


# ============================================================
# 6. GLOBAL DATASET CHECKS
# ============================================================

print_header("5. GLOBAL DATASET CHECKS")

global_checks = {}

global_checks[
    "expected_month_count"
] = EXPECTED_MONTH_COUNT

global_checks[
    "actual_month_count"
] = len(actual_months)

global_checks[
    "missing_month_count"
] = len(missing_months)

global_checks[
    "unexpected_month_count"
] = len(unexpected_months)

global_checks[
    "expected_cells_per_month"
] = EXPECTED_CELLS

global_checks[
    "expected_total_records"
] = EXPECTED_TOTAL_RECORDS

global_checks[
    "actual_total_records"
] = total_records

global_checks[
    "duplicate_records"
] = total_duplicate_records

global_checks[
    "missing_values"
] = total_missing_values

global_checks[
    "invalid_soil_moisture"
] = total_invalid_sm

global_checks[
    "invalid_coverage"
] = total_invalid_coverage

global_checks[
    "invalid_observations"
] = total_invalid_observations

global_checks[
    "coordinate_errors"
] = total_coordinate_errors


def global_check(
    name: str,
    condition: bool,
) -> None:

    global_checks[name] = bool(condition)

    check(condition, name)


global_check(
    "all_expected_months_present",
    not missing_months,
)

global_check(
    "no_unexpected_months",
    not unexpected_months,
)

global_check(
    "all_months_pass",
    failed_months == 0,
)

global_check(
    "total_record_count_correct",
    total_records == EXPECTED_TOTAL_RECORDS,
)

global_check(
    "no_duplicate_records",
    total_duplicate_records == 0,
)

global_check(
    "no_missing_values",
    total_missing_values == 0,
)

global_check(
    "no_invalid_soil_moisture",
    total_invalid_sm == 0,
)

global_check(
    "no_invalid_coverage",
    total_invalid_coverage == 0,
)

global_check(
    "no_invalid_observations",
    total_invalid_observations == 0,
)

global_check(
    "coordinate_consistency_pass",
    total_coordinate_errors == 0,
)


# ============================================================
# 7. DATASET STATISTICS
# ============================================================

print_header("6. DATASET STATISTICS")

if len(qa_df):

    valid_sm = qa_df[
        [
            "mean_soil_moisture",
            "min_soil_moisture",
            "max_soil_moisture",
        ]
    ]

    print(
        f"Monthly mean SM range : "
        f"{valid_sm['mean_soil_moisture'].min():.6f} "
        f"→ "
        f"{valid_sm['mean_soil_moisture'].max():.6f}"
    )

    print(
        f"Monthly minimum SM    : "
        f"{valid_sm['min_soil_moisture'].min():.6f}"
    )

    print(
        f"Monthly maximum SM    : "
        f"{valid_sm['max_soil_moisture'].max():.6f}"
    )

    print(
        f"Coverage range        : "
        f"{qa_df['min_coverage'].min():.6f} "
        f"→ "
        f"{qa_df['max_coverage'].max():.6f}"
    )


# ============================================================
# 8. FINAL DATASET RESULT
# ============================================================

print_header("7. FINAL DATASET VERDICT")

all_pass = (
    not missing_months
    and not unexpected_months
    and failed_months == 0
    and total_records == EXPECTED_TOTAL_RECORDS
    and total_duplicate_records == 0
    and total_missing_values == 0
    and total_invalid_sm == 0
    and total_invalid_coverage == 0
    and total_invalid_observations == 0
    and total_coordinate_errors == 0
)


if all_pass:

    verdict = "PASS"

    print()
    print("🎉 DATASET QA PASSED")
    print()
    print("The SMAP dataset is ready for scientific analysis.")
    print()
    print(
        f"Period              : {START_MONTH} → {END_MONTH}"
    )
    print(
        f"Months              : {EXPECTED_MONTH_COUNT}"
    )
    print(
        f"Cells/month         : {EXPECTED_CELLS:,}"
    )
    print(
        f"Total records       : {total_records:,}"
    )
    print()
    print("DATASET STATUS: FROZEN / ANALYSIS READY")

else:

    verdict = "FAIL"

    print()
    print("❌ DATASET QA FAILED")
    print()
    print(
        "The dataset must NOT be used for final scientific "
        "trend analysis until the failures are fixed."
    )

    if global_errors:

        print()
        print("Detected problems:")

        for error in global_errors[:100]:
            print(f"  ❌ {error}")

        if len(global_errors) > 100:
            print(
                f"\n  ... and "
                f"{len(global_errors) - 100} more problems."
            )


# ============================================================
# 9. JSON QA REPORT
# ============================================================

elapsed_seconds = time.time() - start_time

final_report = {
    "project": "EarthTrend Detective",
    "dataset": "NASA SMAP SPL4SMGP",
    "variable": "/Geophysical_Data/sm_surface",

    "period": {
        "start": START_MONTH,
        "end": END_MONTH,
        "months": EXPECTED_MONTH_COUNT,
    },

    "spatial": {
        "expected_cells_per_month": EXPECTED_CELLS,
    },

    "records": {
        "expected": EXPECTED_TOTAL_RECORDS,
        "actual": total_records,
    },

    "validation": {
        "passed_months": passed_months,
        "failed_months": failed_months,
        "missing_months": missing_months,
        "unexpected_months": unexpected_months,
        "duplicate_records": total_duplicate_records,
        "missing_values": total_missing_values,
        "invalid_soil_moisture": total_invalid_sm,
        "invalid_coverage": total_invalid_coverage,
        "invalid_observations": total_invalid_observations,
        "coordinate_errors": total_coordinate_errors,
    },

    "soil_moisture_range": {
        "minimum_allowed": MIN_SOIL_MOISTURE,
        "maximum_allowed": MAX_SOIL_MOISTURE,
    },

    "verdict": verdict,

    "runtime_seconds": round(
        elapsed_seconds,
        3,
    ),

    "global_errors": global_errors,
}


json_report_path = (
    REPORT_DIR / "final_dataset_qa.json"
)

with open(
    json_report_path,
    "w",
    encoding="utf-8",
) as f:

    json.dump(
        final_report,
        f,
        indent=2,
    )


# ============================================================
# 10. FINAL SUMMARY
# ============================================================

print_header("8. QA REPORTS")

print(
    f"Monthly report:"
    f"\n  {qa_report_path}"
)

print(
    f"\nJSON report:"
    f"\n  {json_report_path}"
)

print(
    f"\nRuntime: {elapsed_seconds:.2f} seconds"
)

print()

if all_pass:
    print("✅ FINAL RESULT: PASS")
    print("🛰️ Dataset is ready for scientific analysis.")
    sys.exit(0)

else:
    print("❌ FINAL RESULT: FAIL")
    print("⚠️ Fix dataset issues before analysis.")
    sys.exit(1)
