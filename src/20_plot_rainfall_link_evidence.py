from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


BASE = Path("/root/earthtrend-detective")

COMMON_FILE = (
    BASE
    / "data"
    / "analysis"
    / "smap_gpm_common_months.csv"
)

LAG_FILE = (
    BASE
    / "data"
    / "analysis"
    / "smap_gpm_lag_correlation.csv"
)

OUT = (
    BASE
    / "data"
    / "analysis"
    / "figures"
    / "earthtrend_rainfall_link.png"
)


print("\n" + "=" * 70)
print("EARTH TREND DETECTIVE — RAINFALL LINK EVIDENCE")
print("=" * 70)


# ============================================================
# LOAD DATA
# ============================================================

common = pd.read_csv(COMMON_FILE)
lag = pd.read_csv(LAG_FILE)

common["date"] = pd.to_datetime(common["date"])


# ============================================================
# VALIDATION
# ============================================================

required_common = [
    "date",
    "smap_standardized_anomaly_mean",
    "standardized_rainfall_anomaly",
]

required_lag = [
    "lag_months",
    "n",
    "pearson_r",
    "pearson_p",
]

missing_common = [
    c for c in required_common
    if c not in common.columns
]

missing_lag = [
    c for c in required_lag
    if c not in lag.columns
]

if missing_common:
    raise ValueError(
        f"Missing common-month columns: {missing_common}"
    )

if missing_lag:
    raise ValueError(
        f"Missing lag columns: {missing_lag}"
    )

assert len(common) == 126
assert len(lag) == 4

assert common["date"].is_monotonic_increasing


# ============================================================
# SAME-MONTH CORRELATION
# ============================================================

x = common["standardized_rainfall_anomaly"].to_numpy()
y = common["smap_standardized_anomaly_mean"].to_numpy()

valid = np.isfinite(x) & np.isfinite(y)

x_valid = x[valid]
y_valid = y[valid]

pearson_r = np.corrcoef(
    x_valid,
    y_valid
)[0, 1]


# Regression line for visualization only.
# This is NOT used as a causal model.

slope, intercept = np.polyfit(
    x_valid,
    y_valid,
    1,
)

x_line = np.linspace(
    x_valid.min(),
    x_valid.max(),
    200,
)

y_line = (
    slope * x_line
    + intercept
)


# ============================================================
# LAG DATA
# ============================================================

lag = lag.sort_values("lag_months")

lag0 = lag.loc[
    lag["lag_months"] == 0
]

if lag0.empty:
    raise ValueError(
        "Lag-0 result not found."
    )

lag0_r = float(
    lag0.iloc[0]["pearson_r"]
)

lag0_p = float(
    lag0.iloc[0]["pearson_p"]
)


print("\nSame-month relationship")
print("-" * 70)

print(
    f"Common months : {len(common)}"
)

print(
    f"Pearson r     : {pearson_r:.6f}"
)

print(
    f"Pearson p     : {lag0_p:.6e}"
)


print("\nLag correlation")
print("-" * 70)

for _, row in lag.iterrows():

    print(
        f"Lag {int(row['lag_months'])} month(s): "
        f"r={row['pearson_r']:.6f}, "
        f"p={row['pearson_p']:.6e}, "
        f"n={int(row['n'])}"
    )


# ============================================================
# FIGURE
# ============================================================

fig, axes = plt.subplots(
    2,
    1,
    figsize=(13, 11),
)


# ============================================================
# PANEL 1 — SAME-MONTH SCATTER
# ============================================================

ax = axes[0]

ax.scatter(
    x_valid,
    y_valid,
    s=32,
    alpha=0.65,
)

ax.plot(
    x_line,
    y_line,
    linewidth=2,
    label=f"Linear fit (Pearson r = {pearson_r:.3f})",
)

ax.axhline(
    0,
    linewidth=0.9,
    linestyle="--",
)

ax.axvline(
    0,
    linewidth=0.9,
    linestyle="--",
)

ax.set_xlabel(
    "Rainfall standardized anomaly"
)

ax.set_ylabel(
    "SMAP soil-moisture standardized anomaly"
)

ax.set_title(
    "RAINFALL LINK — Same-month rainfall and soil-moisture anomalies",
    fontsize=14,
    pad=12,
)

ax.grid(
    True,
    alpha=0.25,
)

ax.legend()

ax.text(
    0.02,
    0.95,
    (
        f"n = {len(x_valid)} months\n"
        f"Pearson r = {pearson_r:.3f}\n"
        f"p = {lag0_p:.2e}"
    ),
    transform=ax.transAxes,
    va="top",
    fontsize=10,
)


# ============================================================
# PANEL 2 — LAG CORRELATION
# ============================================================

ax = axes[1]

ax.plot(
    lag["lag_months"],
    lag["pearson_r"],
    marker="o",
    linewidth=2,
    label="Pearson correlation",
)

ax.axhline(
    0,
    linewidth=0.9,
    linestyle="--",
)

ax.set_xticks(
    lag["lag_months"]
)

ax.set_xlabel(
    "Rainfall lead (months)"
)

ax.set_ylabel(
    "Pearson correlation"
)

ax.set_title(
    "LAG TEST — Association weakens as rainfall is shifted earlier",
    fontsize=14,
    pad=12,
)

ax.grid(
    True,
    alpha=0.25,
)

ax.set_ylim(
    min(-0.1, lag["pearson_r"].min() - 0.05),
    max(0.8, lag["pearson_r"].max() + 0.05),
)

ax.legend()


# Annotate each lag value

for _, row in lag.iterrows():

    lag_month = int(
        row["lag_months"]
    )

    r = float(
        row["pearson_r"]
    )

    ax.annotate(
        f"r = {r:.3f}",
        (
            lag_month,
            r,
        ),
        xytext=(0, 10),
        textcoords="offset points",
        ha="center",
        fontsize=9,
    )


# ============================================================
# FOOTER
# ============================================================

fig.text(
    0.5,
    0.015,
    (
        "SMAP–GPM common period: Apr 2015–Sep 2025 | "
        "Standardized anomalies | "
        "Correlation indicates association, not causality"
    ),
    ha="center",
    fontsize=8,
)


plt.tight_layout(
    rect=[0, 0.04, 1, 1]
)


# ============================================================
# SAVE
# ============================================================

OUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

fig.savefig(
    OUT,
    dpi=200,
    bbox_inches="tight",
)

plt.close(fig)


# ============================================================
# FINAL
# ============================================================

print("\nFigure saved:")
print(OUT)

print("\nStatus: PASS")
print("=" * 70)
