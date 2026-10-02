import pandas as pd

INPUT = "data/smap_granule_inventory.csv"

print("========================================")
print("EARTH TREND DETECTIVE")
print("GRANULE INVENTORY CHECK")
print("========================================")

df = pd.read_csv(INPUT)

df["time_start"] = pd.to_datetime(df["time_start"], utc=True)

df = df.sort_values("time_start").reset_index(drop=True)

print("\nTotal granules:", len(df))

print("\nTime range:")
print("Start:", df["time_start"].min())
print("End  :", df["time_start"].max())

# Duplicate timestamps
duplicate_times = df["time_start"].duplicated().sum()

print("\nDuplicate time_start values:", duplicate_times)

# Duplicate titles
duplicate_titles = df["title"].duplicated().sum()

print("Duplicate titles:", duplicate_titles)

# Monthly distribution
df["month"] = df["time_start"].dt.strftime("%Y-%m")

monthly = df.groupby("month").size()

print("\nMonthly granule counts:")
print(monthly.to_string())

print("\nMonthly statistics:")
print("Minimum:", monthly.min())
print("Maximum:", monthly.max())
print("Median :", monthly.median())

# Time differences
delta_hours = (
    df["time_start"]
    .diff()
    .dt.total_seconds()
    .div(3600)
    .dropna()
)

print("\nTime interval statistics:")
print("Minimum:", delta_hours.min(), "hours")
print("Maximum:", delta_hours.max(), "hours")
print("Median :", delta_hours.median(), "hours")

print("\nInterval distribution:")
print(delta_hours.value_counts().sort_index().head(20))

print("\n========================================")
print("INVENTORY CHECK COMPLETE")
print("========================================")

if duplicate_times == 0 and duplicate_titles == 0:
    print("STATUS: PASS")
else:
    print("STATUS: REVIEW REQUIRED")
