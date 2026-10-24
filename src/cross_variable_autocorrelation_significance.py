import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr, t


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

SMAP_FILE = ROOT / "data/analysis/smap_anomalies_jharkhand.csv"
GPM_FILE = ROOT / "data/analysis/gpm_anomalies_jharkhand.csv"

OUT_CSV = ROOT / "data/analysis/smap_gpm_autocorrelation_significance.csv"
OUT_JSON = ROOT / "data/analysis/smap_gpm_autocorrelation_significance.json"


# ============================================================
# SETTINGS
# ============================================================

ALPHA = 0.05

SEASONS = {
    "winter": [1, 2],
    "pre-monsoon": [3, 4, 5],
    "monsoon": [6, 7, 8, 9],
    "post-monsoon": [10, 11, 12],
}


# ============================================================
# HELPERS
# ============================================================

def lag1_autocorrelation(values):
    """
    Pearson correlation between consecutive observations.
    """
    values = np.asarray(values, dtype=float)

    if len(values) < 3:
        return np.nan

    x = values[:-1]
    y = values[1:]

    if np.std(x) == 0 or np.std(y) == 0:
        return np.nan

    return float(np.corrcoef(x, y)[0, 1])


def effective_sample_size(n, r1_x, r1_y):
    """
    Approximate effective sample size for correlation between
    two autocorrelated time series.

    N_eff = N * (1 - r1_x*r1_y) / (1 + r1_x*r1_y)
    """

    if not np.isfinite(r1_x) or not np.isfinite(r1_y):
        return float(n)

    product = r1_x * r1_y

    denominator = 1.0 + product

    if denominator <= 0:
        return 3.0

    n_eff = n * (1.0 - product) / denominator

    # Keep enough degrees of freedom for a t-test.
    return float(max(3.0, min(n, n_eff)))


def adjusted_pvalue(r, n_eff):
    """
    Convert correlation coefficient to a t statistic using
    effective sample size rather than raw sample size.
    """

    if not np.isfinite(r) or n_eff <= 2:
        return np.nan

    if abs(r) >= 1:
        return 0.0

    t_stat = r * np.sqrt(
        (n_eff - 2.0) / (1.0 - r ** 2)
    )

    df = n_eff - 2.0

    return float(2.0 * t.sf(abs(t_stat), df))


def correlation_result(label, x, y):
    """
    Calculate raw and autocorrelation-aware correlation statistics.
    """

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    valid = np.isfinite(x) & np.isfinite(y)

    x = x[valid]
    y = y[valid]

    n = len(x)

    if n < 4:
        return {
            "analysis": label,
            "n": n,
            "pearson_r": np.nan,
            "raw_p": np.nan,
            "spearman_rho": np.nan,
            "spearman_p": np.nan,
            "rainfall_lag1_acf": np.nan,
            "soil_moisture_lag1_acf": np.nan,
            "effective_n": np.nan,
            "adjusted_p": np.nan,
            "significant_after_adjustment": False,
        }

    pearson_r, raw_p = pearsonr(x, y)
    spearman_rho, spearman_p = spearmanr(x, y)

    rainfall_acf = lag1_autocorrelation(x)
    soil_acf = lag1_autocorrelation(y)

    n_eff = effective_sample_size(
        n,
        rainfall_acf,
        soil_acf,
    )

    adj_p = adjusted_pvalue(
        pearson_r,
        n_eff,
    )

    return {
        "analysis": label,
        "n": n,
        "pearson_r": float(pearson_r),
        "raw_p": float(raw_p),
        "spearman_rho": float(spearman_rho),
        "spearman_p": float(spearman_p),
        "rainfall_lag1_acf": float(rainfall_acf),
        "soil_moisture_lag1_acf": float(soil_acf),
        "effective_n": float(n_eff),
        "adjusted_p": float(adj_p),
        "significant_after_adjustment": bool(
            np.isfinite(adj_p) and adj_p < ALPHA
        ),
    }


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading SMAP anomaly data...")
smap = pd.read_csv(SMAP_FILE)

print("Loading GPM anomaly data...")
gpm = pd.read_csv(GPM_FILE)


# ============================================================
# PREPARE SMAP
# ============================================================

smap["date"] = pd.to_datetime(smap["date"])

smap_monthly = (
    smap.groupby("date", as_index=False)
    .agg(
        soil_moisture_anomaly=(
            "standardized_anomaly",
            "mean",
        )
    )
)

smap_monthly["month_number"] = smap_monthly["date"].dt.month


# ============================================================
# PREPARE GPM
# ============================================================

gpm["date"] = pd.to_datetime(gpm["date"])

gpm_monthly = gpm[
    [
        "date",
        "standardized_rainfall_anomaly",
    ]
].copy()

