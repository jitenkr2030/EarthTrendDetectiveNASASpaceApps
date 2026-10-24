from pathlib import Path
import json

import numpy as np
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "analysis" / "smap_monthly_jharkhand.csv"
CLIMATOLOGY = ROOT / "data" / "analysis" / "smap_climatology.csv"

OUTPUT_DIR = ROOT / "data" / "analysis"
OUTPUT = OUTPUT_DIR / "smap_anomalies_jharkhand.csv"
MANIFEST = OUTPUT_DIR / "smap_anomalies_manifest.json"

EXPECTED_MONTHS = 138
EXPECTED_CELLS = 984
EXPECTED_RECORDS = EXPECTED_MONTHS * EXPECTED_CELLS


# ============================================================
# HELPERS
# ============================================================

def fail(message):
    raise RuntimeError(f"\nFAIL: {message}\n")


# ============================================================
# LOAD + VALIDATE SOURCE DATA
# ============================================================

def load_source():

    if not INPUT.exists():
        fail(f"Input dataset not found: {INPUT}")

    df = pd.read_csv(INPUT)

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
        fail(f"Missing source columns: {sorted(missing)}")

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
        fail("Missing/non-numeric source values found")

    if len(df) != EXPECTED_RECORDS:
        fail(
            f"Unexpected source record count: {len(df):,} "
            f"(expected {EXPECTED_RECORDS:,})"
        )

    duplicate_count = df.duplicated(
        subset=["date", "row", "col"]
    ).sum()

    if duplicate_count:
        fail(f"Duplicate source records: {duplicate_count}")

    if (
        df["soil_moisture"].lt(0).any()
        or df["soil_moisture"].gt(1).any()
    ):
        fail("Source soil moisture outside [0,1]")

    return df


# ============================================================
# LOAD + VALIDATE CLIMATOLOGY
# ============================================================

