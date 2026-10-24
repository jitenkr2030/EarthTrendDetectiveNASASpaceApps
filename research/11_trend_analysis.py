from pathlib import Path
import json

import numpy as np
import pandas as pd
from scipy.stats import kendalltau


# ============================================================
# CONFIG
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "analysis" / "smap_monthly_jharkhand.csv"

OUTPUT_DIR = ROOT / "data" / "analysis"

STATE_OUTPUT = OUTPUT_DIR / "smap_state_trend.csv"
CELL_OUTPUT = OUTPUT_DIR / "smap_cell_trends.csv"
MANIFEST = OUTPUT_DIR / "smap_trend_manifest.json"

EXPECTED_MONTHS = 138
EXPECTED_CELLS = 984
EXPECTED_RECORDS = EXPECTED_MONTHS * EXPECTED_CELLS

ALPHA = 0.05


# ============================================================
# HELPERS
# ============================================================

def fail(message):
    raise RuntimeError(f"\nFAIL: {message}\n")


def sen_slope(values, times):
    """
    Exact Sen slope.

    For n observations, calculate all pairwise slopes:
        (y_j - y_i) / (t_j - t_i)

    and return the median.

    Time is represented as sequential monthly index.
    Therefore slope unit = soil-moisture units / month.
    """

    y = np.asarray(values, dtype=float)
    t = np.asarray(times, dtype=float)

    n = len(y)

    if n < 2:
        return np.nan

    slopes = []

    for i in range(n - 1):
        dy = y[i + 1:] - y[i]
        dt = t[i + 1:] - t[i]

        valid = dt != 0

        if np.any(valid):
            slopes.extend(
                (dy[valid] / dt[valid]).tolist()
            )

    if not slopes:
        return np.nan

    return float(np.median(slopes))


def mann_kendall(values):
    """
    Mann-Kendall test using Kendall's tau.

    For this exploratory/production pipeline we use scipy's
    Kendall tau to test monotonic association between time
    and the observed series.

    Returns:
        tau
        p_value
    """

    y = np.asarray(values, dtype=float)

    n = len(y)

    if n < 3:
        return np.nan, np.nan

    time = np.arange(n, dtype=float)

    result = kendalltau(
        time,
        y,
        nan_policy="omit",
    )

    return float(result.statistic), float(result.pvalue)


def classify_trend(slope, p_value):

    if pd.isna(slope) or pd.isna(p_value):
        return "undefined"

    if p_value < ALPHA:
        if slope > 0:
            return "significant increasing"

        if slope < 0:
            return "significant decreasing"

        return "significant no change"

    if slope > 0:
        return "non-significant increasing"

    if slope < 0:
        return "non-significant decreasing"

    return "non-significant no change"


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
        fail(
            f"Missing columns: {sorted(missing)}"
        )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

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
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    if df[numeric_columns].isna().any().any():
        fail("Missing/non-numeric values found")

    if len(df) != EXPECTED_RECORDS:
        fail(
            f"Unexpected record count: {len(df):,} "
            f"(expected {EXPECTED_RECORDS:,})"
        )

    duplicate_count = df.duplicated(
        subset=["date", "row", "col"]
    ).sum()

    if duplicate_count:
        fail(
            f"Duplicate date/cell records: "
            f"{duplicate_count}"
        )

    if (
        df["soil_moisture"].lt(0).any()
        or df["soil_moisture"].gt(1).any()
    ):
        fail(
            "Soil moisture outside [0,1]"
        )

    return df


# ============================================================
# STATE-WIDE MONTHLY SERIES
# ============================================================

