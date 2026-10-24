from pathlib import Path
import json
import math
import pandas as pd
import numpy as np


# ============================================================
# MODULE 14 — EXTREME EVENT DETECTION
# ============================================================

BASE = Path(__file__).resolve().parents[1]

INPUT = BASE / "data" / "analysis" / "smap_anomalies_jharkhand.csv"

OUT_CELL = BASE / "data" / "analysis" / "smap_extreme_cell_months.csv"
OUT_MONTH = BASE / "data" / "analysis" / "smap_extreme_monthly_summary.csv"
OUT_EVENTS = BASE / "data" / "analysis" / "smap_extreme_events.csv"
OUT_MANIFEST = BASE / "data" / "analysis" / "smap_extreme_event_manifest.json"

EXPECTED_CELLS = 984
EXPECTED_MONTHS = 138
EXPECTED_RECORDS = EXPECTED_CELLS * EXPECTED_MONTHS

DRY_THRESHOLD = -2.0
WET_THRESHOLD = 2.0

# State-wide event threshold:
# at least 5% of Jharkhand cells must be extreme
MIN_EVENT_FRACTION = 0.05
MIN_EVENT_CELLS = math.ceil(EXPECTED_CELLS * MIN_EVENT_FRACTION)


# ============================================================
# HELPERS
# ============================================================

def fail(message):
    raise RuntimeError(message)


def atomic_write_csv(df, path):
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False)
    tmp.replace(path)


def atomic_write_json(payload, path):
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)

    tmp.replace(path)


def require_columns(df, columns, label):
    missing = [c for c in columns if c not in df.columns]

    if missing:
        fail(
            f"{label}: missing required columns: {missing}\n"
            f"Available columns: {list(df.columns)}"
        )


def consecutive_month(a, b):
    """
    True when b is exactly one calendar month after a.
    """
    return b == a + pd.offsets.MonthBegin(1)


# ============================================================
# 1. LOAD
# ============================================================

print("=" * 70)
print("MODULE 14 — EXTREME EVENT DETECTION")
print("=" * 70)

print("\n[1/10] Loading anomaly dataset...")

if not INPUT.exists():
    fail(f"Input file not found: {INPUT}")

df = pd.read_csv(INPUT)

print(f"Loaded records: {len(df):,}")
print(f"Columns: {len(df.columns)}")


# ============================================================
# 2. SCHEMA
# ============================================================

print("\n[2/10] Validating schema...")

required = [
    "date",
    "year",
    "month_number",
    "row",
    "col",
    "latitude",
    "longitude",
    "soil_moisture",
    "season",
    "climatology_mean",
    "climatology_std",
    "anomaly",
    "standardized_anomaly",
]

require_columns(df, required, "Anomaly dataset")

print("Schema validation: PASS")


# ============================================================
# 3. TYPE / BASIC VALIDATION
# ============================================================

print("\n[3/10] Validating dataset integrity...")

df["date"] = pd.to_datetime(df["date"], errors="coerce")

