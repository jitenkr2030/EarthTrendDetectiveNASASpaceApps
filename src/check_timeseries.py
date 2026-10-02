import pandas as pd
import numpy as np

INPUT = "data/smap_jharkhand_test.csv"

print("========================================")
print("EARTH TREND DETECTIVE")
print("TIME-SERIES QUALITY CHECK")
print("========================================")

df = pd.read_csv(INPUT)

df["time"] = pd.to_datetime(df["time"], utc=True)

df = df.sort_values("time").reset_index(drop=True)

print("\nRows:", len(df))
print("Columns:", list(df.columns))

print("\nTime range:")
print("Start:", df["time"].min())
print("End  :", df["time"].max())

# Time differences
delta_hours = (
    df["time"]
    .diff()
    .dt.total_seconds()
    .div(3600)
    .dropna()
)

print("\nObservation interval:")
print("Minimum:", delta_hours.min(), "hours")
print("Maximum:", delta_hours.max(), "hours")
print("Median :", delta_hours.median(), "hours")

print("\nInterval distribution:")
print(delta_hours.value_counts().sort_index())

# Soil moisture statistics
values = df["mean_soil_moisture"].to_numpy(dtype=float)

print("\nSoil moisture:")
print("Minimum:", np.min(values))
print("Maximum:", np.max(values))
print("Mean   :", np.mean(values))
print("Median :", np.median(values))
print("Std    :", np.std(values))

# Valid-cell check
print("\nSpatial validity:")

print(
    "Valid cells:",
    df["valid_cells"].min(),
    "to",
    df["valid_cells"].max()
)

print(
    "Total cells:",
    df["total_cells"].min(),
    "to",
    df["total_cells"].max()
)

all_valid = (
    df["valid_cells"] == df["total_cells"]
).all()

print(
    "Every observation fully valid:",
    all_valid
)

# Duplicate timestamps
duplicates = df["time"].duplicated().sum()

print("\nDuplicate timestamps:", duplicates)

# Missing values
missing = df["mean_soil_moisture"].isna().sum()

print("Missing soil-moisture values:", missing)

print("\n========================================")
print("QUALITY CHECK COMPLETE")
print("========================================")

if (
    len(df) > 0
    and
    all_valid
    and
    duplicates == 0
    and
    missing == 0
):
    print("STATUS: PASS")
else:
    print("STATUS: REVIEW REQUIRED")
