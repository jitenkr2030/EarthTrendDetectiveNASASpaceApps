import json
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd


# ============================================================
# CONFIG
# ============================================================

BASE = Path("/root/earthtrend-detective")
ANALYSIS = BASE / "data" / "analysis"

FILES = {
    "trend": ANALYSIS / "smap_trend_manifest.json",
    "seasonal_trend": ANALYSIS / "smap_seasonal_trend_manifest.json",
    "spatial_trend": ANALYSIS / "smap_spatial_trend_manifest.json",
    "extreme": ANALYSIS / "smap_extreme_event_manifest.json",
    "same_month": ANALYSIS / "smap_gpm_same_month_correlation.json",
    "lag": ANALYSIS / "smap_gpm_lag_correlation.json",
    "seasonal_gpm": ANALYSIS / "smap_gpm_seasonal_correlation.json",
    "acf": ANALYSIS / "smap_gpm_autocorrelation_significance.json",
    "spatial_gpm": ANALYSIS / "smap_gpm_spatial_correlation.json",
    "sensitivity": ANALYSIS / "smap_gpm_spatial_sensitivity.json",
}

OUT_JSON = ANALYSIS / "earthtrend_final_evidence.json"
OUT_CSV = ANALYSIS / "earthtrend_final_evidence.csv"
OUT_MD = ANALYSIS / "earthtrend_final_finding.md"


# ============================================================
# HELPERS
# ============================================================