def load_climatology():

    if not CLIMATOLOGY.exists():
        fail(f"Climatology file not found: {CLIMATOLOGY}")

    clim = pd.read_csv(CLIMATOLOGY)

    required = {
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
    }

    missing = required - set(clim.columns)

    if missing:
        fail(
            f"Missing climatology columns: {sorted(missing)}"
        )

    numeric_columns = [
        "calendar_month",
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

    for column in numeric_columns:
        clim[column] = pd.to_numeric(
            clim[column],
            errors="coerce",
        )

    if clim[numeric_columns].isna().any().any():
        fail("Missing/non-numeric climatology values")

    expected_rows = EXPECTED_CELLS * 12

    if len(clim) != expected_rows:
        fail(
            f"Unexpected climatology rows: {len(clim):,} "
            f"(expected {expected_rows:,})"
        )

    duplicate_count = clim.duplicated(
        subset=["calendar_month", "row", "col"]
    ).sum()

    if duplicate_count:
        fail(
            f"Duplicate climatology records: "
            f"{duplicate_count}"
        )

    return clim


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 70)
    print("EARTH TREND DETECTIVE — ANOMALY ANALYSIS ENGINE")
    print("=" * 70)

    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    print("\nLoading canonical analysis dataset...")

    df = load_source()

    print(f"Source records: {len(df):,}")
    print("PASS source validation")

    print("\nLoading climatology...")

    clim = load_climatology()

    print(f"Climatology records: {len(clim):,}")
    print("PASS climatology validation")

    # --------------------------------------------------------
    # JOIN KEY
    # --------------------------------------------------------

    df["calendar_month"] = df["date"].dt.month

    join_keys = [
        "calendar_month",
        "row",
        "col",
    ]

    # --------------------------------------------------------
    # KEEP ONLY CLIMATOLOGY FIELDS NEEDED FOR ANOMALY
    # --------------------------------------------------------

    clim_join = clim[
        join_keys
        + [
            "climatology_mean",
            "climatology_std",
        ]
    ].copy()

    # --------------------------------------------------------
    # MERGE
    # --------------------------------------------------------

    print("\nJoining observations with climatology...")

    merged = df.merge(
        clim_join,
        on=join_keys,
        how="left",
        validate="many_to_one",
    )

    if len(merged) != len(df):
        fail(
            "Merge changed source record count: "
            f"{len(df):,} -> {len(merged):,}"
        )

    if merged["climatology_mean"].isna().any():
        missing_count = int(
            merged["climatology_mean"].isna().sum()
        )
        fail(
            f"Missing climatology after join: "
            f"{missing_count}"
        )

    print("PASS climatology join")

    # --------------------------------------------------------
    # ABSOLUTE ANOMALY
    #
    # anomaly = observation - climatological mean
    # --------------------------------------------------------

    merged["anomaly"] = (
        merged["soil_moisture"]
        - merged["climatology_mean"]
    )

    # --------------------------------------------------------
    # STANDARDIZED ANOMALY
    #
    # z = (observation - mean) / std
    #
    # If climatology std == 0, z-score is undefined.
    # Keep it as NaN rather than inventing a value.
    # --------------------------------------------------------

    zero_std = merged["climatology_std"].eq(0)

    merged["standardized_anomaly"] = np.nan

    valid_std = ~zero_std

    merged.loc[
        valid_std,
        "standardized_anomaly",
    ] = (
        merged.loc[valid_std, "anomaly"]
        / merged.loc[valid_std, "climatology_std"]
    )

    zero_std_count = int(zero_std.sum())

    print(
        f"\nZero-standard-deviation records: "
        f"{zero_std_count:,}"
    )

    # --------------------------------------------------------
    # ANOMALY CLASSIFICATION
    #
    # Thresholds based on standardized anomaly:
    #
    # <= -2       extremely dry
    # -2 to -1.5  very dry
    # -1.5 to -1  dry
    # -1 to +1    near normal
    # +1 to +1.5  wet
    # +1.5 to +2  very wet
    # >= +2       extremely wet
    #
    # These are labels for anomaly magnitude, not drought
    # declarations.
    # --------------------------------------------------------

    def classify(z):

        if pd.isna(z):
            return "undefined"

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

    merged["anomaly_class"] = (
        merged["standardized_anomaly"]
        .apply(classify)
    )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    print("\nValidating anomaly calculations...")

    if merged["anomaly"].isna().any():
        fail("NaN absolute anomalies found")

    finite_z = merged["standardized_anomaly"].dropna()

    if not np.isfinite(finite_z).all():
        fail("Infinite standardized anomalies found")

    # Basic mathematical consistency
    calculated = (
        merged["soil_moisture"]
        - merged["climatology_mean"]
    )

    if not np.allclose(
        merged["anomaly"].to_numpy(),
        calculated.to_numpy(),
        rtol=1e-10,
        atol=1e-12,
    ):
        fail("Absolute anomaly calculation mismatch")

    print("PASS anomaly arithmetic")

    # --------------------------------------------------------
    # SPATIAL / TEMPORAL COVERAGE
    # --------------------------------------------------------

    month_count = (
        merged["date"]
        .dt.to_period("M")
        .nunique()
    )

    cell_count = (
        merged[["row", "col"]]
        .drop_duplicates()
        .shape[0]
    )

    if month_count != EXPECTED_MONTHS:
        fail(
            f"Unexpected anomaly months: {month_count}"
        )

    if cell_count != EXPECTED_CELLS:
        fail(
            f"Unexpected anomaly cells: {cell_count}"
        )

    # --------------------------------------------------------
    # OUTPUT COLUMNS
    # --------------------------------------------------------

    output_columns = [
        "date",
        "year",
        "month_number",
        "calendar_month",
        "row",
        "col",
        "latitude",
        "longitude",
        "soil_moisture",
        "climatology_mean",
        "climatology_std",
        "anomaly",
        "standardized_anomaly",
        "anomaly_class",
        "season",
        "observations",
        "expected_observations",
        "coverage_fraction",
    ]

    result = merged[output_columns].copy()

    result = result.sort_values(
        [
            "date",
            "row",
            "col",
        ]
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # FINAL DUPLICATE CHECK
    # --------------------------------------------------------

    duplicate_output = result.duplicated(
        subset=["date", "row", "col"]
    ).sum()

    if duplicate_output:
        fail(
            f"Duplicate anomaly records: "
            f"{duplicate_output}"
        )

    # --------------------------------------------------------
    # ATOMIC WRITE
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_output = OUTPUT.with_suffix(".tmp.csv")

    result.to_csv(
        temp_output,
        index=False,
        float_format="%.10f",
    )

    temp_output.replace(OUTPUT)

    # --------------------------------------------------------
    # RELOAD VALIDATION
    # --------------------------------------------------------

    check = pd.read_csv(OUTPUT)

    if len(check) != EXPECTED_RECORDS:
        fail(
            f"Reloaded anomaly record count mismatch: "
            f"{len(check):,}"
        )

    if set(output_columns) - set(check.columns):
        fail("Reloaded anomaly schema mismatch")

    if check.duplicated(
        subset=["date", "row", "col"]
    ).any():
        fail("Duplicate records after reload")

    # --------------------------------------------------------
    # STATE-WIDE MONTHLY ANOMALY SUMMARY
    # --------------------------------------------------------

    monthly_summary = (
        result.groupby(
            [
                "year",
                "month_number",
                "date",
            ],
            as_index=False,
        )
        .agg(
            mean_soil_moisture=(
                "soil_moisture",
                "mean",
            ),
            mean_climatology=(
                "climatology_mean",
                "mean",
            ),
            mean_anomaly=(
                "anomaly",
                "mean",
            ),
            mean_standardized_anomaly=(
                "standardized_anomaly",
                "mean",
            ),
            min_anomaly=(
                "anomaly",
                "min",
            ),
            max_anomaly=(
                "anomaly",
                "max",
            ),
        )
        .sort_values("date")
    )

    # --------------------------------------------------------
    # MONTHLY EXTREME COUNTS
    # --------------------------------------------------------

    class_counts = (
        result.groupby(
            ["date", "anomaly_class"]
        )
        .size()
        .unstack(fill_value=0)
        .reset_index()
        .sort_values("date")
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("ANOMALY SUMMARY")
    print("-" * 70)

    print(
        f"\nAbsolute anomaly range: "
        f"{result['anomaly'].min():.6f} "
        f"to "
        f"{result['anomaly'].max():.6f}"
    )

    if len(finite_z):
        print(
            f"Standardized anomaly range: "
            f"{finite_z.min():.3f} "
            f"to "
            f"{finite_z.max():.3f}"
        )

    print(
        f"\nMean absolute anomaly: "
        f"{result['anomaly'].mean():.6f}"
    )

    print("\nAnomaly class counts:")

    print(
        result["anomaly_class"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    # --------------------------------------------------------
    # MOST EXTREME STATE-WIDE MONTHS
    # --------------------------------------------------------

    extreme_months = (
        monthly_summary[
            [
                "date",
                "mean_anomaly",
                "mean_standardized_anomaly",
            ]
        ]
        .copy()
    )

    extreme_months["abs_mean_anomaly"] = (
        extreme_months["mean_anomaly"].abs()
    )

    extreme_months = (
        extreme_months
        .sort_values(
            "abs_mean_anomaly",
            ascending=False,
        )
        .head(10)
    )

    print("\nTop 10 state-wide anomaly months:")

    print(
        extreme_months[
            [
                "date",
                "mean_anomaly",
                "mean_standardized_anomaly",
            ]
        ].to_string(index=False)
    )

    # --------------------------------------------------------
    # MANIFEST
    # --------------------------------------------------------

    manifest = {
        "status": "PASS",
        "input": str(INPUT.relative_to(ROOT)),
        "climatology_input": str(
            CLIMATOLOGY.relative_to(ROOT)
        ),
        "output": str(OUTPUT.relative_to(ROOT)),
        "source_period": {
            "start": str(
                result["date"].min()
                .date()
            ),
            "end": str(
                result["date"].max()
                .date()
            ),
        },
        "months": int(month_count),
        "spatial_cells": int(cell_count),
        "records": int(len(result)),
        "expected_records": EXPECTED_RECORDS,
        "anomaly_definition": (
            "observed soil moisture minus spatial "
            "cell/calendar-month climatological mean"
        ),
        "standardized_anomaly_definition": (
            "(observed soil moisture - climatological mean) "
            "/ climatological standard deviation"
        ),
        "zero_std_records": zero_std_count,
        "absolute_anomaly_range": {
            "min": float(result["anomaly"].min()),
            "max": float(result["anomaly"].max()),
        },
        "standardized_anomaly_range": {
            "min": (
                float(finite_z.min())
                if len(finite_z)
                else None
            ),
            "max": (
                float(finite_z.max())
                if len(finite_z)
                else None
            ),
        },
        "mean_absolute_anomaly": float(
            result["anomaly"].mean()
        ),
        "anomaly_class_counts": {
            str(k): int(v)
            for k, v in result[
                "anomaly_class"
            ].value_counts().items()
        },
        "top_10_statewide_anomaly_months": (
            extreme_months[
                [
                    "date",
                    "mean_anomaly",
                    "mean_standardized_anomaly",
                ]
            ]
            .assign(
                date=lambda x: x["date"].astype(str)
            )
            .to_dict(orient="records")
        ),
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
    # FINAL
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("ANOMALY ANALYSIS COMPLETE")
    print("=" * 70)

    print(
        f"\nRecords:            {len(result):,}"
    )
    print(
        f"Spatial cells:      {cell_count:,}"
    )
    print(
        f"Months:             {month_count}"
    )
    print(
        f"Zero-std records:   {zero_std_count:,}"
    )

    print("\nOutput:")
    print(OUTPUT)

    print("\nManifest:")
    print(MANIFEST)

    print(
        "\nPASS: Anomaly dataset is ready for "
        "extreme-event and trend analysis."
    )

    print("=" * 70)


if __name__ == "__main__":
    main()
