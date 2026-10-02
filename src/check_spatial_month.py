import pandas as pd
import numpy as np

INPUT = "data/smap_jharkhand_2015_04_spatial.csv"

print("========================================")
print("EARTH TREND DETECTIVE")
print("SPATIAL MONTH QUALITY CHECK")
print("========================================")

df = pd.read_csv(INPUT)

print("\nRows:", len(df))
print("Columns:", list(df.columns))

print("\nMonth:")
print(df["month"].unique())

print("\nGrid:")
print("Rows:", df["row"].nunique())
print("Columns:", df["col"].nunique())
print("Total cells:", len(df))

print("\nObservation coverage:")
print("Minimum observations:", df["observations"].min())
print("Maximum observations:", df["observations"].max())
print("Median observations:", df["observations"].median())

print("\nMissing soil-moisture cells:")
print(df["mean_soil_moisture"].isna().sum())

print("\nLatitude:")
print("Minimum:", df["latitude"].min())
print("Maximum:", df["latitude"].max())

print("\nLongitude:")
print("Minimum:", df["longitude"].min())
print("Maximum:", df["longitude"].max())

values = df["mean_soil_moisture"].to_numpy(dtype=float)

print("\nSoil moisture:")
print("Minimum:", np.nanmin(values))
print("Maximum:", np.nanmax(values))
print("Mean:", np.nanmean(values))
print("Median:", np.nanmedian(values))
print("Std:", np.nanstd(values))

print("\nDuplicate grid cells:")

duplicates = df.duplicated(
    subset=["row", "col"]
).sum()

print(duplicates)

print("\n========================================")
print("SPATIAL QUALITY CHECK COMPLETE")
print("========================================")

if (
    len(df) == 2200
    and df["mean_soil_moisture"].notna().all()
    and df["observations"].min() > 0
    and duplicates == 0
):
    print("STATUS: PASS")
else:
    print("STATUS: REVIEW REQUIRED")
