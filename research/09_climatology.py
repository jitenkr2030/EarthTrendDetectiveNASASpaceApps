from pathlib import Path
import json

import numpy as np
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "analysis" / "smap_monthly_jharkhand.csv"

OUTPUT_DIR = ROOT / "data" / "analysis"
OUTPUT = OUTPUT_DIR / "smap_climatology.csv"
MANIFEST = OUTPUT_DIR / "smap_climatology_manifest.json"


EXPECTED_MONTHS = 138
EXPECTED_CELLS = 984


# ============================================================
# HELPERS
# ============================================================

def fail(message):
    raise RuntimeError(f"\nFAIL: {message}\n")


def validate_input(df):
    required = {
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
    }

    missing = required - set(df.columns)

    if missing:
        fail(f"Missing columns: {sorted(missing)}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    if df["date"].isna().any():
        fail("Invalid dates found")

    numeric_columns = [
        "year",
        "month_number",
        "row",
        "col",
        "latitude",
        "longitude",
        "soil_moisture",
        "observations",
        "expected_observations",
        "coverage_fraction",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    if df[numeric_columns].isna().any().any():
        fail("Missing/non-numeric values found")

    if len(df) != EXPECTED_MONTHS * EXPECTED_CELLS:
        fail(
            f"Unexpected record count: {len(df)} "
            f"(expected {EXPECTED_MONTHS * EXPECTED_CELLS})"
        )

    month_count = df["date"].dt.to_period("M").nunique()

    if month_count != EXPECTED_MONTHS:
        fail(
            f"Unexpected number of months: {month_count} "
            f"(expected {EXPECTED_MONTHS})"
        )

    cell_count = df[["row", "col"]].drop_duplicates().shape[0]

    if cell_count != EXPECTED_CELLS:
        fail(
            f"Unexpected spatial cell count: {cell_count} "
            f"(expected {EXPECTED_CELLS})"
        )

    duplicate_count = df.duplicated(
        subset=["date", "row", "col"]
    ).sum()

    if duplicate_count:
        fail(f"Duplicate date/cell records: {duplicate_count}")

    if df["soil_moisture"].lt(0).any() or df["soil_moisture"].gt(1).any():
        fail("Soil moisture outside [0,1]")

    return df


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 70)
    print("EARTH TREND DETECTIVE — CLIMATOLOGY ENGINE")
    print("=" * 70)

    if not INPUT.exists():
        fail(f"Input dataset not found: {INPUT}")

    print(f"\nInput:")
    print(INPUT)

    print("\nLoading canonical analysis dataset...")

    df = pd.read_csv(INPUT)

    print(f"Records loaded: {len(df):,}")

    # --------------------------------------------------------
    # VALIDATE
    # --------------------------------------------------------

    print("\nValidating input...")

    df = validate_input(df)

    print("PASS input validation")

    # --------------------------------------------------------
    # CALENDAR FIELDS
    # --------------------------------------------------------

    df["calendar_month"] = df["date"].dt.month

    # --------------------------------------------------------
    # CLIMATOLOGY
    #
    # Baseline:
    # each spatial cell × calendar month
    #
    # Example:
    # cell (row=480,col=2840)
    # January 2016
    # January 2017
    # ...
    # January 2026
    #
    # -> January climatology for that cell
    # --------------------------------------------------------

    print("\nCalculating spatially resolved monthly climatology...")

    grouped = (
        df.groupby(
            [
                "row",
                "col",
                "latitude",
                "longitude",
                "calendar_month",
            ],
            as_index=False,
        )
        .agg(
            climatology_mean=("soil_moisture", "mean"),
            climatology_std=("soil_moisture", "std"),
            climatology_min=("soil_moisture", "min"),
            climatology_max=("soil_moisture", "max"),
            years_available=("year", "nunique"),
            observations_total=("observations", "sum"),
        )
    )

    # --------------------------------------------------------
    # MONTH NAME
    # --------------------------------------------------------

    month_names = {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December",
    }

    grouped["calendar_month_name"] = (
        grouped["calendar_month"].map(month_names)
    )

    # --------------------------------------------------------
    # SEASON
    # --------------------------------------------------------

    def season_for_month(month):
        if month in (1, 2):
            return "winter"
        if month in (3, 4, 5):
            return "pre-monsoon"
        if month in (6, 7, 8, 9):
            return "monsoon"
        return "post-monsoon"

    grouped["season"] = grouped["calendar_month"].map(season_for_month)

    # --------------------------------------------------------
    # EXPECTED CLIMATOLOGY RECORDS
    #
    # 984 cells × 12 calendar months
    # --------------------------------------------------------

    expected_climatology_rows = EXPECTED_CELLS * 12

    print(f"\nClimatology records: {len(grouped):,}")
    print(f"Expected records:    {expected_climatology_rows:,}")

    if len(grouped) != expected_climatology_rows:
        fail(
            f"Unexpected climatology record count: {len(grouped)}"
        )

    # --------------------------------------------------------
    # YEARS AVAILABLE
    #
    # Derive expected years directly from the canonical
    # analysis dataset instead of hard-coding assumptions.
    #
    # This is robust to datasets whose start/end dates do not
    # contain every calendar month.
    # --------------------------------------------------------

    available_years_by_month = (
        df.groupby("calendar_month")["year"]
        .nunique()
        .to_dict()
    )

    grouped["expected_years"] = grouped["calendar_month"].map(
        available_years_by_month
    )

    if (
        grouped["years_available"]
        != grouped["expected_years"]
    ).any():

        bad = grouped[
            grouped["years_available"]
            != grouped["expected_years"]
        ]

        fail(
            "Climatology year-count validation failed for "
            f"{len(bad)} records"
        )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if grouped["climatology_mean"].isna().any():
        fail("NaN climatology means found")

    if grouped["climatology_std"].isna().any():
        fail("NaN climatology standard deviations found")

    if grouped["climatology_mean"].lt(0).any() or \
       grouped["climatology_mean"].gt(1).any():
        fail("Climatology mean outside [0,1]")

    if grouped["climatology_min"].lt(0).any() or \
       grouped["climatology_min"].gt(1).any():
        fail("Climatology minimum outside [0,1]")

    if grouped["climatology_max"].lt(0).any() or \
       grouped["climatology_max"].gt(1).any():
        fail("Climatology maximum outside [0,1]")

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    grouped = grouped.sort_values(
        [
            "calendar_month",
            "row",
            "col",
        ]
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # FINAL COLUMNS
    # --------------------------------------------------------

    columns = [
        "calendar_month",
        "calendar_month_name",
        "season",
        "row",
        "col",
        "latitude",
        "longitude",
        "climatology_mean",
        "climatology_std",
        "climatology_min",
        "climatology_max",
        "years_available",
        "expected_years",
        "observations_total",
    ]

    grouped = grouped[columns]

    # --------------------------------------------------------
    # ATOMIC WRITE
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    temp_output = OUTPUT.with_suffix(".tmp.csv")

    grouped.to_csv(
        temp_output,
        index=False,
        float_format="%.10f",
    )

    temp_output.replace(OUTPUT)

    # --------------------------------------------------------
    # RELOAD CHECK
    # --------------------------------------------------------

    check = pd.read_csv(OUTPUT)

    if len(check) != expected_climatology_rows:
        fail(
            f"Reloaded record count mismatch: {len(check)}"
        )

    required_output = set(columns)

    if not required_output.issubset(check.columns):
        fail("Reloaded climatology schema mismatch")

    duplicate_output = check.duplicated(
        subset=["calendar_month", "row", "col"]
    ).sum()

    if duplicate_output:
        fail(
            f"Duplicate climatology records after reload: "
            f"{duplicate_output}"
        )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    state_monthly = (
        grouped.groupby(
            [
                "calendar_month",
                "calendar_month_name",
            ],
            as_index=False,
        )
        .agg(
            mean_soil_moisture=(
                "climatology_mean",
                "mean",
            ),
            std_across_cells=(
                "climatology_mean",
                "std",
            ),
            min_cell_value=(
                "climatology_mean",
                "min",
            ),
            max_cell_value=(
                "climatology_mean",
                "max",
            ),
        )
        .sort_values("calendar_month")
    )

    print("\n" + "-" * 70)
    print("STATE-WIDE CLIMATOLOGICAL FINGERPRINT")
    print("-" * 70)

    print(
        state_monthly[
            [
                "calendar_month_name",
                "mean_soil_moisture",
            ]
        ].to_string(index=False)
    )

    # --------------------------------------------------------
    # MANIFEST
    # --------------------------------------------------------

    manifest = {
        "status": "PASS",
        "input": str(INPUT.relative_to(ROOT)),
        "output": str(OUTPUT.relative_to(ROOT)),
        "source_period": {
            "start": str(df["date"].min().date()),
            "end": str(df["date"].max().date()),
        },
        "source_months": int(
            df["date"].dt.to_period("M").nunique()
        ),
        "spatial_cells": int(
            df[["row", "col"]].drop_duplicates().shape[0]
        ),
        "source_records": int(len(df)),
        "climatology_records": int(len(grouped)),
        "expected_climatology_records": expected_climatology_rows,
        "baseline_definition": (
            "spatial cell × calendar month across all "
            "available years"
        ),
        "calendar_months": 12,
        "season_definition": {
            "winter": [1, 2],
            "pre-monsoon": [3, 4, 5],
            "monsoon": [6, 7, 8, 9],
            "post-monsoon": [10, 11, 12],
        },
        "soil_moisture_range": {
            "min": float(grouped["climatology_min"].min()),
            "max": float(grouped["climatology_max"].max()),
        },
        "state_monthly_climatology": (
            state_monthly.to_dict(orient="records")
        ),
    }

    with MANIFEST.open("w", encoding="utf-8") as f:
        json.dump(
            manifest,
            f,
            indent=2,
        )

    # --------------------------------------------------------
    # FINAL REPORT
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("CLIMATOLOGY COMPLETE")
    print("=" * 70)

    print(f"\nSpatial cells:       {EXPECTED_CELLS:,}")
    print(f"Calendar months:    12")
    print(f"Climatology rows:   {len(grouped):,}")
    print(f"Expected rows:      {expected_climatology_rows:,}")

    print("\nOutput:")
    print(OUTPUT)

    print("\nManifest:")
    print(MANIFEST)

    print("\nPASS: Spatially resolved climatology is ready.")
    print("=" * 70)


if __name__ == "__main__":
    main()
