from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


BASE = Path("/root/earthtrend-detective")

INPUT = (
    BASE
    / "data"
    / "analysis"
    / "smap_extreme_monthly_summary.csv"
)

OUT = (
    BASE
    / "data"
    / "analysis"
    / "figures"
    / "earthtrend_extreme_events.png"
)


print("\n" + "=" * 70)
print("EARTH TREND DETECTIVE — EXTREME EVENT EVIDENCE")
print("=" * 70)


# ============================================================
# LOAD
# ============================================================

df = pd.read_csv(INPUT)

df["date"] = pd.to_datetime(df["date"])

print(f"\nRows loaded : {len(df)}")
print(
    f"Date range  : "
    f"{df['date'].min().date()} -> "
    f"{df['date'].max().date()}"
)


# ============================================================
# VALIDATION
# ============================================================

required = [
    "date",
    "dry_extreme_cells",
    "wet_extreme_cells",
    "dry_extreme_fraction",
    "wet_extreme_fraction",
    "dry_mean_z",
    "wet_mean_z",
    "event_direction",
    "event_candidate",
]

missing = [c for c in required if c not in df.columns]

if missing:
    raise ValueError(
        f"Missing required columns: {missing}"
    )

assert len(df) == 138
assert df["date"].is_monotonic_increasing


# ============================================================
# EVENT SUMMARY
# ============================================================

dry_candidate = df[
    (df["event_candidate"] == True)
    & (df["event_direction"] == "dry")
]

wet_candidate = df[
    (df["event_candidate"] == True)
    & (df["event_direction"] == "wet")
]

print("\nExtreme-event summary")
print("-" * 70)

print(
    f"Months with dry extremes : "
    f"{(df['dry_extreme_cells'] > 0).sum()}"
)

print(
    f"Months with wet extremes : "
    f"{(df['wet_extreme_cells'] > 0).sum()}"
)

print(
    f"Dry event-candidate months: "
    f"{len(dry_candidate)}"
)

print(
    f"Wet event-candidate months: "
    f"{len(wet_candidate)}"
)

print(
    f"Maximum dry affected cells: "
    f"{int(df['dry_extreme_cells'].max())}"
)

print(
    f"Maximum wet affected cells: "
    f"{int(df['wet_extreme_cells'].max())}"
)


# ============================================================
# FIGURE
# ============================================================

fig, ax = plt.subplots(
    figsize=(14, 7)
)


# ============================================================
# DRY EXTREMES
# ============================================================

ax.plot(
    df["date"],
    df["dry_extreme_cells"],
    linewidth=1.8,
    label="Extreme-dry cells",
)


# ============================================================
# WET EXTREMES
# ============================================================

ax.plot(
    df["date"],
    df["wet_extreme_cells"],
    linewidth=1.8,
    label="Extreme-wet cells",
)


# ============================================================
# EVENT THRESHOLD
# ============================================================

# Event definition:
# >= 5% of 984 cells
event_threshold = 50

ax.axhline(
    event_threshold,
    linewidth=1.0,
    linestyle="--",
    label="Event threshold (50 cells)",
)


# ============================================================
# AXES
# ============================================================

ax.set_xlabel("Date")
ax.set_ylabel("Number of extreme cells")

ax.set_title(
    "EXTREMES — Widespread soil-moisture departures across Jharkhand",
    fontsize=14,
    pad=12,
)

ax.grid(
    True,
    alpha=0.25,
)

ax.legend()


# ============================================================
# ANNOTATE MAJOR EVENTS
# ============================================================

major = df[
    (df["dry_extreme_cells"] >= event_threshold)
    | (df["wet_extreme_cells"] >= event_threshold)
].copy()


for _, row in major.iterrows():

    if row["dry_extreme_cells"] >= event_threshold:
        value = row["dry_extreme_cells"]
        label = (
            f"{row['date'].strftime('%Y-%m')}\n"
            f"dry: {int(value)}"
        )

        ax.annotate(
            label,
            xy=(
                row["date"],
                value,
            ),
            xytext=(0, 12),
            textcoords="offset points",
            ha="center",
            fontsize=8,
        )

    if row["wet_extreme_cells"] >= event_threshold:
        value = row["wet_extreme_cells"]
        label = (
            f"{row['date'].strftime('%Y-%m')}\n"
            f"wet: {int(value)}"
        )

        ax.annotate(
            label,
            xy=(
                row["date"],
                value,
            ),
            xytext=(0, -28),
            textcoords="offset points",
            ha="center",
            fontsize=8,
        )


# ============================================================
# FOOTER
# ============================================================

fig.text(
    0.5,
    0.015,
    "Extreme = standardized anomaly ≤ −2 or ≥ +2 | "
    "Event candidate = ≥5% of 984 SMAP cells",
    ha="center",
    fontsize=8,
)


plt.tight_layout(
    rect=[0, 0.04, 1, 1]
)


# ============================================================
# SAVE
# ============================================================

fig.savefig(
    OUT,
    dpi=200,
    bbox_inches="tight",
)

plt.close(fig)


print("\nFigure saved:")
print(OUT)

print("\nStatus: PASS")
print("=" * 70)