numeric_cols = [
    "year",
    "month_number",
    "row",
    "col",
    "latitude",
    "longitude",
    "soil_moisture",
    "climatology_mean",
    "climatology_std",
    "anomaly",
    "standardized_anomaly",
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

if df["date"].isna().any():
    fail("Invalid dates detected.")

if df[numeric_cols].isna().any().any():
    bad = df[numeric_cols].isna().sum()
    bad = bad[bad > 0]
    fail(f"Missing/non-numeric values detected:\n{bad}")

if len(df) != EXPECTED_RECORDS:
    fail(
        f"Expected {EXPECTED_RECORDS:,} records, "
        f"found {len(df):,}"
    )

unique_cells = df[["row", "col"]].drop_duplicates()

if len(unique_cells) != EXPECTED_CELLS:
    fail(
        f"Expected {EXPECTED_CELLS} spatial cells, "
        f"found {len(unique_cells)}"
    )

unique_months = sorted(df["date"].dt.to_period("M").unique())

if len(unique_months) != EXPECTED_MONTHS:
    fail(
        f"Expected {EXPECTED_MONTHS} months, "
        f"found {len(unique_months)}"
    )

duplicate_count = df.duplicated(
    subset=["date", "row", "col"]
).sum()

if duplicate_count:
    fail(f"Duplicate cell-month records: {duplicate_count}")

print("Record count validation: PASS")
print("Spatial cell validation: PASS")
print("Monthly coverage validation: PASS")
print("Duplicate validation: PASS")


# ============================================================
# 4. CLASSIFY EXTREMES
# ============================================================

print("\n[4/10] Classifying extreme dry/wet observations...")

df["extreme_direction"] = "none"

df.loc[
    df["standardized_anomaly"] <= DRY_THRESHOLD,
    "extreme_direction"
] = "dry"

df.loc[
    df["standardized_anomaly"] >= WET_THRESHOLD,
    "extreme_direction"
] = "wet"

df["is_extreme"] = df["extreme_direction"] != "none"

df["absolute_z"] = df["standardized_anomaly"].abs()

print(
    f"Extreme dry cell-months: "
    f"{(df['extreme_direction'] == 'dry').sum():,}"
)

print(
    f"Extreme wet cell-months: "
    f"{(df['extreme_direction'] == 'wet').sum():,}"
)

print(
    f"All extreme cell-months: "
    f"{df['is_extreme'].sum():,}"
)


# ============================================================
# 5. CELL-MONTH EXTREMES
# ============================================================

print("\n[5/10] Building extreme cell-month dataset...")

extreme = df[df["is_extreme"]].copy()

extreme = extreme[
    [
        "date",
        "year",
        "month_number",
        "row",
        "col",
        "latitude",
        "longitude",
        "soil_moisture",
        "season",
        "climatology_mean",
        "climatology_std",
        "anomaly",
        "standardized_anomaly",
        "absolute_z",
        "extreme_direction",
    ]
].sort_values(
    ["date", "extreme_direction", "standardized_anomaly"]
)

if len(extreme):
    duplicate_extreme = extreme.duplicated(
        subset=["date", "row", "col"]
    ).sum()

    if duplicate_extreme:
        fail(
            f"Duplicate extreme cell-month records: "
            f"{duplicate_extreme}"
        )

atomic_write_csv(extreme, OUT_CELL)

print(f"Extreme cell-month rows: {len(extreme):,}")
print(f"Written: {OUT_CELL}")


# ============================================================
# 6. MONTHLY EXTREME SUMMARY
# ============================================================

print("\n[6/10] Building monthly extreme summary...")

monthly_rows = []

for date, group in df.groupby("date", sort=True):

    dry = group[
        group["standardized_anomaly"] <= DRY_THRESHOLD
    ]

    wet = group[
        group["standardized_anomaly"] >= WET_THRESHOLD
    ]

    dry_count = len(dry)
    wet_count = len(wet)

    dry_fraction = dry_count / EXPECTED_CELLS
    wet_fraction = wet_count / EXPECTED_CELLS

    # State-wide monthly mean
    state_mean = group["soil_moisture"].mean()

    state_clim = group["climatology_mean"].mean()

    state_anomaly = state_mean - state_clim

    # Dry statistics
    if dry_count:
        dry_mean_z = dry["standardized_anomaly"].mean()
        dry_min_z = dry["standardized_anomaly"].min()
        dry_mean_abs_z = dry["absolute_z"].mean()
        dry_centroid_lat = dry["latitude"].mean()
        dry_centroid_lon = dry["longitude"].mean()
    else:
        dry_mean_z = np.nan
        dry_min_z = np.nan
        dry_mean_abs_z = np.nan
        dry_centroid_lat = np.nan
        dry_centroid_lon = np.nan

    # Wet statistics
    if wet_count:
        wet_mean_z = wet["standardized_anomaly"].mean()
        wet_max_z = wet["standardized_anomaly"].max()
        wet_mean_abs_z = wet["absolute_z"].mean()
        wet_centroid_lat = wet["latitude"].mean()
        wet_centroid_lon = wet["longitude"].mean()
    else:
        wet_mean_z = np.nan
        wet_max_z = np.nan
        wet_mean_abs_z = np.nan
        wet_centroid_lat = np.nan
        wet_centroid_lon = np.nan

    # Severity = spatial extent × average absolute standardized anomaly
    dry_severity = (
        dry_fraction * dry_mean_abs_z
        if dry_count
        else 0.0
    )

    wet_severity = (
        wet_fraction * wet_mean_abs_z
        if wet_count
        else 0.0
    )

    # State-level event candidate
    if dry_count >= MIN_EVENT_CELLS and dry_count > wet_count:
        event_direction = "dry"
    elif wet_count >= MIN_EVENT_CELLS and wet_count > dry_count:
        event_direction = "wet"
    elif dry_count >= MIN_EVENT_CELLS and wet_count >= MIN_EVENT_CELLS:
        event_direction = (
            "mixed"
            if dry_count == wet_count
            else (
                "dry"
                if dry_count > wet_count
                else "wet"
            )
        )
    else:
        event_direction = "none"

    monthly_rows.append(
        {
            "date": date,
            "year": date.year,
            "month_number": date.month,
            "state_mean_soil_moisture": state_mean,
            "state_climatology_mean": state_clim,
            "state_anomaly": state_anomaly,

            "dry_extreme_cells": dry_count,
            "dry_extreme_fraction": dry_fraction,
            "dry_mean_z": dry_mean_z,
            "dry_min_z": dry_min_z,
            "dry_mean_absolute_z": dry_mean_abs_z,
            "dry_severity": dry_severity,
            "dry_centroid_latitude": dry_centroid_lat,
            "dry_centroid_longitude": dry_centroid_lon,

            "wet_extreme_cells": wet_count,
            "wet_extreme_fraction": wet_fraction,
            "wet_mean_z": wet_mean_z,
            "wet_max_z": wet_max_z,
            "wet_mean_absolute_z": wet_mean_abs_z,
            "wet_severity": wet_severity,
            "wet_centroid_latitude": wet_centroid_lat,
            "wet_centroid_longitude": wet_centroid_lon,

            "event_direction": event_direction,
            "event_candidate": event_direction != "none",
        }
    )

monthly = pd.DataFrame(monthly_rows)

if len(monthly) != EXPECTED_MONTHS:
    fail(
        f"Expected {EXPECTED_MONTHS} monthly summaries, "
        f"found {len(monthly)}"
    )

if monthly["date"].duplicated().any():
    fail("Duplicate monthly summary dates detected.")

atomic_write_csv(monthly, OUT_MONTH)

print(f"Monthly summaries: {len(monthly)}")
print(f"Event candidate months: {monthly['event_candidate'].sum()}")
print(f"Written: {OUT_MONTH}")


# ============================================================
# 7. BUILD STATE EVENT EPISODES
# ============================================================

print("\n[7/10] Building consecutive extreme event episodes...")

candidate = monthly[
    monthly["event_candidate"]
].copy()

candidate = candidate.sort_values("date").reset_index(drop=True)

episodes = []

current = None

for _, row in candidate.iterrows():

    direction = row["event_direction"]
    date = row["date"]

    if current is None:
        current = {
            "direction": direction,
            "start_date": date,
            "end_date": date,
            "months": [row],
        }
        continue

    previous_date = current["end_date"]

    if (
        direction == current["direction"]
        and consecutive_month(previous_date, date)
    ):
        current["end_date"] = date
        current["months"].append(row)

    else:
        episodes.append(current)

        current = {
            "direction": direction,
            "start_date": date,
            "end_date": date,
            "months": [row],
        }

if current is not None:
    episodes.append(current)


# ============================================================
# 8. SUMMARIZE EPISODES
# ============================================================

print("\n[8/10] Ranking event episodes...")

event_rows = []

for event_id, episode in enumerate(
    episodes,
    start=1
):

    rows = pd.DataFrame(episode["months"])

    direction = episode["direction"]

    if direction == "dry":

        extent = rows["dry_extreme_fraction"]

        severity = rows["dry_severity"]

        # Dry events do not have a wet-side maximum z.
        # Initialize explicitly so the output schema is stable.
        max_z = np.nan

        peak_idx = rows["dry_extreme_cells"].idxmax()

        peak_row = rows.loc[peak_idx]

        peak_cells = int(peak_row["dry_extreme_cells"])
        peak_fraction = float(
            peak_row["dry_extreme_fraction"]
        )
        peak_date = peak_row["date"]

        min_z = float(rows["dry_min_z"].min())
        mean_z = float(rows["dry_mean_z"].mean())

        cumulative_severity = float(
            rows["dry_severity"].sum()
        )

        max_severity = float(
            rows["dry_severity"].max()
        )

    elif direction == "wet":

        extent = rows["wet_extreme_fraction"]

        severity = rows["wet_severity"]

        # Wet events do not have a dry-side minimum z.
        # Initialize explicitly so the output schema is stable.
        min_z = np.nan

        peak_idx = rows["wet_extreme_cells"].idxmax()

        peak_row = rows.loc[peak_idx]

        peak_cells = int(peak_row["wet_extreme_cells"])
        peak_fraction = float(
            peak_row["wet_extreme_fraction"]
        )
        peak_date = peak_row["date"]

        max_z = float(rows["wet_max_z"].max())
        mean_z = float(rows["wet_mean_z"].mean())

        cumulative_severity = float(
            rows["wet_severity"].sum()
        )

        max_severity = float(
            rows["wet_severity"].max()
        )

        min_z = np.nan

    else:
        # Mixed episodes are retained, but severity is based
        # on the stronger directional component.
        dry_total = rows["dry_severity"].sum()
        wet_total = rows["wet_severity"].sum()

        if dry_total >= wet_total:
            peak_idx = rows["dry_extreme_cells"].idxmax()
            peak_row = rows.loc[peak_idx]

            peak_cells = int(
                peak_row["dry_extreme_cells"]
            )

            peak_fraction = float(
                peak_row["dry_extreme_fraction"]
            )

            peak_date = peak_row["date"]

            min_z = float(rows["dry_min_z"].min())
            max_z = np.nan
            mean_z = float(rows["dry_mean_z"].mean())

        else:
            peak_idx = rows["wet_extreme_cells"].idxmax()
            peak_row = rows.loc[peak_idx]

            peak_cells = int(
                peak_row["wet_extreme_cells"]
            )

            peak_fraction = float(
                peak_row["wet_extreme_fraction"]
            )

            peak_date = peak_row["date"]

            min_z = np.nan
            max_z = float(rows["wet_max_z"].max())
            mean_z = float(rows["wet_mean_z"].mean())

        cumulative_severity = float(
            max(dry_total, wet_total)
        )

        max_severity = float(
            max(
                rows["dry_severity"].max(),
                rows["wet_severity"].max(),
            )
        )

    event_rows.append(
        {
            "event_id": event_id,
            "direction": direction,
            "start_date": episode["start_date"],
            "end_date": episode["end_date"],
            "duration_months": len(rows),

            "peak_date": peak_date,
            "peak_extreme_cells": peak_cells,
            "peak_extreme_fraction": peak_fraction,

            "mean_standardized_anomaly": mean_z,
            "minimum_z": min_z,
            "maximum_z": max_z,

            "cumulative_severity": cumulative_severity,
            "peak_month_severity": max_severity,
        }
    )


events = pd.DataFrame(event_rows)

if len(events):
    events = events.sort_values(
        [
            "cumulative_severity",
            "peak_extreme_fraction",
        ],
        ascending=False,
    ).reset_index(drop=True)

    events["rank"] = np.arange(1, len(events) + 1)

else:
    events = pd.DataFrame(
        columns=[
            "event_id",
            "direction",
            "start_date",
            "end_date",
            "duration_months",
            "peak_date",
            "peak_extreme_cells",
            "peak_extreme_fraction",
            "mean_standardized_anomaly",
            "minimum_z",
            "maximum_z",
            "cumulative_severity",
            "peak_month_severity",
            "rank",
        ]
    )

atomic_write_csv(events, OUT_EVENTS)

print(f"Event episodes: {len(events)}")
print(f"Written: {OUT_EVENTS}")


# ============================================================
# 9. CELL-LEVEL REPEAT EXTREMES
# ============================================================

print("\n[9/10] Calculating repeated extreme cells...")

if len(extreme):

    repeat_cells = (
        extreme
        .groupby(
            ["row", "col", "latitude", "longitude"],
            as_index=False
        )
        .agg(
            extreme_months=(
                "date",
                "nunique"
            ),
            dry_extreme_months=(
                "extreme_direction",
                lambda x: int((x == "dry").sum())
            ),
            wet_extreme_months=(
                "extreme_direction",
                lambda x: int((x == "wet").sum())
            ),
            mean_z=(
                "standardized_anomaly",
                "mean"
            ),
            minimum_z=(
                "standardized_anomaly",
                "min"
            ),
            maximum_z=(
                "standardized_anomaly",
                "max"
            ),
        )
        .sort_values(
            "extreme_months",
            ascending=False
        )
    )

else:

    repeat_cells = pd.DataFrame(
        columns=[
            "row",
            "col",
            "latitude",
            "longitude",
            "extreme_months",
            "dry_extreme_months",
            "wet_extreme_months",
            "mean_z",
            "minimum_z",
            "maximum_z",
        ]
    )

# Add repeated-cell information into manifest,
# rather than creating another mandatory output file.

top_repeat_cells = repeat_cells.head(20)


# ============================================================
# 10. MANIFEST + FINAL REPORT
# ============================================================

print("\n[10/10] Writing manifest and final report...")

dry_total = int(
    (df["standardized_anomaly"] <= DRY_THRESHOLD).sum()
)

wet_total = int(
    (df["standardized_anomaly"] >= WET_THRESHOLD).sum()
)

candidate_dry_months = int(
    (
        monthly["dry_extreme_cells"]
        >= MIN_EVENT_CELLS
    ).sum()
)

candidate_wet_months = int(
    (
        monthly["wet_extreme_cells"]
        >= MIN_EVENT_CELLS
    ).sum()
)

dry_events = int(
    (events["direction"] == "dry").sum()
)

wet_events = int(
    (events["direction"] == "wet").sum()
)

mixed_events = int(
    (events["direction"] == "mixed").sum()
)

top_dry_months = (
    monthly
    .sort_values(
        "dry_severity",
        ascending=False
    )
    .head(10)
    [
        [
            "date",
            "dry_extreme_cells",
            "dry_extreme_fraction",
            "dry_mean_z",
            "dry_min_z",
            "dry_severity",
        ]
    ]
)

top_wet_months = (
    monthly
    .sort_values(
        "wet_severity",
        ascending=False
    )
    .head(10)
    [
        [
            "date",
            "wet_extreme_cells",
            "wet_extreme_fraction",
            "wet_mean_z",
            "wet_max_z",
            "wet_severity",
        ]
    ]
)

manifest = {
    "module": "14_extreme_events",
    "status": "PASS",

    "input": str(INPUT),

    "outputs": {
        "extreme_cell_months": str(OUT_CELL),
        "monthly_summary": str(OUT_MONTH),
        "event_episodes": str(OUT_EVENTS),
        "manifest": str(OUT_MANIFEST),
    },

    "dataset": {
        "months": EXPECTED_MONTHS,
        "cells": EXPECTED_CELLS,
        "records": EXPECTED_RECORDS,
        "start": str(df["date"].min()),
        "end": str(df["date"].max()),
    },

    "method": {
        "extreme_dry_threshold_z": DRY_THRESHOLD,
        "extreme_wet_threshold_z": WET_THRESHOLD,
        "minimum_event_fraction": MIN_EVENT_FRACTION,
        "minimum_event_cells": MIN_EVENT_CELLS,
        "event_definition": (
            "Consecutive calendar months with at least "
            "5 percent of spatial cells extreme in the "
            "same dominant direction."
        ),
        "severity_definition": (
            "Extreme spatial fraction multiplied by "
            "mean absolute standardized anomaly among "
            "affected cells."
        ),
    },

    "results": {
        "extreme_dry_cell_months": dry_total,
        "extreme_wet_cell_months": wet_total,
        "total_extreme_cell_months": int(
            dry_total + wet_total
        ),

        "dry_candidate_months": candidate_dry_months,
        "wet_candidate_months": candidate_wet_months,

        "total_event_episodes": int(len(events)),
        "dry_event_episodes": dry_events,
        "wet_event_episodes": wet_events,
        "mixed_event_episodes": mixed_events,

        "unique_cells_with_extremes": int(
            repeat_cells.shape[0]
        ),
    },

    "top_repeated_extreme_cells": (
        top_repeat_cells.to_dict("records")
    ),

    "top_dry_months": (
        top_dry_months.to_dict("records")
    ),

    "top_wet_months": (
        top_wet_months.to_dict("records")
    ),

    "scientific_notes": [
        (
            "Extreme events are identified from standardized "
            "soil-moisture anomalies relative to each cell's "
            "calendar-month climatology."
        ),
        (
            "A long-term non-significant trend does not imply "
            "absence of episodic dry or wet extremes."
        ),
        (
            "Event detection describes temporal and spatial "
            "patterns and does not establish causation."
        ),
        (
            "The 5 percent state-event threshold is an "
            "analytical definition, not a physical law."
        ),
        (
            "Cross-variable evidence is required before "
            "attributing extremes to rainfall, temperature, "
            "vegetation, or other drivers."
        ),
    ],
}

atomic_write_json(manifest, OUT_MANIFEST)


# ============================================================
# FINAL CONSOLE SUMMARY
# ============================================================

print("\n")
print("=" * 70)
print("MODULE 14 COMPLETE")
print("=" * 70)

print(f"Dataset records:              {len(df):,}")
print(f"Spatial cells:                {EXPECTED_CELLS:,}")
print(f"Months:                       {EXPECTED_MONTHS:,}")

print(
    f"Extreme dry cell-months:      {dry_total:,}"
)

print(
    f"Extreme wet cell-months:      {wet_total:,}"
)

print(
    f"Total extreme cell-months:    {dry_total + wet_total:,}"
)

print(
    f"Dry event candidate months:   {candidate_dry_months}"
)

print(
    f"Wet event candidate months:   {candidate_wet_months}"
)

print(
    f"Dry event episodes:            {dry_events}"
)

print(
    f"Wet event episodes:            {wet_events}"
)

print(
    f"Mixed event episodes:          {mixed_events}"
)

print(
    f"Cells with >=1 extreme:       {len(repeat_cells):,}"
)

print("\nTOP DRY MONTHS")
print("-" * 70)

if len(top_dry_months):
    print(
        top_dry_months.to_string(
            index=False,
            formatters={
                "dry_extreme_fraction": "{:.3f}".format,
                "dry_mean_z": "{:.3f}".format,
                "dry_min_z": "{:.3f}".format,
                "dry_severity": "{:.4f}".format,
            },
        )
    )

print("\nTOP WET MONTHS")
print("-" * 70)

if len(top_wet_months):
    print(
        top_wet_months.to_string(
            index=False,
            formatters={
                "wet_extreme_fraction": "{:.3f}".format,
                "wet_mean_z": "{:.3f}".format,
                "wet_max_z": "{:.3f}".format,
                "wet_severity": "{:.4f}".format,
            },
        )
    )

print("\nOUTPUTS")
print("-" * 70)
print(OUT_CELL)
print(OUT_MONTH)
print(OUT_EVENTS)
print(OUT_MANIFEST)

print("\nSTATUS: PASS")
