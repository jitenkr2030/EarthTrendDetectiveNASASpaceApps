import pandas as pd
import numpy as np

INPUT = "data/smap_jharkhand_test.csv"
OUTPUT = "data/smap_jharkhand_monthly_test.csv"

print("========================================")
print("EARTH TREND DETECTIVE")
print("MONTHLY AGGREGATION")
print("========================================")

df = pd.read_csv(INPUT)

df["time"] = pd.to_datetime(df["time"], utc=True)

df = df.sort_values("time").reset_index(drop=True)

# Month represented by the first day of that month
df["month"] = df["time"].dt.to_period("M").dt.to_timestamp()

monthly = (
    df.groupby("month")
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

monthly["month"] = monthly["month"].dt.strftime("%Y-%m")

monthly.to_csv(OUTPUT, index=False)

print("\nInput observations:", len(df))
print("Monthly observations:", len(monthly))

print("\nMonthly data:")
print(monthly.to_string(index=False))

print("\nOutput:", OUTPUT)

print("\n========================================")
print("MONTHLY AGGREGATION COMPLETE")
print("========================================")
