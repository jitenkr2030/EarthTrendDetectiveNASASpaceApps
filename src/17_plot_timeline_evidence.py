from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


BASE = Path("/root/earthtrend-detective")

INPUT = BASE / "data" / "analysis" / "earthtrend_timeline.csv"
OUT = BASE / "data" / "analysis" / "figures" / "earthtrend_when_timeline.png"


print("\n" + "=" * 70)
print("EARTH TREND DETECTIVE — WHEN EVIDENCE")
print("=" * 70)


# ============================================================
# LOAD
# ============================================================

df = pd.read_csv(INPUT)
df["date"] = pd.to_datetime(df["date"])

print(f"\nRows loaded: {len(df)}")
print(
    f"Period: {df['date'].min().date()} -> "
    f"{df['date'].max().date()}"
)


# ============================================================
# VALIDATION
# ============================================================

assert len(df) == 138
assert df["date"].is_monotonic_increasing
assert df["soil_moisture_mean"].notna().all()
assert df["climatology_mean"].notna().all()
assert df["standardized_anomaly"].notna().all()


# ============================================================
# FIGURE
# ============================================================

fig, (ax1, ax2) = plt.subplots(
    2,
    1,
    figsize=(14, 9),
    sharex=True,
)


# ============================================================
# PANEL 1 — ACTUAL SOIL MOISTURE
# ============================================================

ax1.plot(
    df["date"],
    df["soil_moisture_mean"],
    linewidth=1.8,
    label="SMAP state mean",
)

ax1.plot(
    df["date"],
    df["climatology_mean"],
    linewidth=1.4,
    linestyle="--",
    label="Calendar-month climatology",
)

ax1.set_ylabel("Soil moisture (m³/m³)")
ax1.set_title(
    "WHEN? — Jharkhand soil-moisture timeline"
)

ax1.grid(True, alpha=0.25)
ax1.legend()


# ============================================================
# PANEL 2 — STANDARDIZED ANOMALY
# ============================================================

ax2.axhline(
    0,
    linewidth=1.0,
)

ax2.axhline(
    2,
    linewidth=0.8,
    linestyle="--",
)

ax2.axhline(
    -2,
    linewidth=0.8,
    linestyle="--",
)

ax2.plot(
    df["date"],
    df["standardized_anomaly"],
    linewidth=1.5,
    label="Standardized anomaly",
)

ax2.set_ylabel("Standardized anomaly (z)")
ax2.set_xlabel("Date")

ax2.grid(True, alpha=0.25)
ax2.legend()


# ============================================================
# OVERALL TITLE
# ============================================================

fig.suptitle(
    "EarthTrend Detective — Jharkhand SMAP Evidence",
    fontsize=16,
    y=0.98,
)

fig.text(
    0.5,
    0.01,
    "SMAP Level-4 soil moisture | Apr 2015–Sep 2026 | "
    "984-cell Jharkhand analysis",
    ha="center",
    fontsize=9,
)


plt.tight_layout(rect=[0, 0.03, 1, 0.96])


# ============================================================
# SAVE
# ============================================================

fig.savefig(
    OUT,
    dpi=180,
    bbox_inches="tight",
)

plt.close(fig)


print("\nFigure saved:")
print(OUT)

print("\nStatus: PASS")
print("=" * 70)
