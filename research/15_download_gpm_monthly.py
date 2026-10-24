from pathlib import Path
import json
import time
import requests
import pandas as pd
import numpy as np


# ============================================================
# MODULE 15A — GPM IMERG MONTHLY PRECIPITATION
# ============================================================

BASE = Path(__file__).resolve().parents[1]

MASK_FILE = BASE / "data" / "jharkhand_smap_mask.csv"

OUT_DIR = BASE / "data" / "cross_variable" / "gpm_monthly"
MANIFEST = BASE / "data" / "cross_variable" / "gpm_monthly_manifest.json"

START = pd.Timestamp("2015-04-01")
END = pd.Timestamp("2025-09-01")

# GPM IMERG Final Monthly V07
# 0.1 degree
BASE_URL = (
    "https://goldsmr4.gesdisc.eosdis.nasa.gov"
    "/opendap/GPM_3IMERGM.07"
)

EXPECTED_MONTHS = (
    pd.period_range(
        START,
        END,
        freq="M"
    )
)

# ============================================================
# IMPORTANT
# ============================================================
#
# GPM monthly files contain global 0.1 degree grids.
#
# We do NOT download the whole global grid.
#
# We first identify the latitude/longitude indices covering
# the Jharkhand SMAP cells, then request only the small spatial
# subset through OPeNDAP.
#
# ============================================================


def fail(msg):
    raise RuntimeError(msg)


def atomic_json(payload, path):
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp = path.with_suffix(".tmp")

    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)

    tmp.replace(path)


def get_url(month):
    """
    GES DISC monthly IMERG OPeNDAP naming.

    Example:
    2025-07 ->
    GPM_3IMERGM.07:3B-MO.MS.MRG.3IMERG.
    20250701-S000000-E235959.07.V07B.HDF5
    """

    stamp = month.strftime("%Y%m01")

    filename = (
        "GPM_3IMERGM.07:"
        f"3B-MO.MS.MRG.3IMERG."
        f"{stamp}-S000000-E235959.07.V07B.HDF5"
    )

    return (
        f"{BASE_URL}/"
        f"{month.year:04d}/"
        f"{month.month:02d}/"
        f"{filename}"
    )


# ============================================================
# 1. LOAD SMAP MASK
# ============================================================

print("=" * 70)
print("MODULE 15A — GPM MONTHLY PRECIPITATION")
print("=" * 70)

print("\n[1/7] Loading Jharkhand SMAP spatial mask...")

if not MASK_FILE.exists():
    fail(f"Mask not found: {MASK_FILE}")

mask = pd.read_csv(MASK_FILE)

required = [
    "row",
    "col",
    "latitude",
    "longitude",
]

missing = [
    c for c in required
    if c not in mask.columns
]

if missing:
    fail(f"Mask missing columns: {missing}")

mask["latitude"] = pd.to_numeric(
    mask["latitude"],
    errors="coerce"
)

mask["longitude"] = pd.to_numeric(
    mask["longitude"],
    errors="coerce"
)

mask = mask.dropna(
    subset=["latitude", "longitude"]
)

print(f"SMAP cells: {len(mask)}")

if len(mask) != 984:
    fail(
        f"Expected 984 SMAP cells, found {len(mask)}"
    )


# ============================================================
# 2. DEFINE GPM SPATIAL WINDOW
# ============================================================

print("\n[2/7] Defining GPM spatial window...")

lat_min = float(mask["latitude"].min())
lat_max = float(mask["latitude"].max())

lon_min = float(mask["longitude"].min())
lon_max = float(mask["longitude"].max())

# Small padding around the SMAP footprint.
PAD = 0.5

print(
    f"Latitude range:  {lat_min:.4f} → {lat_max:.4f}"
)

print(
    f"Longitude range: {lon_min:.4f} → {lon_max:.4f}"
)

print(
    f"Requested padded range: "
    f"{lat_min-PAD:.4f} → {lat_max+PAD:.4f}, "
    f"{lon_min-PAD:.4f} → {lon_max+PAD:.4f}"
)


# ============================================================
# 3. TEST FIRST GRANULE
# ============================================================

print("\n[3/7] Testing NASA GPM OPeNDAP access...")

