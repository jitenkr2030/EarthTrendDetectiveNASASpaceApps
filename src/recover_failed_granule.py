#!/usr/bin/env python3

import os
import numpy as np
import pandas as pd
from pydap.client import open_url


R1, R2 = 465, 509
C1, C2 = 2820, 2870

SM_PATH = "/Geophysical_Data/sm_surface"

MONTH = "2015-05"

CHECKPOINT = f"data/checkpoints/{MONTH}.npz"
OUTPUT = f"data/monthly/{MONTH}.csv"

MASK_FILE = "data/jharkhand_smap_mask.csv"

URL = (
    "https://opendap.earthdata.nasa.gov/"
    "collections/C3480440870-NSIDC_CPRD/granules/"
    "SMAP_L4_SM_gph_20150526T163000_Vv8010_001.h5"
)

EXPECTED_CELLS = 984


print("=" * 70)
print("EarthTrend Detective — Failed Granule Recovery")
print("=" * 70)

# ---------------------------------------------------------
# Load checkpoint
# ---------------------------------------------------------

if not os.path.exists(CHECKPOINT):
    raise FileNotFoundError(
        f"Checkpoint not found: {CHECKPOINT}"
    )

checkpoint = np.load(CHECKPOINT)

next_index = int(checkpoint["next_index"][0])

sums = checkpoint["sums"].copy()
counts = checkpoint["counts"].copy()

print(f"Checkpoint next_index: {next_index}")
print(f"Cells in checkpoint:   {len(sums)}")

if len(sums) != EXPECTED_CELLS:
    raise ValueError(
        "Checkpoint does not contain 984 cells."
    )

# ---------------------------------------------------------
# Safety check
# ---------------------------------------------------------

if np.any(counts != 247):
    raise ValueError(
        "Expected every cell to have exactly "
        "247 observations before recovery."
    )

# ---------------------------------------------------------
# Load mask
# ---------------------------------------------------------

mask = pd.read_csv(MASK_FILE)

if len(mask) != EXPECTED_CELLS:
    raise ValueError(
        f"Expected {EXPECTED_CELLS} mask cells, "
        f"found {len(mask)}"
    )

rr = (
    mask["row"].to_numpy(dtype=int)
    - R1
)

cc = (
    mask["col"].to_numpy(dtype=int)
    - C1
)

# ---------------------------------------------------------
# Read recovered NASA granule
# ---------------------------------------------------------

print("\nOpening recovered granule...")

ds = open_url(URL)

values = np.asarray(
    ds[SM_PATH][R1:R2, C1:C2]
).squeeze()

if values.shape != (R2 - R1, C2 - C1):
    raise ValueError(
        f"Unexpected shape: {values.shape}"
    )

selected = values[rr, cc].astype(
    np.float64,
    copy=False
)

valid = (
    np.isfinite(selected)
    & (selected >= 0.0)
    & (selected <= 0.9)
)

print(f"Grid shape:     {values.shape}")
print(f"Selected cells: {len(selected)}")
print(f"Valid cells:    {int(valid.sum())}")
print(f"Invalid cells:  {int((~valid).sum())}")

if not valid.all():
    raise ValueError(
        "Recovered granule does not contain "
        "valid data for all 984 cells."
    )

# ---------------------------------------------------------
# Add recovered observation
# ---------------------------------------------------------

sums[valid] += selected[valid]
counts[valid] += 1

# ---------------------------------------------------------
# Verify
# ---------------------------------------------------------

if not np.all(counts == 248):
    raise ValueError(
        "Recovery did not produce 248 observations "
        "for every cell."
    )

# ---------------------------------------------------------
# Save corrected checkpoint
# ---------------------------------------------------------

np.savez_compressed(
    CHECKPOINT,
    next_index=np.array([248]),
    sums=sums,
    counts=counts,
)

print("\nCheckpoint updated.")

# ---------------------------------------------------------
# Rebuild monthly CSV
# ---------------------------------------------------------

monthly_mean = sums / counts

output = mask.copy()

output["month"] = MONTH
output["soil_moisture_mean"] = monthly_mean
output["observations"] = counts
output["expected_observations"] = 248
output["coverage_fraction"] = counts / 248

output.to_csv(
    OUTPUT,
    index=False
)

print("\n" + "=" * 70)
print("RECOVERY COMPLETE")
print("=" * 70)

print(f"Month:                 {MONTH}")
print("Original observations: 247")
print("Recovered:              1")
print("Final observations:    248")
print(f"Cells:                 {len(output)}")
print(
    f"Observation min:      {counts.min()}"
)
print(
    f"Observation max:      {counts.max()}"
)
print(
    f"Coverage min:         "
    f"{(counts / 248).min():.6f}"
)
print(
    f"Coverage max:         "
    f"{(counts / 248).max():.6f}"
)
print(
    f"Monthly mean:         "
    f"{monthly_mean.mean():.8f}"
)

print(f"\nOutput: {OUTPUT}")
print(f"Checkpoint: {CHECKPOINT}")

print("=" * 70)
print("STATUS: PASS")
print("=" * 70)
