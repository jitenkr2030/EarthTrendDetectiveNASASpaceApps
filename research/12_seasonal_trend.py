from pathlib import Path
import json
import time

import numpy as np
import pandas as pd
from scipy.stats import kendalltau


BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = BASE_DIR / "data" / "analysis" / "smap_monthly_jharkhand.csv"
OUTPUT_DIR = BASE_DIR / "data" / "analysis"

STATE_OUTPUT = OUTPUT_DIR / "smap_seasonal_state_trends.csv"
CELL_OUTPUT = OUTPUT_DIR / "smap_seasonal_cell_trends.csv"
MANIFEST_OUTPUT = OUTPUT_DIR / "smap_seasonal_trend_manifest.json"

ALPHA = 0.05
EXPECTED_CELLS = 984

SEASON_ORDER = [
    "winter",
    "pre-monsoon",
    "monsoon",
    "post-monsoon",
]

EXPECTED_SEASON_YEARS = {
    "winter": 11,
    "pre-monsoon": 12,
    "monsoon": 12,
    "post-monsoon": 11,
}

SEASON_RANK = {
    "winter": 1,
    "pre-monsoon": 2,
    "monsoon": 3,
    "post-monsoon": 4,
}


def sen_slope(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    if len(x) < 2:
        return np.nan

    slopes = []

    for i in range(len(x) - 1):
        dx = x[i + 1:] - x[i]
        dy = y[i + 1:] - y[i]

        valid = dx != 0

        if np.any(valid):
            slopes.extend((dy[valid] / dx[valid]).tolist())

    if not slopes:
        return np.nan

    return float(np.median(slopes))


def run_kendall(x, y):
    if len(y) < 3:
        return np.nan, np.nan

    result = kendalltau(x, y)

    return (
        float(result.statistic),
        float(result.pvalue),
    )


def classify_trend(slope, p_value):
    if not np.isfinite(slope) or not np.isfinite(p_value):
        return "insufficient-data"

    if p_value < ALPHA:
        if slope > 0:
            return "significant-increasing"
        elif slope < 0:
            return "significant-decreasing"
        return "no-change"

    if slope > 0:
        return "non-significant-increasing"

    if slope < 0:
        return "non-significant-decreasing"

    return "no-change"


def main():

    start_time = time.time()

    print("=" * 70)
    print("EARTH TREND DETECTIVE")
    print("MODULE 12 - SEASONAL TREND ANALYSIS")
    print("=" * 70)

    # ========================================================
    # 1. LOAD DATA
    # ========================================================

    print("\n[1/8] Loading canonical analysis dataset...")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Canonical dataset not found:\n{INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    print(f"Loaded records: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    # ========================================================
    # 2. SCHEMA VALIDATION
    # ========================================================

    print("\n[2/8] Validating schema...")

    required_columns = {
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

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    df["date"] = pd.to_datetime(df["date"])

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
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    if df[numeric_columns].isna().any().any():
        raise ValueError(
            "Numeric columns contain missing values."
        )

    df["season"] = df["season"].astype(str)

    unexpected = set(df["season"].unique()) - set(SEASON_ORDER)

    if unexpected:
        raise ValueError(
            f"Unexpected seasons: {sorted(unexpected)}"
        )

    # ========================================================
    # 3. SPATIAL GRID
    # ========================================================

    print("\n[3/8] Validating spatial grid...")

    cells = (
        df[
            [
                "row",
                "col",
                "latitude",
                "longitude",
            ]
        ]
        .drop_duplicates()
    )

    if len(cells) != EXPECTED_CELLS:
        raise ValueError(
            f"Expected {EXPECTED_CELLS} cells, "
            f"found {len(cells)}."
        )

    print(f"Unique spatial cells: {len(cells):,}")
    print("Spatial grid validation: PASS")

    # ========================================================
    # 4. SEASONAL-YEAR AGGREGATION
    # ========================================================

    print("\n[4/8] Building seasonal-year means...")

    # State-wide seasonal mean
    state_seasonal = (
        df.groupby(
            ["season", "year"],
            as_index=False
        )
        .agg(
            seasonal_soil_moisture=(
                "soil_moisture",
                "mean"
            ),
            cell_count=(
                "soil_moisture",
                "count"
            ),
            monthly_record_count=(
                "soil_moisture",
                "size"
            ),
        )
    )

    state_seasonal["year"] = (
        state_seasonal["year"].astype(int)
    )

    state_seasonal["season_rank"] = (
        state_seasonal["season"].map(SEASON_RANK)
    )

    state_seasonal = (
        state_seasonal
        .sort_values(
            ["season_rank", "year"]
        )
        .drop(columns=["season_rank"])
        .reset_index(drop=True)
    )

    print(
        f"State seasonal-year rows: "
        f"{len(state_seasonal):,}"
    )

    # Cell-level seasonal mean
    cell_seasonal = (
        df.groupby(
            [
                "season",
                "row",
                "col",
                "latitude",
                "longitude",
                "year",
            ],
            as_index=False
        )
        .agg(
            seasonal_soil_moisture=(
                "soil_moisture",
                "mean"
            ),
            monthly_record_count=(
                "soil_moisture",
                "size"
            ),
        )
    )

    cell_seasonal["year"] = (
        cell_seasonal["year"].astype(int)
    )

    cell_seasonal["season_rank"] = (
        cell_seasonal["season"].map(SEASON_RANK)
    )

    cell_seasonal = (
        cell_seasonal
        .sort_values(
            [
                "season_rank",
                "row",
                "col",
                "year",
            ]
        )
        .drop(columns=["season_rank"])
        .reset_index(drop=True)
    )

    print(
        f"Cell seasonal-year rows: "
        f"{len(cell_seasonal):,}"
    )

    # ========================================================
    # 5. COVERAGE VALIDATION
    # ========================================================

    print("\n[5/8] Validating seasonal coverage...")

    state_year_counts = (
        state_seasonal
        .groupby("season")["year"]
        .nunique()
        .to_dict()
    )

    for season in SEASON_ORDER:

        actual = int(
            state_year_counts.get(season, 0)
        )

        expected = EXPECTED_SEASON_YEARS[season]

        print(
            f"{season:15s} "
            f"years={actual:2d} "
            f"expected={expected:2d}"
        )

        if actual != expected:
            raise ValueError(
                f"{season}: expected {expected} years, "
                f"found {actual}."
            )

    # Critical validation:
    # Every cell must have expected number of years
    for season in SEASON_ORDER:

        expected_years = EXPECTED_SEASON_YEARS[season]

        sub = cell_seasonal[
            cell_seasonal["season"] == season
        ]

        cell_year_counts = (
            sub.groupby(
                ["row", "col"]
            )["year"]
            .nunique()
        )

        if len(cell_year_counts) != EXPECTED_CELLS:
            raise ValueError(
                f"{season}: expected "
                f"{EXPECTED_CELLS} cells, "
                f"found {len(cell_year_counts)}."
            )

        bad_cells = (
            cell_year_counts[
                cell_year_counts != expected_years
            ]
        )

        if len(bad_cells) > 0:
            raise ValueError(
                f"{season}: {len(bad_cells)} cells "
                f"have incorrect year coverage."
            )

    print("Seasonal coverage validation: PASS")

    # ========================================================
    # 6. STATE-WIDE SEASONAL TRENDS
    # ========================================================

    print(
        "\n[6/8] Calculating state-wide seasonal trends..."
    )

    state_results = []

    for season in SEASON_ORDER:

        sub = (
            state_seasonal[
                state_seasonal["season"] == season
            ]
            .sort_values("year")
        )

        years = sub["year"].to_numpy(
            dtype=float
        )

        values = sub[
            "seasonal_soil_moisture"
        ].to_numpy(
            dtype=float
        )

        slope = sen_slope(
            years,
            values
        )

        tau, p_value = run_kendall(
            years,
            values
        )

        significant = bool(
            p_value < ALPHA
        )

        trend_class = classify_trend(
            slope,
            p_value
        )

        state_results.append(
            {
                "season": season,
                "years_available": len(values),
                "first_year": int(years.min()),
                "last_year": int(years.max()),
                "mean_soil_moisture": float(
                    np.mean(values)
                ),
                "minimum_seasonal_mean": float(
                    np.min(values)
                ),
                "maximum_seasonal_mean": float(
                    np.max(values)
                ),
                "sen_slope_per_year": slope,
                "kendall_tau": tau,
                "p_value": p_value,
                "significant_at_0_05": significant,
                "trend_class": trend_class,
            }
        )

    state_results_df = pd.DataFrame(
        state_results
    )

    print("\nSTATE-WIDE SEASONAL RESULTS")
    print("-" * 70)

    for _, result in state_results_df.iterrows():

        print(
            f"{result['season']:15s} "
            f"slope/year="
            f"{result['sen_slope_per_year']:.10f} "
            f"tau="
            f"{result['kendall_tau']:.6f} "
            f"p="
            f"{result['p_value']:.6f} "
            f"{result['trend_class']}"
        )

    # ========================================================
    # 7. CELL-LEVEL SEASONAL TRENDS
    # ========================================================

    print(
        "\n[7/8] Calculating cell-level seasonal trends..."
    )

    cell_results = []

    grouped = cell_seasonal.groupby(
        [
            "season",
            "row",
            "col",
            "latitude",
            "longitude",
        ]
    )

    for (
        season,
        row_idx,
        col_idx,
        latitude,
        longitude,
    ), sub in grouped:

        sub = sub.sort_values("year")

        years = sub["year"].to_numpy(
            dtype=float
        )

        values = sub[
            "seasonal_soil_moisture"
        ].to_numpy(
            dtype=float
        )

        slope = sen_slope(
            years,
            values
        )

        tau, p_value = run_kendall(
            years,
            values
        )

        significant = bool(
            p_value < ALPHA
        )

        trend_class = classify_trend(
            slope,
            p_value
        )

        cell_results.append(
            {
                "season": season,
                "row": int(row_idx),
                "col": int(col_idx),
                "latitude": float(latitude),
                "longitude": float(longitude),
                "years_available": len(values),
                "first_year": int(years.min()),
                "last_year": int(years.max()),
                "mean_seasonal_soil_moisture": float(
                    np.mean(values)
                ),
                "minimum_seasonal_mean": float(
                    np.min(values)
                ),
                "maximum_seasonal_mean": float(
                    np.max(values)
                ),
                "sen_slope_per_year": slope,
                "kendall_tau": tau,
                "p_value": p_value,
                "significant_at_0_05": significant,
                "trend_class": trend_class,
            }
        )

    cell_results_df = pd.DataFrame(
        cell_results
    )

    expected_cell_results = (
        EXPECTED_CELLS
        * len(SEASON_ORDER)
    )

    print(
        f"Cell-season trend rows: "
        f"{len(cell_results_df):,}"
    )

    if len(cell_results_df) != expected_cell_results:
        raise ValueError(
            f"Expected {expected_cell_results:,} "
            f"cell-season results, "
            f"found {len(cell_results_df):,}."
        )

    # ========================================================
    # CELL SUMMARY
    # ========================================================

    print("\nCELL-LEVEL SUMMARY")
    print("-" * 70)

    for season in SEASON_ORDER:

        sub = cell_results_df[
            cell_results_df["season"] == season
        ]

        significant = int(
            sub["significant_at_0_05"].sum()
        )

        increasing = int(
            (
                sub["sen_slope_per_year"] > 0
            ).sum()
        )

        decreasing = int(
            (
                sub["sen_slope_per_year"] < 0
            ).sum()
        )

        print(
            f"{season:15s} "
            f"cells={len(sub):4d} "
            f"increasing={increasing:4d} "
            f"decreasing={decreasing:4d} "
            f"significant={significant:4d}"
        )

    # ========================================================
    # 8. WRITE OUTPUTS
    # ========================================================

    print("\n[8/8] Writing analysis outputs...")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    state_results_df.to_csv(
        STATE_OUTPUT,
        index=False
    )

    cell_results_df.to_csv(
        CELL_OUTPUT,
        index=False
    )

    # ========================================================
    # FINAL RELOAD VALIDATION
    # ========================================================

    state_check = pd.read_csv(
        STATE_OUTPUT
    )

    cell_check = pd.read_csv(
        CELL_OUTPUT
    )

    if len(state_check) != 4:
        raise ValueError(
            "State output validation failed."
        )

    if len(cell_check) != expected_cell_results:
        raise ValueError(
            "Cell output validation failed."
        )

    duplicate_check = cell_check[
        [
            "season",
            "row",
            "col",
        ]
    ].duplicated().any()

    if duplicate_check:
        raise ValueError(
            "Duplicate cell-season results found."
        )

    # ========================================================
    # MANIFEST
    # ========================================================

    significant_state = int(
        state_check[
            "significant_at_0_05"
        ].sum()
    )

    significant_cells = int(
        cell_check[
            "significant_at_0_05"
        ].sum()
    )

    increasing_cells = int(
        (
            cell_check[
                "sen_slope_per_year"
            ] > 0
        ).sum()
    )

    decreasing_cells = int(
        (
            cell_check[
                "sen_slope_per_year"
            ] < 0
        ).sum()
    )

    manifest = {
        "module": "12_seasonal_trend",
        "status": "PASS",

        "dataset": {
            "input": str(INPUT_FILE),
            "records": int(len(df)),
            "cells": EXPECTED_CELLS,
            "period_start": str(
                df["date"].min().date()
            ),
            "period_end": str(
                df["date"].max().date()
            ),
        },

        "method": {
            "seasonal_aggregation":
                "mean soil moisture per season-year",
            "trend_estimator":
                "exact Sen's slope",
            "slope_unit":
                "soil_moisture_per_year",
            "monotonic_test":
                "scipy.stats.kendalltau",
            "alpha": ALPHA,
            "statistical_note":
                "This is a first-pass seasonal "
                "monotonic trend test. It is not "
                "an autocorrelation-corrected "
                "Seasonal Mann-Kendall implementation.",
        },

        "season_definition": {
            "winter":
                "January-February",
            "pre-monsoon":
                "March-May",
            "monsoon":
                "June-September",
            "post-monsoon":
                "October-December",
        },

        "expected_season_years":
            EXPECTED_SEASON_YEARS,

        "results": {
            "state_seasons":
                int(len(state_check)),
            "significant_state_seasons":
                significant_state,
            "cell_season_results":
                int(len(cell_check)),
            "significant_cell_seasons":
                significant_cells,
            "increasing_cell_seasons":
                increasing_cells,
            "decreasing_cell_seasons":
                decreasing_cells,
        },

        "outputs": {
            "state":
                str(STATE_OUTPUT),
            "cell":
                str(CELL_OUTPUT),
            "manifest":
                str(MANIFEST_OUTPUT),
        },

        "validation": {
            "state_rows_pass":
                len(state_check) == 4,
            "cell_rows_pass":
                len(cell_check) == expected_cell_results,
            "duplicate_cell_season_pass":
                not duplicate_check,
            "status":
                "PASS",
        },
    }

    with open(
        MANIFEST_OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            manifest,
            f,
            indent=2
        )

    elapsed = time.time() - start_time

    # ========================================================
    # FINAL
    # ========================================================

    print("\n" + "=" * 70)
    print("MODULE 12 COMPLETE")
    print("=" * 70)

    print(
        f"State seasonal results: "
        f"{len(state_check)}"
    )

    print(
        f"Cell-season results: "
        f"{len(cell_check):,}"
    )

    print(
        f"Significant state seasons: "
        f"{significant_state}"
    )

    print(
        f"Significant cell-season results: "
        f"{significant_cells:,}"
    )

    print(
        f"Increasing cell-season results: "
        f"{increasing_cells:,}"
    )

    print(
        f"Decreasing cell-season results: "
        f"{decreasing_cells:,}"
    )

    print("\nOutputs:")
    print(STATE_OUTPUT)
    print(CELL_OUTPUT)
    print(MANIFEST_OUTPUT)

    print(
        f"\nRuntime: {elapsed:.2f} seconds"
    )

    print("\nSTATUS: PASS")
    print("=" * 70)


if __name__ == "__main__":
    main()