gpm_monthly["month_number"] = gpm_monthly["date"].dt.month


# ============================================================
# MERGE
# ============================================================

common = pd.merge(
    smap_monthly,
    gpm_monthly,
    on=["date", "month_number"],
    how="inner",
)

common = common.sort_values("date").reset_index(drop=True)

print("\nCommon monthly dataset:")
print(f"  Records: {len(common)}")
print(f"  Start:   {common['date'].min().date()}")
print(f"  End:     {common['date'].max().date()}")


# ============================================================
# OVERALL MONTHLY ANALYSIS
# ============================================================

results = []

overall = correlation_result(
    "overall_monthly",
    common["standardized_rainfall_anomaly"],
    common["soil_moisture_anomaly"],
)

results.append(overall)


# ============================================================
# SEASON-YEAR AGGREGATION
# ============================================================

common["season"] = common["month_number"].map(
    lambda m: next(
        season
        for season, months in SEASONS.items()
        if m in months
    )
)

common["season_year"] = common["date"].dt.year


season_year = (
    common.groupby(
        ["season", "season_year"],
        as_index=False,
    )
    .agg(
        rainfall_anomaly=(
            "standardized_rainfall_anomaly",
            "mean",
        ),
        soil_moisture_anomaly=(
            "soil_moisture_anomaly",
            "mean",
        ),
        months_present=(
            "month_number",
            "count",
        ),
    )
)


# Only complete seasons are used.
complete_season_rows = []

for season, months in SEASONS.items():

    required_months = len(months)

    subset = season_year[
        (season_year["season"] == season)
        & (season_year["months_present"] == required_months)
    ].copy()

    complete_season_rows.append(subset)


complete_seasons = pd.concat(
    complete_season_rows,
    ignore_index=True,
)


# ============================================================
# SEASONAL AUTOCORRELATION-AWARE ANALYSIS
# ============================================================

for season in SEASONS:

    subset = complete_seasons[
        complete_seasons["season"] == season
    ].sort_values("season_year")

    result = correlation_result(
        f"season_{season}",
        subset["rainfall_anomaly"],
        subset["soil_moisture_anomaly"],
    )

    result["complete_seasons"] = int(len(subset))

    if len(subset) > 0:
        result["season_year_start"] = int(
            subset["season_year"].min()
        )
        result["season_year_end"] = int(
            subset["season_year"].max()
        )
    else:
        result["season_year_start"] = None
        result["season_year_end"] = None

    results.append(result)


# ============================================================
# SAVE RESULTS
# ============================================================

results_df = pd.DataFrame(results)

results_df.to_csv(
    OUT_CSV,
    index=False,
)


manifest = {
    "analysis": "Autocorrelation-aware significance of SMAP-GPM correlation",
    "alpha": ALPHA,
    "method": {
        "lag1_autocorrelation": (
            "Pearson correlation between consecutive observations"
        ),
        "effective_sample_size": (
            "N * (1-r1_x*r1_y) / (1+r1_x*r1_y)"
        ),
        "adjusted_significance": (
            "Correlation t-test using effective sample size"
        ),
    },
    "overall_period": {
        "start": str(common["date"].min().date()),
        "end": str(common["date"].max().date()),
        "records": int(len(common)),
    },
    "seasonal_method": (
        "Season-year means using complete seasons only"
    ),
    "results": results,
}

with open(OUT_JSON, "w") as f:
    json.dump(
        manifest,
        f,
        indent=2,
    )


# ============================================================
# PRINT RESULTS
# ============================================================

print("\n" + "=" * 72)
print("AUTOCORRELATION-AWARE SIGNIFICANCE")
print("=" * 72)

for row in results:

    print(f"\n{row['analysis']}")

    print(f"  N:                  {row['n']}")
    print(f"  Pearson r:          {row['pearson_r']:.6f}")
    print(f"  Raw p:              {row['raw_p']:.6e}")

    print(
        f"  Rainfall lag-1 ACF: "
        f"{row['rainfall_lag1_acf']:.6f}"
    )

    print(
        f"  Soil-moisture ACF:  "
        f"{row['soil_moisture_lag1_acf']:.6f}"
    )

    print(
        f"  Effective N:        "
        f"{row['effective_n']:.2f}"
    )

    print(
        f"  Adjusted p:         "
        f"{row['adjusted_p']:.6e}"
    )

    print(
        f"  Significant:        "
        f"{row['significant_after_adjustment']}"
    )

    if "complete_seasons" in row:
        print(
            f"  Complete seasons:   "
            f"{row['complete_seasons']}"
        )


print("\n" + "=" * 72)
print("FILES")
print("=" * 72)

print(f"CSV:  {OUT_CSV}")
print(f"JSON: {OUT_JSON}")

print("\nDONE.")
