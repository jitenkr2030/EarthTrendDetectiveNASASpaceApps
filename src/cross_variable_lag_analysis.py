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

OUTPUT_CSV = BASE / "data/analysis/smap_gpm_lag_correlation.csv"
OUTPUT_JSON = BASE / "data/analysis/smap_gpm_lag_correlation.json"


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading datasets...")

smap = pd.read_csv(SMAP_FILE)
gpm = pd.read_csv(GPM_FILE)

smap["date"] = pd.to_datetime(smap["date"])
gpm["date"] = pd.to_datetime(gpm["date"])


# ============================================================
# SMAP: CELL MONTHLY -> STATE MONTHLY
# ============================================================

smap_monthly = (
    smap.groupby("date", as_index=False)
    .agg(
        smap_anomaly=("anomaly", "mean"),
        smap_z=("standardized_anomaly", "mean"),
        smap_soil_moisture=("soil_moisture", "mean"),
    )
)

print(f"SMAP monthly records: {len(smap_monthly)}")


# ============================================================
# GPM: ALREADY STATE MONTHLY
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

print(f"GPM monthly records: {len(gpm_monthly)}")


# ============================================================
# COMMON PERIOD
# ============================================================

df = pd.merge(
    smap_monthly,
    gpm_monthly,
    on="date",
    how="inner",
).sort_values("date").reset_index(drop=True)

print(f"Common months: {len(df)}")

print(
    f"Period: {df['date'].min().date()} "
    f"to {df['date'].max().date()}"
)


# ============================================================
# LAG ANALYSIS
# ============================================================

results = []

for lag in [0, 1, 2, 3]:

    test = df.copy()

    # Rainfall lagged by N months:
    #
    # lag 0 = rainfall(t)   -> soil moisture(t)
    # lag 1 = rainfall(t-1) -> soil moisture(t)
    # lag 2 = rainfall(t-2) -> soil moisture(t)
    # lag 3 = rainfall(t-3) -> soil moisture(t)

    test["rainfall_lagged_z"] = test["gpm_z"].shift(lag)

    test = test.dropna(
        subset=[
            "rainfall_lagged_z",
            "smap_z",
        ]
    )

    x = test["rainfall_lagged_z"].to_numpy()
    y = test["smap_z"].to_numpy()

    pearson_r, pearson_p = pearsonr(x, y)
    spearman_rho, spearman_p = spearmanr(x, y)

    results.append(
        {
            "lag_months": lag,
            "n": len(test),
            "pearson_r": float(pearson_r),
            "pearson_p": float(pearson_p),
            "spearman_rho": float(spearman_rho),
            "spearman_p": float(spearman_p),
        }
    )

    print(f"\nLag {lag} month(s)")
    print(f"  n = {len(test)}")
    print(f"  Pearson r = {pearson_r:.6f}")
    print(f"  Pearson p = {pearson_p:.6e}")
    print(f"  Spearman rho = {spearman_rho:.6f}")
    print(f"  Spearman p = {spearman_p:.6e}")


# ============================================================
# RESULT TABLE
# ============================================================

results_df = pd.DataFrame(results)

print("\n" + "=" * 70)
print("LAG CORRELATION SUMMARY")
print("=" * 70)

print(results_df.to_string(index=False))


# ============================================================
# FIND STRONGEST ABSOLUTE CORRELATION
# ============================================================

best_idx = results_df["pearson_r"].abs().idxmax()
best = results_df.loc[best_idx]

best_lag = int(best["lag_months"])
best_r = float(best["pearson_r"])

same_month_r = float(
    results_df.loc[
        results_df["lag_months"] == 0,
        "pearson_r",
    ].iloc[0]
)


# ============================================================
# INTERPRETATION
# ============================================================

if best_lag == 0:

    interpretation = (
        "The strongest tested association occurs in the same month. "
        "Rainfall anomalies at 1–3 month lags do not exceed the "
        "same-month association."
    )

else:

    interpretation = (
        f"The strongest tested association occurs when rainfall "
        f"leads soil moisture by {best_lag} month(s). This provides "
        "additional temporal-association evidence, but does not "
        "establish causality."
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
    "analysis": "SMAP-GPM lagged cross-variable correlation",

    "smap_source": str(
        SMAP_FILE.relative_to(BASE)
    ),

    "gpm_source": str(
        GPM_FILE.relative_to(BASE)
    ),

    "common_months": int(len(df)),

    "period_start": str(
        df["date"].min().date()
    ),

    "period_end": str(
        df["date"].max().date()
    ),

    "tested_lags_months": [
        0,
        1,
        2,
        3,
    ],

    "same_month_pearson_r": same_month_r,

    "best_absolute_pearson_lag_months": best_lag,

    "best_absolute_pearson_r": best_r,

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

print("\n" + "=" * 70)
print("FINAL LAG FINDING")
print("=" * 70)

print(
    f"Same-month Pearson r : {same_month_r:.6f}"
)

print(
    f"Strongest lag        : {best_lag} month(s)"
)

print(
    f"Strongest Pearson r  : {best_r:.6f}"
)

print()

print(
    interpretation
)

print("\nOutputs:")

print(
    f"  {OUTPUT_CSV}"
)

print(
    f"  {OUTPUT_JSON}"
)

print(
    "\nPASS — lag analysis complete."
)
