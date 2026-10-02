import pandas as pd
from pathlib import Path

INPUT = Path("data/smap_jharkhand_2015_04_masked.csv")
OUTPUT = Path("data/jharkhand_smap_mask.csv")

df = pd.read_csv(INPUT)

required = ["row", "col", "latitude", "longitude"]

missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Missing columns: {missing}")

mask = (
    df[required]
    .drop_duplicates(subset=["row", "col"])
    .sort_values(["row", "col"])
    .reset_index(drop=True)
)

if len(mask) != 984:
    raise ValueError(
        f"Expected 984 Jharkhand cells, found {len(mask)}"
    )

if mask[["row", "col"]].duplicated().any():
    raise ValueError("Duplicate row/col cells found")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
mask.to_csv(OUTPUT, index=False)

print("MASTER MASK CREATED")
print(f"File: {OUTPUT}")
print(f"Cells: {len(mask)}")
print(f"Rows: {mask['row'].min()} - {mask['row'].max()}")
print(f"Cols: {mask['col'].min()} - {mask['col'].max()}")
print(f"Latitude: {mask['latitude'].min():.6f} - {mask['latitude'].max():.6f}")
print(f"Longitude: {mask['longitude'].min():.6f} - {mask['longitude'].max():.6f}")
print("Duplicate cells:", mask[["row", "col"]].duplicated().sum())
