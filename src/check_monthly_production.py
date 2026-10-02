#!/usr/bin/env python3

import sys
import numpy as np
import pandas as pd


EXPECTED_CELLS = 984


def check_month(month):

    path = f"data/monthly/{month}.csv"

    print("=" * 70)
    print("EarthTrend Detective — Monthly Production Validation")
    print(f"Month: {month}")
    print("=" * 70)

    df = pd.read_csv(path)

    required = [
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

    missing_columns = [
        col for col in required
        if col not in df.columns
    ]

    if missing_columns:
        print("STATUS: FAIL")
        print(f"Missing columns: {missing_columns}")
        return 1

    # -----------------------------------------------------
    # Cell count
    # -----------------------------------------------------

    print(f"Rows:                 {len(df)}")

    unique_cells = df[["row", "col"]].drop_duplicates()

    print(
        f"Unique cells:         "
        f"{len(unique_cells)}"
    )

    duplicate_cells = (
        df.duplicated(
            subset=["row", "col"]
        ).sum()
    )

    print(
        f"Duplicate cells:      "
        f"{duplicate_cells}"
    )

    # -----------------------------------------------------
    # Month
    # -----------------------------------------------------

    print(
        f"Month values:         "
        f"{df['month'].unique().tolist()}"
    )

    # -----------------------------------------------------
    # Observation coverage
    # -----------------------------------------------------

    print(
        f"Observations min:     "
        f"{df['observations'].min()}"
    )

    print(
        f"Observations max:     "
        f"{df['observations'].max()}"
    )

    print(
        f"Expected observations:"
        f" {df['expected_observations'].unique().tolist()}"
    )

    print(
        f"Coverage min:         "
        f"{df['coverage_fraction'].min():.6f}"
    )

    print(
        f"Coverage max:         "
        f"{df['coverage_fraction'].max():.6f}"
    )

    # -----------------------------------------------------
    # Coordinates
    # -----------------------------------------------------

    print(
        f"Latitude:             "
        f"{df['latitude'].min():.6f} - "
        f"{df['latitude'].max():.6f}"
    )

    print(
        f"Longitude:            "
        f"{df['longitude'].min():.6f} - "
        f"{df['longitude'].max():.6f}"
    )

    # -----------------------------------------------------
    # Soil moisture
    # -----------------------------------------------------

    sm = df["soil_moisture_mean"]

    print(
        f"Soil moisture min:    "
        f"{sm.min():.8f}"
    )

    print(
        f"Soil moisture max:    "
        f"{sm.max():.8f}"
    )

    print(
        f"Soil moisture mean:   "
        f"{sm.mean():.8f}"
    )

    print(
        f"Soil moisture missing:"
        f" {sm.isna().sum()}"
    )

    # -----------------------------------------------------
    # Validation rules
    # -----------------------------------------------------

    checks = {}

    checks["984 cells"] = (
        len(df) == EXPECTED_CELLS
        and len(unique_cells) == EXPECTED_CELLS
    )

    checks["No duplicate cells"] = (
        duplicate_cells == 0
    )

    checks["No missing soil moisture"] = (
        sm.isna().sum() == 0
    )

    checks["Soil moisture range"] = (
        sm.ge(0.0).all()
        and sm.le(0.9).all()
    )

    checks["Coverage <= 1"] = (
        df["coverage_fraction"].le(1.0).all()
    )

    checks["Coverage > 0"] = (
        df["coverage_fraction"].gt(0.0).all()
    )

    checks["Valid coordinates"] = (
        df["latitude"].between(-90, 90).all()
        and df["longitude"].between(-180, 180).all()
    )

    print("\nValidation checks:")

    all_pass = True

    for name, result in checks.items():

        status = "PASS" if result else "FAIL"

        print(
            f"  {name:<30} {status}"
        )

        if not result:
            all_pass = False

    print("\n" + "=" * 70)

    if all_pass:
        print("STATUS: PASS")
        print(
            f"{month} production monthly dataset "
            f"passed validation."
        )
        return 0

    print("STATUS: FAIL")
    return 1


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print(
            "Usage: python "
            "src/check_monthly_production.py YYYY-MM"
        )
        sys.exit(1)

    sys.exit(
        check_month(sys.argv[1])
    )
