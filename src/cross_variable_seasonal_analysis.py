import json
from pathlib import Path

import pandas as pd
from scipy.stats import pearsonr, spearmanr


# ============================================================
# CONFIG
# ============================================================

BASE = Path(__file__).resolve().parents[1]

SMAP_FILE = BASE / "data/analysis/smap_anomalies_jharkhand.csv"
GPM_FILE = BASE / "data/analysis/gpm_anomalies_jharkhand.csv"

OUTPUT_CSV = BASE / "data/analysis/smap_gpm_seasonal_correlation.csv"
OUTPUT_JSON = BASE / "data/analysis/smap_gpm_seasonal_correlation.json"


# ============================================================
# LOAD
# ============================================================

print("\nLoading datasets...")

smap = pd.read_csv(SMAP_FILE)
gpm = pd.read_csv(GPM_FILE)

smap["date"] = pd.to_datetime(smap["date"])
gpm["date"] = pd.to_datetime(gpm["date"])


# ============================================================
# SEASON FUNCTION
# ============================================================

def get_season(month):
    if month in [1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "pre-monsoon"
    elif month in [6, 7, 8, 9]:
        return "monsoon"
    elif month in [10, 11, 12]:
        return "post-monsoon"
    else:
        raise ValueError(f"Invalid month: {month}")


# ============================================================
# SMAP STATE MONTHLY
# ============================================================

smap_monthly = (
    smap.groupby("date", as_index=False)
    .agg(
        smap_anomaly=("anomaly", "mean"),
        smap_z=("standardized_anomaly", "mean"),
        smap_soil_moisture=("soil_moisture", "mean"),
    )
)

smap_monthly["month_number"] = (
    smap_monthly["date"].dt.month
)

smap_monthly["season"] = (
    smap_monthly["month_number"].apply(get_season)
)


# ============================================================
# GPM MONTHLY
# ============================================================

gpm_monthly = gpm[
    [
        "date",
        "rainfall_mm_month",
        "rainfall_anomaly_mm",
        "standardized_rainfall_anomaly",
    ]
].copy()

gpm_monthly = gpm_monthly.rename(
    columns={
        "rainfall_anomaly_mm": "gpm_anomaly",
        "standardized_rainfall_anomaly": "gpm_z",
    }
)

gpm_monthly["month_number"] = (
    gpm_monthly["date"].dt.month
)

gpm_monthly["season"] = (
    gpm_monthly["month_number"].apply(get_season)
)


# ============================================================
# MERGE
# ============================================================

df = pd.merge(
    smap_monthly,
    gpm_monthly,
    on=[
        "date",
        "month_number",
        "season",
    ],
    how="inner",
).sort_values("date").reset_index(drop=True)


print(f"Common monthly records: {len(df)}")

print(
    f"Period: {df['date'].min().date()} "
    f"to {df['date'].max().date()}"
)


# ============================================================
# SEASONAL CORRELATION
# ============================================================

season_order = [
    "winter",
    "pre-monsoon",
    "monsoon",
    "post-monsoon",
]

results = []

for season in season_order:

    subset = df[
        df["season"] == season
    ].dropna(
        subset=[
            "gpm_z",
            "smap_z",
        ]
    )

    x = subset["gpm_z"].to_numpy()
    y = subset["smap_z"].to_numpy()

    if len(subset) < 3:
        print(
            f"\n{season}: insufficient observations"
        )
        continue

    pearson_r, pearson_p = pearsonr(
        x,
        y,
    )

    spearman_rho, spearman_p = spearmanr(
        x,
        y,
    )

    results.append(
        {
            "season": season,
            "n": len(subset),
            "pearson_r": float(pearson_r),
            "pearson_p": float(pearson_p),
            "spearman_rho": float(spearman_rho),
            "spearman_p": float(spearman_p),
        }
    )

    print(
        f"\n{season.upper()}"
    )

    print(
        f"  n = {len(subset)}"
    )

    print(
        f"  Pearson r = {pearson_r:.6f}"
    )

    print(
        f"  Pearson p = {pearson_p:.6e}"
    )

    print(
        f"  Spearman rho = {spearman_rho:.6f}"
    )

    print(
        f"  Spearman p = {spearman_p:.6e}"
    )


# ============================================================
# RESULT TABLE
# ============================================================

results_df = pd.DataFrame(results)

print(
    "\n" + "=" * 70
)

print(
    "SEASONAL CROSS-VARIABLE CORRELATION"
)

print(
    "=" * 70
)

print(
    results_df.to_string(index=False)
)


# ============================================================
# STRONGEST SEASON
# ============================================================

best_idx = (
    results_df["pearson_r"]
    .abs()
    .idxmax()
)

best = results_df.loc[best_idx]

best_season = str(
    best["season"]
)

best_r = float(
    best["pearson_r"]
)


# ============================================================
# INTERPRETATION
# ============================================================

interpretation = (
    f"The strongest seasonal rainfall-soil-moisture "
    f"association occurs during the {best_season} season "
    f"(Pearson r = {best_r:.6f}). Seasonal correlations "
    "describe association within each season and should "
    "not be interpreted as evidence of causality."
)


# ============================================================
# SAVE CSV
# ============================================================

OUTPUT_CSV.parent.mkdir(
    parents=True,
    exist_ok=True,
)

results_df.to_csv(
    OUTPUT_CSV,
    index=False,
)


# ============================================================
# SAVE JSON
# ============================================================

result = {
    "analysis": (
        "Seasonal SMAP-GPM cross-variable correlation"
    ),

    "smap_source": str(
        SMAP_FILE.relative_to(BASE)
    ),

    "gpm_source": str(
        GPM_FILE.relative_to(BASE)
    ),

    "common_months": int(
        len(df)
    ),

    "period_start": str(
        df["date"].min().date()
    ),

    "period_end": str(
        df["date"].max().date()
    ),

    "seasons": season_order,

    "strongest_season_by_absolute_pearson": (
        best_season
    ),

    "strongest_pearson_r": best_r,

    "interpretation": interpretation,

    "results": results,
}


with open(
    OUTPUT_JSON,
    "w",
) as f:

    json.dump(
        result,
        f,
        indent=2,
    )


# ============================================================
# FINAL
# ============================================================

print(
    "\n" + "=" * 70
)

print(
    "FINAL SEASONAL FINDING"
)

print(
    "=" * 70
)

print(
    interpretation
)

print(
    "\nOutputs:"
)

print(
    f"  {OUTPUT_CSV}"
)

print(
    f"  {OUTPUT_JSON}"
)

print(
    "\nPASS — seasonal cross-variable analysis complete."
)
