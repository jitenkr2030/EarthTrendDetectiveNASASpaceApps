import pandas as pd
import numpy as np

INPUT = "data/smap_jharkhand_test.csv"
OUTPUT = "data/smap_jharkhand_daily_test.csv"

print("========================================")
print("EARTH TREND DETECTIVE")
print("DAILY AGGREGATION")
print("========================================")

df = pd.read_csv(INPUT)

df["time"] = pd.to_datetime(df["time"], utc=True)

df = df.sort_values("time").reset_index(drop=True)

# Use observation date in UTC
df["date"] = df["time"].dt.floor("D")

daily = (
    df.groupby("date")
    .agg(
        mean_soil_moisture=("mean_soil_moisture", "mean"),
        median_soil_moisture=("median_soil_moisture", "mean"),
        observations=("mean_soil_moisture", "count"),
        min_soil_moisture=("mean_soil_moisture", "min"),
        max_soil_moisture=("mean_soil_moisture", "max"),
        valid_cells_min=("valid_cells", "min"),
        total_cells=("total_cells", "first"),
    )
    .reset_index()
)

daily["coverage_percent"] = (
    daily["observations"] / 8 * 100
)

daily["date"] = daily["date"].dt.strftime("%Y-%m-%d")

daily.to_csv(OUTPUT, index=False)

print("\nInput observations:", len(df))
print("Daily observations:", len(daily))

print("\nDaily data:")
print(daily.to_string(index=False))

print("\nOutput:", OUTPUT)

print("\n========================================")
print("DAILY AGGREGATION COMPLETE")
print("========================================")
