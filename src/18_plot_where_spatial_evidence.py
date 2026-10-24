from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


BASE = Path("/root/earthtrend-detective")

INPUT = (
    BASE
    / "data"
    / "analysis"
    / "smap_gpm_spatial_correlation.csv"
)

OUT = (
    BASE
    / "data"
    / "analysis"
    / "figures"
    / "earthtrend_where_rainfall_link.png"
)


print("\n" + "=" * 70)
print("EARTH TREND DETECTIVE — WHERE EVIDENCE")
print("=" * 70)


# ============================================================
# LOAD
# ============================================================

print("\nLoading spatial correlation evidence...")

df = pd.read_csv(INPUT)

print(f"Rows loaded: {len(df)}")


# ============================================================
# VALIDATION
# ============================================================

required = [
    "smap_latitude",
    "smap_longitude",
    "pearson_r",
    "pearson_p",
    "fdr_significant",
    "correlation_class",
]

missing = [c for c in required if c not in df.columns]

if missing:
    raise ValueError(
        f"Missing required columns: {missing}"
    )


assert len(df) == 984
assert df["pearson_r"].notna().all()
assert df["smap_latitude"].notna().all()
assert df["smap_longitude"].notna().all()


# ============================================================
# SUMMARY
# ============================================================

mean_r = df["pearson_r"].mean()
median_r = df["pearson_r"].median()
min_r = df["pearson_r"].min()
max_r = df["pearson_r"].max()

positive_pct = (
    (df["pearson_r"] > 0).mean() * 100
)

strong_pct = (
    (df["pearson_r"] >= 0.7).mean() * 100
)

fdr_pct = (
    df["fdr_significant"].astype(bool).mean() * 100
)

print("\nSpatial evidence summary")
print("-" * 70)

print(f"SMAP cells          : {len(df)}")
print(f"Mean Pearson r      : {mean_r:.6f}")
print(f"Median Pearson r    : {median_r:.6f}")
print(f"Minimum Pearson r   : {min_r:.6f}")
print(f"Maximum Pearson r   : {max_r:.6f}")
print(f"Positive cells      : {positive_pct:.2f}%")
print(f"r >= 0.70 cells     : {strong_pct:.2f}%")
print(f"FDR-significant     : {fdr_pct:.2f}%")


# ============================================================
# FIGURE
# ============================================================

fig, ax = plt.subplots(
    figsize=(11, 9)
)


# ============================================================
# SPATIAL SCATTER
# ============================================================

scatter = ax.scatter(
    df["smap_longitude"],
    df["smap_latitude"],
    c=df["pearson_r"],
    s=28,
    alpha=0.85,
    edgecolors="none",
)


# ============================================================
# AXES
# ============================================================

ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")

ax.set_title(
    "WHERE? — Rainfall–soil-moisture association across Jharkhand",
    fontsize=14,
    pad=12,
)

ax.grid(
    True,
    alpha=0.25,
)


# ============================================================
# COLORBAR
# ============================================================

cbar = fig.colorbar(
    scatter,
    ax=ax,
    pad=0.02,
)

cbar.set_label(
    "Pearson correlation (r)"
)


# ============================================================
# ANNOTATION
# ============================================================

text = (
    f"984 SMAP cells\n"
    f"Mean r = {mean_r:.3f}\n"
    f"Median r = {median_r:.3f}\n"
    f"Range = {min_r:.3f}–{max_r:.3f}\n"
    f"Positive cells = {positive_pct:.1f}%"
)

ax.text(
    0.02,
    0.02,
    text,
    transform=ax.transAxes,
    fontsize=9,
    verticalalignment="bottom",
    bbox=dict(
        boxstyle="round,pad=0.4",
        facecolor="white",
        alpha=0.85,
    ),
)


# ============================================================
# FOOTER
# ============================================================

fig.text(
    0.5,
    0.015,
    "SMAP–GPM common period: Apr 2015–Sep 2025 | "
    "Pearson correlation of standardized anomalies",
    ha="center",
    fontsize=8,
)


plt.tight_layout(
    rect=[0, 0.035, 1, 1]
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
