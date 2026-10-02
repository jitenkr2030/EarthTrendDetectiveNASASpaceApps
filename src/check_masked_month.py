import pandas as pd

FILE = "data/smap_jharkhand_2015_04_masked_v2.csv"

df = pd.read_csv(FILE)

print("=== MASKED MONTH VALIDATION ===")
print("Rows:", len(df))
print("Unique cells:", df[["row", "col"]].drop_duplicates().shape[0])
print("Duplicate cells:", df[["row", "col"]].duplicated().sum())

print("Month:", df["month"].unique())

print(
    "Observations min/max:",
    df["observations"].min(),
    df["observations"].max()
)

print(
    "Missing soil moisture:",
    df["soil_moisture_mean"].isna().sum()
)

print(
    "Latitude:",
    round(df["latitude"].min(), 6),
    "-",
    round(df["latitude"].max(), 6)
)

print(
    "Longitude:",
    round(df["longitude"].min(), 6),
    "-",
    round(df["longitude"].max(), 6)
)

print(
    "Soil moisture mean:",
    round(df["soil_moisture_mean"].mean(), 8)
)

print(
    "Soil moisture min:",
    round(df["soil_moisture_mean"].min(), 8)
)

print(
    "Soil moisture max:",
    round(df["soil_moisture_mean"].max(), 8)
)

checks = [
    len(df) == 984,
    df[["row", "col"]].drop_duplicates().shape[0] == 984,
    df[["row", "col"]].duplicated().sum() == 0,
    df["observations"].min() == 240,
    df["observations"].max() == 240,
    df["soil_moisture_mean"].isna().sum() == 0,
]

print()
print("STATUS:", "PASS" if all(checks) else "FAIL")
