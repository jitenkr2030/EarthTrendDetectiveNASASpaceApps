from pathlib import Path
import pandas as pd


BASE = Path("/root/earthtrend-detective")
ANALYSIS = BASE / "data" / "analysis"

SMAP_FILE = ANALYSIS / "smap_monthly_jharkhand.csv"
ANOMALY_FILE = ANALYSIS / "smap_anomalies_jharkhand.csv"

OUT_FILE = ANALYSIS / "earthtrend_timeline.csv"


print("\n" + "=" * 70)
print("EARTH TREND DETECTIVE — TIMELINE EVIDENCE")
print("=" * 70)


# ============================================================
# LOAD
# ============================================================

print("\nLoading source data...")

smap = pd.read_csv(SMAP_FILE)
anom = pd.read_csv(ANOMALY_FILE)

print(f"SMAP rows   : {len(smap):,}")
print(f"Anomaly rows: {len(anom):,}")


# ============================================================
# DATE
# ============================================================

smap["date"] = pd.to_datetime(smap["date"])
anom["date"] = pd.to_datetime(anom["date"])


# ============================================================
# STATE-LEVEL MONTHLY SOIL MOISTURE
# ============================================================

print("\nBuilding state-level monthly soil-moisture timeline...")

state = (
    smap.groupby(
        ["date", "year", "month_number", "season"],
        as_index=False
    )
    .agg(
        soil_moisture_mean=("soil_moisture", "mean"),
        soil_moisture_min=("soil_moisture", "min"),
        soil_moisture_max=("soil_moisture", "max"),
        cells=("soil_moisture", "count"),
    )
)


# ============================================================
# STATE-LEVEL ANOMALY
# ============================================================

print("Building state-level anomaly timeline...")

anom_state = (
    anom.groupby(
        ["date", "year", "month_number"],
        as_index=False
    )
    .agg(
        climatology_mean=("climatology_mean", "mean"),
        climatology_std=("climatology_std", "mean"),
        anomaly=("anomaly", "mean"),
        standardized_anomaly=("standardized_anomaly", "mean"),
    )
)


# ============================================================
# ANOMALY CLASS
# ============================================================

def classify_anomaly(z):
    if z <= -2:
        return "extremely dry"
    elif z <= -1.5:
        return "very dry"
    elif z <= -1:
        return "dry"
    elif z < 1:
        return "near normal"
    elif z < 1.5:
        return "wet"
    elif z < 2:
        return "very wet"
    else:
        return "extremely wet"


anom_state["anomaly_class"] = (
    anom_state["standardized_anomaly"]
    .apply(classify_anomaly)
)


# ============================================================
# MERGE
# ============================================================

print("Combining timeline evidence...")

timeline = state.merge(
    anom_state,
    on=["date", "year", "month_number"],
    how="left",
)


# ============================================================
# VALIDATION
# ============================================================

expected_months = 138

print("\nValidation")
print("-" * 70)

print(f"Timeline rows       : {len(timeline)}")
print(f"Expected months     : {expected_months}")

print(
    f"Date range          : "
    f"{timeline['date'].min().date()} -> "
    f"{timeline['date'].max().date()}"
)

print(
    f"Missing soil moisture: "
    f"{timeline['soil_moisture_mean'].isna().sum()}"
)

print(
    f"Missing anomaly      : "
    f"{timeline['anomaly'].isna().sum()}"
)

print(
    f"Missing z-score      : "
    f"{timeline['standardized_anomaly'].isna().sum()}"
)

print(
    f"Missing climatology  : "
    f"{timeline['climatology_mean'].isna().sum()}"
)


assert len(timeline) == expected_months
assert timeline["soil_moisture_mean"].notna().all()
assert timeline["anomaly"].notna().all()
assert timeline["standardized_anomaly"].notna().all()
assert timeline["climatology_mean"].notna().all()


# ============================================================
# ORDER
# ============================================================

timeline = (
    timeline
    .sort_values("date")
    .reset_index(drop=True)
)


# ============================================================
# SAVE
# ============================================================

timeline.to_csv(
    OUT_FILE,
    index=False,
    float_format="%.8f",
)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("TIMELINE EVIDENCE COMPLETE")
print("=" * 70)

print(f"\nOutput:")
print(OUT_FILE)

print("\nColumns:")
for column in timeline.columns:
    print(f"  - {column}")

print("\nFirst 5 months:")
print(
    timeline.head(5).to_string(index=False)
)

print("\nLast 5 months:")
print(
    timeline.tail(5).to_string(index=False)
)

print("\nSoil-moisture range:")
print(
    f"  min = {timeline['soil_moisture_mean'].min():.6f}"
)
print(
    f"  max = {timeline['soil_moisture_mean'].max():.6f}"
)

print("\nStandardized anomaly range:")
print(
    f"  min = {timeline['standardized_anomaly'].min():.3f}"
)
print(
    f"  max = {timeline['standardized_anomaly'].max():.3f}"
)

print("\nStatus: PASS")
print("=" * 70)