test_month = EXPECTED_MONTHS[0].to_timestamp()

test_url = get_url(test_month)

print("Test URL:")
print(test_url)

try:
    response = requests.get(
        test_url + ".dds",
        timeout=60,
    )

    print(
        f"HTTP status: {response.status_code}"
    )

    if response.status_code != 200:
        print(response.text[:1000])
        fail(
            "NASA OPeNDAP DDS request failed."
        )

    dds = response.text

except Exception as e:
    fail(
        "Could not access GPM OPeNDAP.\n"
        f"{type(e).__name__}: {e}"
    )

print("\nDDS received successfully.")

# Detect likely precipitation variable names.
print("\nRelevant variables detected:")

for line in dds.splitlines():
    low = line.lower()

    if (
        "precipitation" in low
        or "lat" in low
        or "lon" in low
        or "time" in low
    ):
        print(line)


# ============================================================
# 4. CHECK FILE INVENTORY
# ============================================================

print("\n[4/7] Preparing monthly inventory...")

OUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

inventory = []

for period in EXPECTED_MONTHS:

    month = period.to_timestamp()

    output = (
        OUT_DIR /
        f"{month.strftime('%Y-%m')}.csv"
    )

    inventory.append(
        {
            "month": month.strftime("%Y-%m"),
            "url": get_url(month),
            "output": str(output),
            "status": (
                "complete"
                if output.exists()
                else "pending"
            ),
        }
    )

inventory_df = pd.DataFrame(inventory)

print(
    f"Expected rainfall months: "
    f"{len(inventory_df)}"
)

print(
    f"Already existing: "
    f"{(inventory_df['status'] == 'complete').sum()}"
)

print(
    f"Pending: "
    f"{(inventory_df['status'] == 'pending').sum()}"
)


# ============================================================
# 5. SAVE MANIFEST
# ============================================================

print("\n[5/7] Writing acquisition manifest...")

manifest = {
    "module": "15A_gpm_monthly_precipitation",
    "status": "INITIALIZED",

    "source": {
        "provider": "NASA GPM",
        "product": "IMERG Final Monthly",
        "collection": "GPM_3IMERGM",
        "version": "07",
        "resolution": "0.1 degree",
        "access": "OPeNDAP",
    },

    "period": {
        "start": str(START),
        "end": str(END),
        "months": len(EXPECTED_MONTHS),
    },

    "target": {
        "region": "Jharkhand",
        "source_grid": "SMAP SPL4SMGP",
        "smap_cells": 984,
        "latitude_min": lat_min,
        "latitude_max": lat_max,
        "longitude_min": lon_min,
        "longitude_max": lon_max,
        "padding_degrees": PAD,
    },

    "notes": [
        (
            "Common-period analysis is limited to "
            "2015-04 through 2025-09 because the "
            "NASA IMERG Final V07 archive currently "
            "available here ends at 2025-09."
        ),
        (
            "The global GPM grid will not be downloaded "
            "in full; only the Jharkhand spatial window "
            "will be requested."
        ),
        (
            "Rainfall will be independently validated "
            "before correlation with SMAP soil moisture."
        ),
    ],

    "inventory": inventory,
}

atomic_json(
    manifest,
    MANIFEST
)


# ============================================================
# 6. DISPLAY FIRST REQUEST
# ============================================================

print("\n[6/7] First monthly request prepared...")

print(
    "\nFIRST MONTH:"
)

print(
    f"Month: {test_month.strftime('%Y-%m')}"
)

print(
    f"URL: {test_url}"
)

print(
    "\nNo bulk download has been performed yet."
)


# ============================================================
# 7. FINAL STATUS
# ============================================================

print("\n[7/7] Module initialization complete.")

print("=" * 70)
print("MODULE 15A INITIALIZATION COMPLETE")
print("=" * 70)

print(
    f"Common period: "
    f"{START.strftime('%Y-%m')} → "
    f"{END.strftime('%Y-%m')}"
)

print(
    f"Months: {len(EXPECTED_MONTHS)}"
)

print(
    f"SMAP spatial cells: {len(mask)}"
)

print(
    f"Output directory: {OUT_DIR}"
)

print(
    f"Manifest: {MANIFEST}"
)

print(
    "\nSTATUS: PASS"
)