def build_state_series(df):

    state = (
        df.groupby(
            "date",
            as_index=False,
        )
        .agg(
            mean_soil_moisture=(
                "soil_moisture",
                "mean",
            ),
            median_soil_moisture=(
                "soil_moisture",
                "median",
            ),
            std_across_cells=(
                "soil_moisture",
                "std",
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
        .sort_values("date")
        .reset_index(drop=True)
    )

    if len(state) != EXPECTED_MONTHS:
        fail(
            f"State series has {len(state)} months "
            f"(expected {EXPECTED_MONTHS})"
        )

    return state


# ============================================================
# CELL TRENDS
# ============================================================

def build_cell_trends(df):

    rows = []

    grouped = df.groupby(
        [
            "row",
            "col",
            "latitude",
            "longitude",
        ],
        sort=True,
    )

    total = len(grouped)

    print(
        f"\nCalculating trends for {total:,} cells..."
    )

    for counter, (
        (row, col, latitude, longitude),
        group,
    ) in enumerate(grouped, start=1):

        group = group.sort_values("date")

        values = group[
            "soil_moisture"
        ].to_numpy(dtype=float)

        dates = group["date"].to_numpy()

        if len(values) != EXPECTED_MONTHS:
            fail(
                f"Cell ({row}, {col}) has "
                f"{len(values)} observations "
                f"(expected {EXPECTED_MONTHS})"
            )

        times = np.arange(
            len(values),
            dtype=float,
        )

        slope = sen_slope(
            values,
            times,
        )

        tau, p_value = mann_kendall(
            values
        )

        trend_class = classify_trend(
            slope,
            p_value,
        )

        rows.append(
            {
                "row": int(row),
                "col": int(col),
                "latitude": float(latitude),
                "longitude": float(longitude),
                "observations": int(len(values)),
                "start_date": str(
                    pd.Timestamp(dates[0]).date()
                ),
                "end_date": str(
                    pd.Timestamp(dates[-1]).date()
                ),
                "mean_soil_moisture": float(
                    np.mean(values)
                ),
                "minimum_soil_moisture": float(
                    np.min(values)
                ),
                "maximum_soil_moisture": float(
                    np.max(values)
                ),
                "sen_slope_per_month": float(
                    slope
                ),
                "sen_slope_per_year": float(
                    slope * 12
                ),
                "kendall_tau": float(tau),
                "p_value": float(p_value),
                "significant_at_0_05": bool(
                    p_value < ALPHA
                ),
                "trend_class": trend_class,
            }
        )

        if counter % 100 == 0:
            print(
                f"  processed {counter:,}/{total:,}"
            )

    result = pd.DataFrame(rows)

    if len(result) != EXPECTED_CELLS:
        fail(
            f"Cell trend rows: {len(result):,} "
            f"(expected {EXPECTED_CELLS:,})"
        )

    return result


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 70)
    print("EARTH TREND DETECTIVE — TREND DETECTION ENGINE")
    print("=" * 70)

    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    if not INPUT.exists():
        fail(
            f"Input dataset not found: {INPUT}"
        )

    print("\nLoading canonical analysis dataset...")

    df = pd.read_csv(INPUT)

    print(
        f"Records loaded: {len(df):,}"
    )

    print("\nValidating input...")

    df = validate_input(df)

    print("PASS input validation")

    # --------------------------------------------------------
    # STATE SERIES
    # --------------------------------------------------------

    print(
        "\nBuilding state-wide monthly soil-moisture series..."
    )

    state = build_state_series(df)

    print(
        f"State series: {len(state):,} months"
    )

    # --------------------------------------------------------
    # STATE TREND
    # --------------------------------------------------------

    state_values = state[
        "mean_soil_moisture"
    ].to_numpy(dtype=float)

    state_times = np.arange(
        len(state_values),
        dtype=float,
    )

    state_slope = sen_slope(
        state_values,
        state_times,
    )

    state_tau, state_p = mann_kendall(
        state_values
    )

    state_class = classify_trend(
        state_slope,
        state_p,
    )

    # --------------------------------------------------------
    # CELL TRENDS
    # --------------------------------------------------------

    cell_trends = build_cell_trends(df)

    # --------------------------------------------------------
    # STATE OUTPUT
    # --------------------------------------------------------

    state_output = pd.DataFrame(
        [
            {
                "start_date": str(
                    state["date"].min().date()
                ),
                "end_date": str(
                    state["date"].max().date()
                ),
                "observations": int(
                    len(state)
                ),
                "mean_soil_moisture": float(
                    state_values.mean()
                ),
                "sen_slope_per_month": float(
                    state_slope
                ),
                "sen_slope_per_year": float(
                    state_slope * 12
                ),
                "kendall_tau": float(
                    state_tau
                ),
                "p_value": float(
                    state_p
                ),
                "significant_at_0_05": bool(
                    state_p < ALPHA
                ),
                "trend_class": state_class,
            }
        ]
    )

    # --------------------------------------------------------
    # CELL SUMMARY
    # --------------------------------------------------------

    significant = cell_trends[
        cell_trends[
            "significant_at_0_05"
        ]
    ]

    increasing = cell_trends[
        cell_trends[
            "trend_class"
        ].str.contains(
            "increasing"
        )
    ]

    decreasing = cell_trends[
        cell_trends[
            "trend_class"
        ].str.contains(
            "decreasing"
        )
    ]

    significant_increasing = cell_trends[
        cell_trends["trend_class"]
        == "significant increasing"
    ]

    significant_decreasing = cell_trends[
        cell_trends["trend_class"]
        == "significant decreasing"
    ]

    # --------------------------------------------------------
    # ATOMIC OUTPUT
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_state = STATE_OUTPUT.with_suffix(
        ".tmp.csv"
    )

    temp_cells = CELL_OUTPUT.with_suffix(
        ".tmp.csv"
    )

    state_output.to_csv(
        temp_state,
        index=False,
        float_format="%.10f",
    )

    cell_trends.to_csv(
        temp_cells,
        index=False,
        float_format="%.10f",
    )

    temp_state.replace(STATE_OUTPUT)
    temp_cells.replace(CELL_OUTPUT)

    # --------------------------------------------------------
    # RELOAD VALIDATION
    # --------------------------------------------------------

    state_check = pd.read_csv(
        STATE_OUTPUT
    )

    cells_check = pd.read_csv(
        CELL_OUTPUT
    )

    if len(state_check) != 1:
        fail(
            "State trend output must contain exactly "
            "one summary record"
        )

    if len(cells_check) != EXPECTED_CELLS:
        fail(
            f"Reloaded cell trends: "
            f"{len(cells_check):,}"
        )

    if cells_check[
        [
            "sen_slope_per_month",
            "sen_slope_per_year",
            "kendall_tau",
            "p_value",
        ]
    ].isna().any().any():
        fail(
            "NaN trend statistics found"
        )

    if not np.isfinite(
        cells_check[
            [
                "sen_slope_per_month",
                "sen_slope_per_year",
                "kendall_tau",
                "p_value",
            ]
        ].to_numpy()
    ).all():
        fail(
            "Non-finite trend statistics found"
        )

    # --------------------------------------------------------
    # MANIFEST
    # --------------------------------------------------------

    manifest = {
        "status": "PASS",
        "input": str(
            INPUT.relative_to(ROOT)
        ),
        "state_output": str(
            STATE_OUTPUT.relative_to(ROOT)
        ),
        "cell_output": str(
            CELL_OUTPUT.relative_to(ROOT)
        ),
        "source_period": {
            "start": str(
                df["date"].min().date()
            ),
            "end": str(
                df["date"].max().date()
            ),
        },
        "months": int(
            df["date"]
            .dt.to_period("M")
            .nunique()
        ),
        "spatial_cells": int(
            df[
                ["row", "col"]
            ]
            .drop_duplicates()
            .shape[0]
        ),
        "records": int(len(df)),
        "method": {
            "trend_magnitude": (
                "Sen's slope"
            ),
            "trend_significance": (
                "Mann-Kendall using Kendall tau"
            ),
            "alpha": ALPHA,
            "time_unit": "monthly",
            "annualized_slope": (
                "monthly Sen slope × 12"
            ),
        },
        "state_trend": {
            "sen_slope_per_month": float(
                state_slope
            ),
            "sen_slope_per_year": float(
                state_slope * 12
            ),
            "kendall_tau": float(
                state_tau
            ),
            "p_value": float(
                state_p
            ),
            "significant_at_0_05": bool(
                state_p < ALPHA
            ),
            "trend_class": state_class,
        },
        "cell_summary": {
            "total_cells": int(
                len(cell_trends)
            ),
            "significant_cells": int(
                len(significant)
            ),
            "significant_fraction": float(
                len(significant)
                / len(cell_trends)
            ),
            "increasing_cells": int(
                len(increasing)
            ),
            "decreasing_cells": int(
                len(decreasing)
            ),
            "significant_increasing_cells": int(
                len(significant_increasing)
            ),
            "significant_decreasing_cells": int(
                len(significant_decreasing)
            ),
        },
        "sen_slope_per_year_range": {
            "min": float(
                cell_trends[
                    "sen_slope_per_year"
                ].min()
            ),
            "max": float(
                cell_trends[
                    "sen_slope_per_year"
                ].max()
            ),
        },
    }

    with MANIFEST.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            manifest,
            f,
            indent=2,
        )

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TREND DETECTION COMPLETE")
    print("=" * 70)

    print("\nSTATE-WIDE TREND")
    print("-" * 70)

    print(
        f"Period:             "
        f"{state['date'].min().date()} → "
        f"{state['date'].max().date()}"
    )

    print(
        f"Sen slope/month:    "
        f"{state_slope:.10f}"
    )

    print(
        f"Sen slope/year:     "
        f"{state_slope * 12:.10f}"
    )

    print(
        f"Kendall tau:        "
        f"{state_tau:.6f}"
    )

    print(
        f"p-value:            "
        f"{state_p:.8f}"
    )

    print(
        f"Significant α=.05:  "
        f"{'YES' if state_p < ALPHA else 'NO'}"
    )

    print(
        f"Trend:              "
        f"{state_class}"
    )

    print("\nCELL-LEVEL SUMMARY")
    print("-" * 70)

    print(
        f"Total cells:                 "
        f"{len(cell_trends):,}"
    )

    print(
        f"Significant cells:           "
        f"{len(significant):,}"
    )

    print(
        f"Significant fraction:        "
        f"{len(significant) / len(cell_trends):.3%}"
    )

    print(
        f"All increasing cells:        "
        f"{len(increasing):,}"
    )

    print(
        f"All decreasing cells:        "
        f"{len(decreasing):,}"
    )

    print(
        f"Significant increasing:      "
        f"{len(significant_increasing):,}"
    )

    print(
        f"Significant decreasing:      "
        f"{len(significant_decreasing):,}"
    )

    print("\nOutputs:")

    print(
        f"State trend:\n{STATE_OUTPUT}"
    )

    print(
        f"\nCell trends:\n{CELL_OUTPUT}"
    )

    print(
        f"\nManifest:\n{MANIFEST}"
    )

    print("\nPASS: Trend analysis dataset is ready.")

    print("=" * 70)


if __name__ == "__main__":
    main()