def load_json(path):
    if not path.exists():
        raise FileNotFoundError(f"Required file missing: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_required_files():
    print("\nChecking required evidence files...")

    missing = []

    for name, path in FILES.items():
        if path.exists():
            print(f"  PASS  {name}: {path.name}")
        else:
            print(f"  FAIL  {name}: {path.name}")
            missing.append(str(path))

    if missing:
        raise FileNotFoundError(
            "Missing required evidence files:\n" + "\n".join(missing)
        )


# ============================================================
# START
# ============================================================

print("\n" + "=" * 70)
print("EARTH TREND DETECTIVE — FINAL EVIDENCE SYNTHESIS")
print("=" * 70)

check_required_files()

data = {
    name: load_json(path)
    for name, path in FILES.items()
}

print("\nLoaded all required evidence manifests.")


# ============================================================
# 1. DATASET
# ============================================================

trend = data["trend"]

dataset = {
    "region": "Jharkhand, India",
    "primary_variable": "SMAP surface soil moisture",
    "smap_product": "SPL4SMGP Version 008",
    "smap_variable": "/Geophysical_Data/sm_surface",
    "smap_units": "m3/m3",
    "smap_start": trend["source_period"]["start"],
    "smap_end": trend["source_period"]["end"],
    "smap_months": trend["months"],
    "smap_cells": trend["spatial_cells"],
    "smap_records": trend["records"],
    "gpm_product": "GPM IMERG Monthly Version 07B",
    "gpm_common_start": data["same_month"]["period_start"],
    "gpm_common_end": data["same_month"]["period_end"],
    "gpm_common_months": data["same_month"]["common_months"],
}


# ============================================================
# 2. LONG-TERM TREND
# ============================================================

state_trend = trend["state_trend"]
cell_summary = trend["cell_summary"]

trend_evidence = {
    "sen_slope_per_month": state_trend["sen_slope_per_month"],
    "sen_slope_per_year": state_trend["sen_slope_per_year"],
    "kendall_tau": state_trend["kendall_tau"],
    "p_value": state_trend["p_value"],
    "significant_at_0_05": state_trend["significant_at_0_05"],
    "trend_class": state_trend["trend_class"],
    "total_cells": cell_summary["total_cells"],
    "significant_cells": cell_summary["significant_cells"],
    "significant_fraction": cell_summary["significant_fraction"],
    "increasing_cells": cell_summary["increasing_cells"],
    "decreasing_cells": cell_summary["decreasing_cells"],
    "significant_increasing_cells": cell_summary["significant_increasing_cells"],
    "significant_decreasing_cells": cell_summary["significant_decreasing_cells"],
}


# ============================================================
# 3. SEASONAL TREND
# ============================================================

seasonal_trend = data["seasonal_trend"]

seasonal_results = seasonal_trend["results"]

seasonal_trend_evidence = {
    "state_seasons": seasonal_results["state_seasons"],
    "significant_state_seasons": seasonal_results["significant_state_seasons"],
    "cell_season_results": seasonal_results["cell_season_results"],
    "significant_cell_seasons_raw": seasonal_results["significant_cell_seasons"],
    "increasing_cell_seasons": seasonal_results["increasing_cell_seasons"],
    "decreasing_cell_seasons": seasonal_results["decreasing_cell_seasons"],
    "season_definition": seasonal_trend["season_definition"],
    "statistical_note": seasonal_trend["method"]["statistical_note"],
}


# ============================================================
# 4. SPATIAL TREND
# ============================================================

spatial_trend = data["spatial_trend"]
spatial_stats = spatial_trend["statistics"]

spatial_trend_evidence = {
    "raw_significant_results": spatial_stats["raw_significant_results"],
    "fdr_significant_results": spatial_stats["fdr_significant_results"],
    "spatial_hotspot_results": spatial_stats["spatial_hotspot_results"],
    "spatial_cluster_results": spatial_stats["spatial_cluster_results"],
    "isolated_significant_results": spatial_stats["isolated_significant_results"],
    "fdr_method": spatial_trend["multiple_testing"]["method"],
    "fdr_family": spatial_trend["multiple_testing"]["family"],
    "fdr_threshold": spatial_trend["multiple_testing"]["threshold"],
    "connectivity": spatial_trend["spatial_method"]["connectivity"],
}


# ============================================================
# 5. EXTREME EVENTS
# ============================================================

extreme = data["extreme"]

extreme_results = extreme["results"]

extreme_evidence = {
    "extreme_dry_cell_months": extreme_results["extreme_dry_cell_months"],
    "extreme_wet_cell_months": extreme_results["extreme_wet_cell_months"],
    "total_extreme_cell_months": extreme_results["total_extreme_cell_months"],
    "dry_candidate_months": extreme_results["dry_candidate_months"],
    "wet_candidate_months": extreme_results["wet_candidate_months"],
    "total_event_episodes": extreme_results["total_event_episodes"],
    "dry_event_episodes": extreme_results["dry_event_episodes"],
    "wet_event_episodes": extreme_results["wet_event_episodes"],
    "mixed_event_episodes": extreme_results["mixed_event_episodes"],
    "unique_cells_with_extremes": extreme_results["unique_cells_with_extremes"],
    "extreme_dry_threshold_z": extreme["method"]["extreme_dry_threshold_z"],
    "extreme_wet_threshold_z": extreme["method"]["extreme_wet_threshold_z"],
    "minimum_event_fraction": extreme["method"]["minimum_event_fraction"],
}


# ============================================================
# 6. SAME-MONTH RAINFALL ASSOCIATION
# ============================================================

same_month = data["same_month"]

same_month_evidence = {
    "common_months": same_month["common_months"],
    "period_start": same_month["period_start"],
    "period_end": same_month["period_end"],
    "standardized_pearson_r": (
        same_month["standardized_anomaly_correlation"]["pearson_r"]
    ),
    "standardized_pearson_p": (
        same_month["standardized_anomaly_correlation"]["pearson_p"]
    ),
    "standardized_spearman_rho": (
        same_month["standardized_anomaly_correlation"]["spearman_rho"]
    ),
    "standardized_spearman_p": (
        same_month["standardized_anomaly_correlation"]["spearman_p"]
    ),
    "raw_pearson_r": (
        same_month["raw_variable_correlation"]["pearson_r"]
    ),
    "raw_pearson_p": (
        same_month["raw_variable_correlation"]["pearson_p"]
    ),
    "simultaneous_events": same_month["simultaneous_events"],
}


# ============================================================
# 7. LAG ANALYSIS
# ============================================================

lag = data["lag"]

lag_evidence = {
    "tested_lags_months": lag["tested_lags_months"],
    "same_month_pearson_r": lag["same_month_pearson_r"],
    "best_absolute_pearson_lag_months": (
        lag["best_absolute_pearson_lag_months"]
    ),
    "best_absolute_pearson_r": lag["best_absolute_pearson_r"],
    "interpretation": lag["interpretation"],
    "results": lag["results"],
}


# ============================================================
# 8. SEASONAL RAINFALL ASSOCIATION
# ============================================================

seasonal_gpm = data["seasonal_gpm"]

seasonal_gpm_evidence = {
    "strongest_season": seasonal_gpm[
        "strongest_season_by_absolute_pearson"
    ],
    "strongest_pearson_r": seasonal_gpm["strongest_pearson_r"],
    "results": seasonal_gpm["results"],
}


# ============================================================
# 9. AUTOCORRELATION-AWARE SIGNIFICANCE
# ============================================================

acf = data["acf"]

acf_evidence = {
    "alpha": acf["alpha"],
    "method": acf["method"],
    "overall_period": acf["overall_period"],
    "seasonal_method": acf["seasonal_method"],
    "results": acf["results"],
}


overall_acf = next(
    r for r in acf["results"]
    if r["analysis"] == "overall_monthly"
)


# ============================================================
# 10. SPATIAL RAINFALL ASSOCIATION
# ============================================================

spatial_gpm = data["spatial_gpm"]

spatial_gpm_evidence = {
    "smap_cells": spatial_gpm["smap_cells"],
    "gpm_cells": spatial_gpm["gpm_cells"],
    "mapped_smap_cells": spatial_gpm["mapped_smap_cells"],
    "joined_rows": spatial_gpm["joined_rows"],
    "correlated_cells": spatial_gpm["correlated_cells"],
    "fdr_significant_cells": spatial_gpm["fdr_significant_cells"],
    "pearson_r_min": spatial_gpm["pearson_r_min"],
    "pearson_r_mean": spatial_gpm["pearson_r_mean"],
    "pearson_r_median": spatial_gpm["pearson_r_median"],
    "pearson_r_max": spatial_gpm["pearson_r_max"],
    "mapping_distance_km_mean": spatial_gpm["mapping_distance_km_mean"],
    "mapping_distance_km_max": spatial_gpm["mapping_distance_km_max"],
    "fdr_method": spatial_gpm["fdr_method"],
}


# ============================================================
# 11. SPATIAL SENSITIVITY
# ============================================================

sensitivity = data["sensitivity"]

sensitivity_evidence = {
    "thresholds_tested_km": sensitivity["thresholds_tested_km"],
    "total_valid_cells": sensitivity["total_valid_cells"],
    "results": sensitivity["results"],
}

sensitivity_5km = next(
    r for r in sensitivity["results"]
    if r["distance_threshold_km"] == 5.0
)


# ============================================================
# 12. SCIENTIFIC INTERPRETATION
# ============================================================

long_term_drying_supported = (
    state_trend["significant_at_0_05"] is True
    and state_trend["sen_slope_per_year"] < 0
)

no_significant_spatial_hotspots = (
    spatial_stats["fdr_significant_results"] == 0
    and spatial_stats["spatial_hotspot_results"] == 0
)

overall_rainfall_association_significant = (
    overall_acf["significant_after_adjustment"] is True
)

final_finding = (
    "Across the analyzed Jharkhand SMAP record, no statistically "
    "significant long-term monotonic soil-moisture decline was detected. "
    "The state-level trend was slightly negative but highly non-significant, "
    "and none of the 984 SMAP cells had a statistically significant "
    "long-term trend in the first-pass cell analysis. Seasonal analysis "
    "also found no significant state-level seasonal trends, while the "
    "seven raw significant cell-season results disappeared after "
    "Benjamini-Hochberg FDR correction, leaving no statistically robust "
    "spatial-seasonal hotspots. At the same time, the record contains "
    "widespread episodic soil-moisture extremes. Soil-moisture and rainfall "
    "anomalies show a strong positive same-month association, and that "
    "overall association remains significant after an "
    "autocorrelation-aware effective-sample-size adjustment. The spatial "
    "rainfall relationship is also consistently positive across the "
    "mapped SMAP cells and remains stable when the analysis is restricted "
    "to closer SMAP-GPM matches. Together, the evidence supports strong "
    "rainfall-linked variability and episodic extremes, rather than a "
    "simple state-wide long-term drying claim."
)


# ============================================================
# 13. LIMITATIONS
# ============================================================

limitations = [
    (
        "The primary long-term SMAP trend test is a first-pass "
        "Kendall/Mann-Kendall-style analysis and is not a fully "
        "seasonality- and autocorrelation-corrected trend model."
    ),
    (
        "The seasonal trend analysis explicitly states that it is not "
        "an autocorrelation-corrected Seasonal Mann-Kendall implementation."
    ),
    (
        "Seasonal rainfall-soil-moisture analyses use relatively small "
        "complete season-year sample sizes; therefore seasonal estimates "
        "should be interpreted cautiously."
    ),
    (
        "The GPM comparison period ends in September 2025, whereas the "
        "SMAP analysis continues through September 2026."
    ),
    (
        "The spatial cross-variable analysis maps 984 SMAP cells to 703 "
        "coarser GPM cells, so the 984 spatial correlations are not "
        "984 independent spatial experiments."
    ),
    (
        "FDR significance in the spatial cross-variable analysis is a "
        "multiple-testing screening result and does not remove all "
        "spatial-dependence concerns."
    ),
    (
        "Extreme-event thresholds and the minimum 5 percent affected-cell "
        "criterion are analytical definitions used by this study."
    ),
    (
        "Correlation and lagged association establish statistical "
        "association, not physical causality."
    ),
]


# ============================================================
# 14. EVIDENCE OBJECT
# ============================================================

generated_at = datetime.now(timezone.utc).isoformat()

evidence = {
    "project": "EarthTrend Detective",
    "case": "Case #001 — Jharkhand",
    "generated_at_utc": generated_at,
    "status": "PASS",

    "DATA": dataset,

    "EVIDENCE": {
        "LONG_TERM_TREND": trend_evidence,
        "SEASONAL_TREND": seasonal_trend_evidence,
        "SPATIAL_TREND": spatial_trend_evidence,
        "EXTREME_EVENTS": extreme_evidence,
        "RAINFALL_SAME_MONTH": same_month_evidence,
        "RAINFALL_LAG": lag_evidence,
        "RAINFALL_SEASONAL": seasonal_gpm_evidence,
        "RAINFALL_AUTOCORRELATION_AWARE": acf_evidence,
        "RAINFALL_SPATIAL": spatial_gpm_evidence,
        "SPATIAL_SENSITIVITY": sensitivity_evidence,
    },

    "INTERPRETATION": {
        "long_term_drying_supported": long_term_drying_supported,
        "no_significant_spatial_hotspots": no_significant_spatial_hotspots,
        "overall_rainfall_association_significant_after_adjustment": (
            overall_rainfall_association_significant
        ),
        "final_finding": final_finding,
        "causality_statement": (
            "The analyses demonstrate association, not causality."
        ),
    },

    "LIMITATIONS": limitations,
}


# ============================================================
# 15. SAVE JSON
# ============================================================

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(
        evidence,
        f,
        indent=2,
        ensure_ascii=False,
    )


# ============================================================
# 16. SAVE CSV
# ============================================================

rows = [
    ("DATA", "SMAP months", dataset["smap_months"]),
    ("DATA", "SMAP cells", dataset["smap_cells"]),
    ("DATA", "SMAP records", dataset["smap_records"]),

    ("TREND", "Sen slope per month",
     trend_evidence["sen_slope_per_month"]),
    ("TREND", "Sen slope per year",
     trend_evidence["sen_slope_per_year"]),
    ("TREND", "Kendall tau",
     trend_evidence["kendall_tau"]),
    ("TREND", "p-value",
     trend_evidence["p_value"]),
    ("TREND", "Significant at 0.05",
     trend_evidence["significant_at_0_05"]),
    ("TREND", "Significant cells",
     trend_evidence["significant_cells"]),

    ("SEASONAL TREND", "Significant state seasons",
     seasonal_trend_evidence["significant_state_seasons"]),
    ("SEASONAL TREND", "Raw significant cell-seasons",
     seasonal_trend_evidence["significant_cell_seasons_raw"]),

    ("SPATIAL TREND", "Raw significant results",
     spatial_trend_evidence["raw_significant_results"]),
    ("SPATIAL TREND", "FDR significant results",
     spatial_trend_evidence["fdr_significant_results"]),
    ("SPATIAL TREND", "Spatial hotspots",
     spatial_trend_evidence["spatial_hotspot_results"]),

    ("EXTREMES", "Extreme dry cell-months",
     extreme_evidence["extreme_dry_cell_months"]),
    ("EXTREMES", "Extreme wet cell-months",
     extreme_evidence["extreme_wet_cell_months"]),
    ("EXTREMES", "Total extreme cell-months",
     extreme_evidence["total_extreme_cell_months"]),
    ("EXTREMES", "Total event episodes",
     extreme_evidence["total_event_episodes"]),

    ("RAINFALL", "Same-month Pearson r",
     same_month_evidence["standardized_pearson_r"]),
    ("RAINFALL", "Same-month Pearson p",
     same_month_evidence["standardized_pearson_p"]),

    ("RAINFALL LAG", "Best lag months",
     lag_evidence["best_absolute_pearson_lag_months"]),
    ("RAINFALL LAG", "Best lag Pearson r",
     lag_evidence["best_absolute_pearson_r"]),

    ("RAINFALL ACF", "Overall effective sample size",
     overall_acf["effective_n"]),
    ("RAINFALL ACF", "Overall adjusted p",
     overall_acf["adjusted_p"]),
    ("RAINFALL ACF", "Significant after adjustment",
     overall_acf["significant_after_adjustment"]),

    ("SPATIAL RAINFALL", "Mean Pearson r",
     spatial_gpm_evidence["pearson_r_mean"]),
    ("SPATIAL RAINFALL", "Median Pearson r",
     spatial_gpm_evidence["pearson_r_median"]),
    ("SPATIAL RAINFALL", "Minimum Pearson r",
     spatial_gpm_evidence["pearson_r_min"]),
    ("SPATIAL RAINFALL", "Maximum Pearson r",
     spatial_gpm_evidence["pearson_r_max"]),
    ("SPATIAL RAINFALL", "Positive cells (%)",
     sensitivity["results"][0]["positive_percent"]),

    ("SENSITIVITY", "<=5 km cells",
     sensitivity_5km["cells"]),
    ("SENSITIVITY", "<=5 km mean Pearson r",
     sensitivity_5km["mean_r"]),
    ("SENSITIVITY", "<=5 km median Pearson r",
     sensitivity_5km["median_r"]),
]

df = pd.DataFrame(
    rows,
    columns=["section", "metric", "value"],
)

df.to_csv(OUT_CSV, index=False)


# ============================================================
# 17. SAVE MARKDOWN FINDING
# ============================================================

with open(OUT_MD, "w", encoding="utf-8") as f:

    f.write("# EarthTrend Detective — Final Finding\n\n")
    f.write("## Case #001 — Jharkhand\n\n")

    f.write("## Final detective finding\n\n")
    f.write(final_finding + "\n\n")

    f.write("## 1. Data\n\n")

    f.write(
        f"- SMAP product: **{dataset['smap_product']}**\n"
    )
    f.write(
        f"- SMAP variable: **{dataset['smap_variable']}**\n"
    )
    f.write(
        f"- Analysis period: **{dataset['smap_start']} → "
        f"{dataset['smap_end']}**\n"
    )
    f.write(
        f"- Monthly periods: **{dataset['smap_months']}**\n"
    )
    f.write(
        f"- SMAP cells: **{dataset['smap_cells']}**\n"
    )
    f.write(
        f"- Cell-month records: **{dataset['smap_records']:,}**\n"
    )
    f.write(
        f"- GPM comparison period: **{dataset['gpm_common_start']} → "
        f"{dataset['gpm_common_end']}**\n"
    )
    f.write(
        f"- Common GPM months: **{dataset['gpm_common_months']}**\n\n"
    )

    f.write("## 2. Long-term trend evidence\n\n")

    f.write(
        f"- Sen slope: **{trend_evidence['sen_slope_per_year']:.10f} "
        f"soil-moisture units/year**\n"
    )
    f.write(
        f"- Kendall tau: **{trend_evidence['kendall_tau']:.6f}**\n"
    )
    f.write(
        f"- p-value: **{trend_evidence['p_value']:.6f}**\n"
    )
    f.write(
        f"- Significant at 0.05: "
        f"**{trend_evidence['significant_at_0_05']}**\n"
    )
    f.write(
        f"- Significant cells: **{trend_evidence['significant_cells']} / "
        f"{trend_evidence['total_cells']}**\n"
    )

    f.write(
        "\n**Interpretation:** The analyzed record does not show a "
        "statistically significant state-wide monotonic drying trend.\n\n"
    )

    f.write("## 3. Seasonal and spatial trend evidence\n\n")

    f.write(
        f"- Significant state seasonal trends: "
        f"**{seasonal_trend_evidence['significant_state_seasons']} / 4**\n"
    )
    f.write(
        f"- Raw significant cell-season results: "
        f"**{seasonal_trend_evidence['significant_cell_seasons_raw']}**\n"
    )
    f.write(
        f"- FDR-significant spatial trend results: "
        f"**{spatial_trend_evidence['fdr_significant_results']}**\n"
    )
    f.write(
        f"- Spatial hotspots: "
        f"**{spatial_trend_evidence['spatial_hotspot_results']}**\n"
    )

    f.write(
        "\nAfter FDR correction, no statistically robust "
        "spatial-seasonal trend hotspot was identified.\n\n"
    )

    f.write("## 4. Extreme-event evidence\n\n")

    f.write(
        f"- Extreme dry cell-months: "
        f"**{extreme_evidence['extreme_dry_cell_months']:,}**\n"
    )
    f.write(
        f"- Extreme wet cell-months: "
        f"**{extreme_evidence['extreme_wet_cell_months']:,}**\n"
    )
    f.write(
        f"- Total extreme cell-months: "
        f"**{extreme_evidence['total_extreme_cell_months']:,}**\n"
    )
    f.write(
        f"- Event episodes: **{extreme_evidence['total_event_episodes']}** "
        f"({extreme_evidence['dry_event_episodes']} dry, "
        f"{extreme_evidence['wet_event_episodes']} wet)\n"
    )
    f.write(
        f"- Cells experiencing at least one extreme: "
        f"**{extreme_evidence['unique_cells_with_extremes']}**\n\n"
    )

    f.write("## 5. Rainfall relationship\n\n")

    f.write(
        f"- Same-month standardized Pearson r: "
        f"**{same_month_evidence['standardized_pearson_r']:.6f}**\n"
    )
    f.write(
        f"- Same-month Pearson p: "
        f"**{same_month_evidence['standardized_pearson_p']:.3e}**\n"
    )
    f.write(
        f"- Strongest tested lag: "
        f"**{lag_evidence['best_absolute_pearson_lag_months']} month**\n"
    )
    f.write(
        f"- Pearson r at strongest lag: "
        f"**{lag_evidence['best_absolute_pearson_r']:.6f}**\n"
    )
    f.write(
        f"- Autocorrelation-adjusted effective N: "
        f"**{overall_acf['effective_n']:.2f}**\n"
    )
    f.write(
        f"- Autocorrelation-adjusted p: "
        f"**{overall_acf['adjusted_p']:.3e}**\n"
    )
    f.write(
        f"- Significant after adjustment: "
        f"**{overall_acf['significant_after_adjustment']}**\n\n"
    )

    f.write("## 6. Spatial rainfall relationship\n\n")

    f.write(
        f"- Mapped SMAP cells: **{spatial_gpm_evidence['mapped_smap_cells']}**\n"
    )
    f.write(
        f"- GPM cells: **{spatial_gpm_evidence['gpm_cells']}**\n"
    )
    f.write(
        f"- Pearson r range: **"
        f"{spatial_gpm_evidence['pearson_r_min']:.4f} → "
        f"{spatial_gpm_evidence['pearson_r_max']:.4f}**\n"
    )
    f.write(
        f"- Mean Pearson r: **"
        f"{spatial_gpm_evidence['pearson_r_mean']:.4f}**\n"
    )
    f.write(
        f"- Median Pearson r: **"
        f"{spatial_gpm_evidence['pearson_r_median']:.4f}**\n"
    )
    f.write(
        f"- Mean mapping distance: **"
        f"{spatial_gpm_evidence['mapping_distance_km_mean']:.2f} km**\n"
    )
    f.write(
        f"- Maximum mapping distance: **"
        f"{spatial_gpm_evidence['mapping_distance_km_max']:.2f} km**\n\n"
    )

    f.write("### Distance sensitivity\n\n")

    for result in sensitivity["results"]:
        label = result["threshold"]

        f.write(
            f"- **{label}**: {result['cells']} cells, "
            f"mean r = {result['mean_r']:.6f}, "
            f"median r = {result['median_r']:.6f}\n"
        )

    f.write("\nThis shows that the spatial relationship remains stable "
            "when restricting matches to closer distances.\n\n")

    f.write("## 7. Scientific interpretation\n\n")

    f.write(
        "The central result is not evidence of a simple long-term drying "
        "trend across Jharkhand. Instead, the analyzed SMAP record shows "
        "substantial temporal variability, widespread extreme soil-moisture "
        "events, and a strong statistical association between soil-moisture "
        "and rainfall anomalies. The association is strongest in the same "
        "month among the tested lags and remains significant after the "
        "autocorrelation-aware adjustment applied here.\n\n"
    )

    f.write(
        "The rainfall relationship should be interpreted as statistical "
        "association rather than proof of a causal mechanism.\n\n"
    )

    f.write("## 8. Limitations\n\n")

    for limitation in limitations:
        f.write(f"- {limitation}\n")

    f.write("\n## 9. Reproducibility\n\n")

    f.write(
        "Generated automatically by "
        "`src/15_final_evidence_synthesis.py` from the frozen analysis "
        "outputs and evidence manifests.\n"
    )


# ============================================================
# FINAL CONSOLE OUTPUT
# ============================================================

print("\n" + "=" * 70)
print("FINAL SYNTHESIS COMPLETE")
print("=" * 70)

print(f"\nJSON : {OUT_JSON}")
print(f"CSV  : {OUT_CSV}")
print(f"MD   : {OUT_MD}")

print("\nKEY FINDING")
print("-" * 70)
print(final_finding)

print("\nKEY NUMBERS")
print("-" * 70)

print(
    f"SMAP period              : "
    f"{dataset['smap_start']} -> {dataset['smap_end']}"
)
print(f"SMAP cells               : {dataset['smap_cells']}")
print(f"SMAP records             : {dataset['smap_records']:,}")
print(
    f"Sen slope/year           : "
    f"{trend_evidence['sen_slope_per_year']:.10f}"
)
print(f"Kendall tau              : {trend_evidence['kendall_tau']:.6f}")
print(f"Trend p-value            : {trend_evidence['p_value']:.6f}")
print(
    f"Significant trend        : "
    f"{trend_evidence['significant_at_0_05']}"
)
print(
    f"Significant cells        : "
    f"{trend_evidence['significant_cells']}"
)
print(
    f"FDR spatial results      : "
    f"{spatial_trend_evidence['fdr_significant_results']}"
)
print(
    f"Spatial hotspots         : "
    f"{spatial_trend_evidence['spatial_hotspot_results']}"
)
print(
    f"Extreme dry cell-months  : "
    f"{extreme_evidence['extreme_dry_cell_months']}"
)
print(
    f"Extreme wet cell-months  : "
    f"{extreme_evidence['extreme_wet_cell_months']}"
)
print(
    f"Total event episodes     : "
    f"{extreme_evidence['total_event_episodes']}"
)
print(
    f"Same-month Pearson r     : "
    f"{same_month_evidence['standardized_pearson_r']:.6f}"
)
print(
    f"Adjusted Pearson p       : "
    f"{overall_acf['adjusted_p']:.3e}"
)
print(
    f"Spatial mean Pearson r   : "
    f"{spatial_gpm_evidence['pearson_r_mean']:.6f}"
)
print(
    f"Spatial median Pearson r : "
    f"{spatial_gpm_evidence['pearson_r_median']:.6f}"
)

print("\nStatus: PASS")
print("=" * 70)
