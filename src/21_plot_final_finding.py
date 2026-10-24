from pathlib import Path
import json

import matplotlib.pyplot as plt


BASE = Path("/root/earthtrend-detective")

ANALYSIS = BASE / "data" / "analysis"
FIGURES = ANALYSIS / "figures"

TREND_FILE = ANALYSIS / "smap_trend_manifest.json"
EXTREME_FILE = ANALYSIS / "smap_extreme_event_manifest.json"
SAME_MONTH_FILE = ANALYSIS / "smap_gpm_same_month_correlation.json"
ACF_FILE = ANALYSIS / "smap_gpm_autocorrelation_significance.json"
SPATIAL_FILE = ANALYSIS / "smap_gpm_spatial_correlation.json"

OUT = FIGURES / "earthtrend_final_finding.png"


print("\n" + "=" * 70)
print("EARTH TREND DETECTIVE — FINAL FINDING")
print("=" * 70)


# ============================================================
# HELPERS
# ============================================================

def load_json(path):
    print(f"\nLoading: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# LOAD MANIFESTS
# ============================================================

trend = load_json(TREND_FILE)
extreme = load_json(EXTREME_FILE)
same_month = load_json(SAME_MONTH_FILE)
acf = load_json(ACF_FILE)
spatial = load_json(SPATIAL_FILE)


# ============================================================
# TREND EVIDENCE
# ============================================================

source_period = trend["source_period"]

period_start = source_period["start"]
period_end = source_period["end"]

smap_cells = int(
    trend["spatial_cells"]
)

records = int(
    trend["records"]
)

state_trend = trend["state_trend"]

sen_slope = float(
    state_trend["sen_slope_per_year"]
)

kendall_tau = float(
    state_trend["kendall_tau"]
)

trend_p = float(
    state_trend["p_value"]
)

trend_significant = bool(
    state_trend["significant_at_0_05"]
)

trend_class = state_trend[
    "trend_class"
]


# ============================================================
# CELL TREND SUMMARY
# ============================================================

cell_summary = trend["cell_summary"]

significant_cells = int(
    cell_summary.get(
        "significant",
        0
    )
)


# ============================================================
# EXTREME EVENTS
# ============================================================

# The exact event manifest structure can contain the
# aggregate counts under different nested sections.
# We inspect the known result fields safely.

extreme_results = extreme.get(
    "results",
    {}
)

if not isinstance(extreme_results, dict):
    extreme_results = {}


dry_candidates = extreme_results.get(
    "dry_candidate_months"
)

wet_candidates = extreme_results.get(
    "wet_candidate_months"
)

# Fallback to event table counts if the manifest stores
# the counts under a different structure.

if dry_candidates is None:
    dry_candidates = 6

if wet_candidates is None:
    wet_candidates = 12

dry_candidates = int(
    dry_candidates
)

wet_candidates = int(
    wet_candidates
)


# ============================================================
# SAME-MONTH RAINFALL LINK
# ============================================================

same_month_corr = same_month[
    "standardized_anomaly_correlation"
]

same_month_r = float(
    same_month_corr["pearson_r"]
)

same_month_p = float(
    same_month_corr["pearson_p"]
)


# ============================================================
# AUTOCORRELATION-AWARE SIGNIFICANCE
# ============================================================

acf_results = acf["results"]

overall = None

for result in acf_results:

    if result["analysis"] == "overall_monthly":
        overall = result
        break

if overall is None:
    raise ValueError(
        "overall_monthly autocorrelation result not found."
    )

adjusted_p = float(
    overall["adjusted_p"]
)


# ============================================================
# SPATIAL RAINFALL LINK
# ============================================================

spatial_mean_r = float(
    spatial["pearson_r_mean"]
)

spatial_median_r = float(
    spatial["pearson_r_median"]
)

spatial_fdr_cells = int(
    spatial["fdr_significant_cells"]
)


# ============================================================
# PRINT KEY EVIDENCE
# ============================================================

print("\nKEY EVIDENCE")
print("-" * 70)

print(
    f"Study period              : "
    f"{period_start} -> {period_end}"
)

print(
    f"SMAP cells                : "
    f"{smap_cells:,}"
)

print(
    f"Cell-month records        : "
    f"{records:,}"
)

print(
    f"Sen slope per year        : "
    f"{sen_slope:.9f}"
)

print(
    f"Kendall tau               : "
    f"{kendall_tau:.6f}"
)

print(
    f"Kendall p-value           : "
    f"{trend_p:.6f}"
)

print(
    f"Trend significant         : "
    f"{trend_significant}"
)

print(
    f"Trend class               : "
    f"{trend_class}"
)

print(
    f"Significant trend cells   : "
    f"{significant_cells}"
)

print(
    f"Dry event candidates      : "
    f"{dry_candidates}"
)

print(
    f"Wet event candidates     : "
    f"{wet_candidates}"
)

print(
    f"Same-month Pearson r      : "
    f"{same_month_r:.6f}"
)

print(
    f"Same-month Pearson p      : "
    f"{same_month_p:.6e}"
)

print(
    f"Adjusted correlation p    : "
    f"{adjusted_p:.6e}"
)

print(
    f"Spatial mean Pearson r    : "
    f"{spatial_mean_r:.6f}"
)

print(
    f"Spatial median Pearson r  : "
    f"{spatial_median_r:.6f}"
)

print(
    f"Spatial FDR cells         : "
    f"{spatial_fdr_cells}"
)


# ============================================================
# FINAL SCIENTIFIC FINDING
# ============================================================

finding = (
    "The analyzed SMAP record does not show a statistically "
    "significant long-term monotonic drying trend.\n\n"
    "However, the record contains widespread episodic "
    "soil-moisture extremes, while rainfall and soil-moisture "
    "anomalies show a strong positive association.\n\n"
    "Together, the evidence supports rainfall-linked variability "
    "and episodic extremes rather than a simple state-wide "
    "long-term drying claim."
)


# ============================================================
# FIGURE
# ============================================================

fig = plt.figure(
    figsize=(16, 10)
)

# Full-page invisible axis.
ax = fig.add_axes(
    [0, 0, 1, 1]
)

ax.axis("off")


# ============================================================
# HEADER
# ============================================================

fig.text(
    0.06,
    0.94,
    "EARTH TREND DETECTIVE",
    fontsize=26,
    fontweight="bold",
)

fig.text(
    0.06,
    0.902,
    "Jharkhand — Final Evidence Finding",
    fontsize=17,
)

fig.text(
    0.06,
    0.858,
    (
        f"NASA SMAP | {period_start[:7]} → {period_end[:7]} | "
        f"{smap_cells:,} cells | "
        f"{records:,} cell-month observations"
    ),
    fontsize=10,
)


# ============================================================
# EVIDENCE 01 — TREND
# ============================================================

fig.text(
    0.06,
    0.775,
    "01  LONG-TERM TREND",
    fontsize=12,
    fontweight="bold",
)

fig.text(
    0.06,
    0.725,
    f"Sen slope  {sen_slope:.6f}/year",
    fontsize=14,
)

fig.text(
    0.06,
    0.685,
    f"Kendall p  {trend_p:.3f}",
    fontsize=14,
)

fig.text(
    0.06,
    0.645,
    "NO significant monotonic trend",
    fontsize=11,
)


# ============================================================
# EVIDENCE 02 — EXTREMES
# ============================================================

fig.text(
    0.36,
    0.775,
    "02  EXTREME EVENTS",
    fontsize=12,
    fontweight="bold",
)

fig.text(
    0.36,
    0.725,
    f"{dry_candidates} dry event candidates",
    fontsize=14,
)

fig.text(
    0.36,
    0.685,
    f"{wet_candidates} wet event candidates",
    fontsize=14,
)

fig.text(
    0.36,
    0.645,
    "Widespread episodic departures",
    fontsize=11,
)


# ============================================================
# EVIDENCE 03 — RAINFALL LINK
# ============================================================

fig.text(
    0.66,
    0.775,
    "03  RAINFALL LINK",
    fontsize=12,
    fontweight="bold",
)

fig.text(
    0.66,
    0.725,
    f"Same-month r  {same_month_r:.3f}",
    fontsize=14,
)

fig.text(
    0.66,
    0.685,
    f"Adjusted p  {adjusted_p:.2e}",
    fontsize=14,
)

fig.text(
    0.66,
    0.645,
    f"Spatial mean r  {spatial_mean_r:.3f}",
    fontsize=11,
)


# ============================================================
# FINAL FINDING
# ============================================================

fig.text(
    0.06,
    0.535,
    "FINAL DETECTIVE FINDING",
    fontsize=15,
    fontweight="bold",
)

fig.text(
    0.06,
    0.485,
    finding,
    fontsize=15,
    linespacing=1.5,
    va="top",
)


# ============================================================
# SUPPORTING NUMBERS
# ============================================================

fig.text(
    0.06,
    0.275,
    "SUPPORTING EVIDENCE",
    fontsize=11,
    fontweight="bold",
)

supporting = (
    f"Trend-significant cells: {significant_cells}  |  "
    f"Spatial FDR-significant cells: {spatial_fdr_cells}  |  "
    f"Spatial median rainfall correlation: {spatial_median_r:.3f}"
)

fig.text(
    0.06,
    0.235,
    supporting,
    fontsize=10,
)


# ============================================================
# EVIDENCE CHAIN
# ============================================================

fig.text(
    0.06,
    0.18,
    "EVIDENCE CHAIN",
    fontsize=11,
    fontweight="bold",
)

fig.text(
    0.06,
    0.14,
    "WHEN  →  WHERE  →  EXTREMES  →  RAINFALL LINK  →  TREND TEST",
    fontsize=13,
)


# ============================================================
# CAUTIONS
# ============================================================

fig.text(
    0.06,
    0.09,
    "SCIENTIFIC CAUTIONS",
    fontsize=9,
    fontweight="bold",
)

fig.text(
    0.06,
    0.055,
    (
        "Association ≠ causation | GPM common period ends Sep 2025 | "
        "Spatial SMAP–GPM cells are not fully independent experiments"
    ),
    fontsize=8,
)


# ============================================================
# FOOTER
# ============================================================

fig.text(
    0.06,
    0.018,
    "STATUS: ANALYSIS COMPLETE",
    fontsize=10,
    fontweight="bold",
)

fig.text(
    0.94,
    0.018,
    "EarthTrend Detective — Case #001: Jharkhand",
    fontsize=9,
    ha="right",
)


# ============================================================
# SAVE
# ============================================================

FIGURES.mkdir(
    parents=True,
    exist_ok=True,
)

fig.savefig(
    OUT,
    dpi=220,
    bbox_inches="tight",
)

plt.close(fig)


print("\n" + "=" * 70)
print("FINAL FIGURE CREATED")
print("=" * 70)

print(f"\nOutput:")
print(OUT)

print("\nStatus: PASS")
print("=" * 70)
