from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

SMAP_MASK = ROOT / "data/jharkhand_smap_mask.csv"
GPM_MASK = ROOT / "data/gpm_jharkhand_mask.csv"

OUT_FILE = ROOT / "data/analysis/smap_gpm_spatial_mapping.csv"


# ============================================================
# LOAD MASKS
# ============================================================

print("\nLoading SMAP mask...")
smap = pd.read_csv(SMAP_MASK)

print("Loading GPM mask...")
gpm = pd.read_csv(GPM_MASK)


# ============================================================
# VALIDATE COORDINATES
# ============================================================

required_smap = {"row", "col", "latitude", "longitude"}
required_gpm = {"latitude", "longitude"}

missing_smap = required_smap - set(smap.columns)
missing_gpm = required_gpm - set(gpm.columns)

if missing_smap:
    raise ValueError(
        f"SMAP mask missing columns: {sorted(missing_smap)}"
    )

if missing_gpm:
    raise ValueError(
        f"GPM mask missing columns: {sorted(missing_gpm)}"
    )


smap = smap.drop_duplicates(
    subset=["row", "col"]
).reset_index(drop=True)

gpm = gpm.drop_duplicates(
    subset=["latitude", "longitude"]
).reset_index(drop=True)


print(f"\nSMAP cells: {len(smap)}")
print(f"GPM cells:  {len(gpm)}")


# ============================================================
# NEAREST GPM CELL FOR EACH SMAP CELL
# ============================================================

gpm_lat = gpm["latitude"].to_numpy(dtype=float)
gpm_lon = gpm["longitude"].to_numpy(dtype=float)

results = []

for _, smap_row in smap.iterrows():

    lat = float(smap_row["latitude"])
    lon = float(smap_row["longitude"])

    # Simple lat/lon distance for nearby cells in Jharkhand.
    distance = np.sqrt(
        (gpm_lat - lat) ** 2
        +
        (gpm_lon - lon) ** 2
    )

    nearest_idx = int(np.argmin(distance))

    nearest_distance = float(distance[nearest_idx])

    gpm_row = gpm.iloc[nearest_idx]

    results.append(
        {
            "smap_row": int(smap_row["row"]),
            "smap_col": int(smap_row["col"]),
            "smap_latitude": lat,
            "smap_longitude": lon,
            "gpm_latitude": float(gpm_row["latitude"]),
            "gpm_longitude": float(gpm_row["longitude"]),
            "coordinate_distance_degrees": nearest_distance,
        }
    )


mapping = pd.DataFrame(results)


# ============================================================
# DISTANCE QA
# ============================================================

print("\nSpatial mapping QA")

print(
    f"Mappings created: "
    f"{len(mapping)}"
)

print(
    f"Minimum distance: "
    f"{mapping['coordinate_distance_degrees'].min():.6f}°"
)

print(
    f"Mean distance:    "
    f"{mapping['coordinate_distance_degrees'].mean():.6f}°"
)

print(
    f"Maximum distance: "
    f"{mapping['coordinate_distance_degrees'].max():.6f}°"
)


# Approximate conversion.
# Around Jharkhand, 1 degree latitude is approximately 111 km.
mapping["approx_distance_km"] = (
    mapping["coordinate_distance_degrees"] * 111.0
)


print(
    f"Mean distance:    "
    f"{mapping['approx_distance_km'].mean():.2f} km"
)

print(
    f"Maximum distance: "
    f"{mapping['approx_distance_km'].max():.2f} km"
)


# ============================================================
# DUPLICATE GPM ASSIGNMENT QA
# ============================================================

gpm_usage = (
    mapping.groupby(
        ["gpm_latitude", "gpm_longitude"]
    )
    .size()
    .reset_index(name="smap_cells_assigned")
)

print(
    "\nGPM cells receiving SMAP assignments: "
    f"{len(gpm_usage)}"
)

print(
    "Maximum SMAP cells mapped to one GPM cell: "
    f"{gpm_usage['smap_cells_assigned'].max()}"
)


# ============================================================
# SAVE
# ============================================================

mapping.to_csv(
    OUT_FILE,
    index=False,
)


print("\n" + "=" * 72)
print("SPATIAL MAPPING COMPLETE")
print("=" * 72)

print(f"Output: {OUT_FILE}")

print("\nFirst 5 mappings:")
print(mapping.head().to_string(index=False))

print("\nDONE.")
