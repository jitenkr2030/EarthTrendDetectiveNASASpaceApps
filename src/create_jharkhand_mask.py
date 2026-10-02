import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

BOUNDARY = "data/boundaries/india_adm1/IND_ADM1.geojson"

INPUT = "data/smap_jharkhand_2015_04_spatial.csv"

OUTPUT = "data/smap_jharkhand_2015_04_masked.csv"

print("========================================")
print("EARTH TREND DETECTIVE")
print("JHARKHAND SPATIAL MASK")
print("========================================")

# --------------------------------------------------
# Load state boundaries
# --------------------------------------------------

states = gpd.read_file(BOUNDARY)

jharkhand = states[
    states["NAME"].str.strip().str.lower() == "jharkhand"
].copy()

if len(jharkhand) != 1:
    raise RuntimeError(
        f"Expected exactly 1 Jharkhand polygon, found {len(jharkhand)}"
    )

print("\nJharkhand polygon found.")

print("CRS:", jharkhand.crs)

# --------------------------------------------------
# Load NASA spatial grid
# --------------------------------------------------

df = pd.read_csv(INPUT)

print("\nInput cells:", len(df))

# --------------------------------------------------
# Create cell-center GeoDataFrame
# --------------------------------------------------

geometry = [
    Point(lon, lat)
    for lon, lat in zip(
        df["longitude"],
        df["latitude"]
    )
]

cells = gpd.GeoDataFrame(
    df,
    geometry=geometry,
    crs="EPSG:4326"
)

# --------------------------------------------------
# Spatial mask
# --------------------------------------------------

jharkhand_geometry = jharkhand.geometry.union_all()

inside = cells.geometry.within(
    jharkhand_geometry
)

cells["inside_jharkhand"] = inside

# --------------------------------------------------
# Keep only cells inside Jharkhand
# --------------------------------------------------

masked = cells[
    cells["inside_jharkhand"]
].copy()

masked = masked.drop(
    columns=["geometry"]
)

# --------------------------------------------------
# Save
# --------------------------------------------------

masked.to_csv(
    OUTPUT,
    index=False
)

# --------------------------------------------------
# Statistics
# --------------------------------------------------

inside_count = int(inside.sum())
outside_count = int((~inside).sum())

print("\n========================================")
print("MASK RESULTS")
print("========================================")

print("Input cells:", len(df))
print("Inside Jharkhand:", inside_count)
print("Outside Jharkhand:", outside_count)

print(
    "Percentage inside:",
    round(
        inside_count / len(df) * 100,
        2
    ),
    "%"
)

print("\nOutput:", OUTPUT)

print("\n========================================")
print("MASK COMPLETE")
print("========================================")
