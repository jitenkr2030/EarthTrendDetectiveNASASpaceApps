from pathlib import Path
import calendar
import json
import time

import earthaccess
import numpy as np
import pandas as pd
import xarray as xr


# ============================================================
# CONFIGURATION
# ============================================================

START = pd.Timestamp("2015-04-01")
END = pd.Timestamp("2025-09-01")

MASK_FILE = Path("data/gpm_jharkhand_mask.csv")
DOWNLOAD_DIR = Path("data/gpm_monthly")
OUTPUT_FILE = Path("data/analysis/gpm_monthly_jharkhand.csv")
MANIFEST_FILE = Path("data/analysis/gpm_monthly_jharkhand_manifest.json")

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)


# ============================================================
# EARTHDATA LOGIN
# ============================================================

print("=" * 70)
print("GPM IMERG MONTHLY — JHARKHAND PRODUCTION EXTRACTION")
print("=" * 70)

print("\nLogging into NASA Earthdata...")

auth = earthaccess.login(strategy="netrc")

if auth is None:
    raise RuntimeError("NASA Earthdata authentication failed.")

print("Earthdata login: PASS")


# ============================================================
# LOAD MASK
# ============================================================

mask = pd.read_csv(MASK_FILE)

required_mask_columns = {
    "gpm_lon_index",
    "gpm_lat_index",
    "longitude",
    "latitude",
}

missing_columns = required_mask_columns - set(mask.columns)

if missing_columns:
    raise RuntimeError(
        f"Mask missing required columns: {sorted(missing_columns)}"
    )

if len(mask) != 703:
    raise RuntimeError(
        f"Expected 703 Jharkhand GPM cells, found {len(mask)}"
    )

if mask.duplicated(
    subset=["gpm_lon_index", "gpm_lat_index"]
).any():
    raise RuntimeError("Duplicate GPM mask cells detected.")

print("\nGPM mask:")
print("Cells:", len(mask))
print("Mask validation: PASS")


# ============================================================
# MONTH RANGE
# ============================================================

months = pd.date_range(
    START,
    END,
    freq="MS",
)

print("\nProduction period:")
print("Start:", START.date())
print("End:", END.date())
print("Months:", len(months))


# ============================================================
# EARTHACCESS SEARCH
# ============================================================

def find_month_granule(month):
    """
    Search NASA GES DISC for the monthly GPM IMERG V07B
    granule corresponding to the requested month.
    """

    start = month.to_pydatetime()
    next_month = (
        month + pd.offsets.MonthBegin(1)
    )

    results = earthaccess.search_data(
        short_name="GPM_3IMERGM",
        version="07",
        temporal=(
            start,
            next_month.to_pydatetime(),
        ),
    )

    if not results:
        return None

    # Prefer the exact monthly V07B granule.
    target_prefix = month.strftime("%Y%m")

    for item in results:
        filename = getattr(item, "data_links", None)

        # Search results can expose filename through multiple fields.
        item_text = str(item)

        if (
            target_prefix in item_text
            and "3B-MO.MS.MRG.3IMERG" in item_text
        ):
            return item

    return results[0]


# ============================================================
# DOWNLOAD + EXTRACT ONE MONTH
# ============================================================

def process_month(month):

    month_key = month.strftime("%Y-%m")

    print("\n" + "=" * 70)
    print(f"PROCESSING {month_key}")
    print("=" * 70)

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    print("Searching NASA GES DISC...")

    granule = find_month_granule(month)

    if granule is None:
        raise RuntimeError(
            f"No GPM IMERG granule found for {month_key}"
        )

    print("Granule found.")

    # --------------------------------------------------------
    # Download
    # --------------------------------------------------------

    print("Downloading granule...")

    downloaded = earthaccess.download(
        [granule],
        local_path=str(DOWNLOAD_DIR),
    )

    if not downloaded:
        raise RuntimeError(
            f"Download returned no files for {month_key}"
        )

    gpm_file = Path(downloaded[0])

    print("Downloaded:", gpm_file.name)
    print(
        "File size:",
        round(gpm_file.stat().st_size / 1024 / 1024, 2),
        "MB",
    )

    # --------------------------------------------------------
    # Open Grid group
    # --------------------------------------------------------

    ds = xr.open_dataset(
        gpm_file,
        group="Grid",
        engine="h5netcdf",
    )

    try:
        precip = ds["precipitation"].values[0]

        lat = ds["lat"].values
        lon = ds["lon"].values

        # ----------------------------------------------------
        # Coordinate validation
        # ----------------------------------------------------

        lat_diff = (
            mask["latitude"].to_numpy()
            - lat[mask["gpm_lat_index"].to_numpy()]
        )

        lon_diff = (
            mask["longitude"].to_numpy()
            - lon[mask["gpm_lon_index"].to_numpy()]
        )

        if np.max(np.abs(lat_diff)) >= 1e-6:
            raise RuntimeError(
                f"Latitude mismatch for {month_key}"
            )

        if np.max(np.abs(lon_diff)) >= 1e-6:
            raise RuntimeError(
                f"Longitude mismatch for {month_key}"
            )

        # ----------------------------------------------------
        # Extract 703 Jharkhand cells
        # ----------------------------------------------------

        lon_idx = mask["gpm_lon_index"].to_numpy()
        lat_idx = mask["gpm_lat_index"].to_numpy()

        values = np.asarray(
            precip[lon_idx, lat_idx],
            dtype=np.float64,
        )

        # ----------------------------------------------------
        # Handle fill values
        # ----------------------------------------------------

        fill_value = -9999.9

        values[
            values <= -9990
        ] = np.nan

        values[
            values == fill_value
        ] = np.nan

        valid = values[np.isfinite(values)]

        expected_cells = len(mask)
        valid_cells = len(valid)

        coverage = (
            valid_cells / expected_cells
        )

        if valid_cells == 0:
            raise RuntimeError(
                f"No valid rainfall cells for {month_key}"
            )

        if coverage < 0.95:
            raise RuntimeError(
                f"Rainfall coverage below 95% for {month_key}: "
                f"{coverage:.4f}"
            )

        # ----------------------------------------------------
        # Monthly duration
        # ----------------------------------------------------

        year = month.year
        month_number = month.month

        days = calendar.monthrange(
            year,
            month_number,
        )[1]

        hours = days * 24

        # GPM field is mean precipitation rate.
        rate_mean = float(np.mean(valid))

        rainfall_mm = rate_mean * hours

        # ----------------------------------------------------
        # Time metadata
        # ----------------------------------------------------

        time_value = ds["time"].values[0]

        if "time_bnds" in ds:
            time_bounds = ds["time_bnds"].values[0]
            time_start = str(time_bounds[0])
            time_end = str(time_bounds[1])
        else:
            time_start = ""
            time_end = ""

        result = {
            "date": month.strftime("%Y-%m-%d"),
            "year": year,
            "month_number": month_number,
            "days_in_month": days,
            "hours_in_month": hours,
            "gpm_cells": expected_cells,
            "valid_cells": valid_cells,
            "coverage_fraction": coverage,
            "precipitation_rate_mm_hr": rate_mean,
            "rainfall_mm_month": rainfall_mm,
            "minimum_precipitation_rate_mm_hr": float(valid.min()),
            "maximum_precipitation_rate_mm_hr": float(valid.max()),
            "median_precipitation_rate_mm_hr": float(
                np.median(valid)
            ),
            "time_start": time_start,
            "time_end": time_end,
            "source_file": gpm_file.name,
        }

        print("\nExtraction:")
        print("Expected cells:", expected_cells)
        print("Valid cells:", valid_cells)
        print("Coverage:", round(coverage, 6))
        print(
            "Mean rate:",
            round(rate_mean, 6),
            "mm/hr",
        )
        print(
            "Monthly rainfall:",
            round(rainfall_mm, 3),
            "mm",
        )

        print("Validation: PASS")

        return result

    finally:
        ds.close()


# ============================================================
# RESUME / CHECKPOINT
# ============================================================

results = []

if OUTPUT_FILE.exists():
    existing = pd.read_csv(OUTPUT_FILE)

    if not existing.empty:
        results = existing.to_dict("records")

existing_dates = {
    row["date"]
    for row in results
}

print("\nExisting completed months:", len(existing_dates))


# ============================================================
# PRODUCTION LOOP
# ============================================================

for month in months:

    month_key = month.strftime("%Y-%m-%d")

    if month_key in existing_dates:
        print(
            f"\nSKIP {month_key} — already extracted"
        )
        continue

    try:

        result = process_month(month)

        results.append(result)

        # Save checkpoint after every month.
        df_checkpoint = pd.DataFrame(results)
        df_checkpoint = df_checkpoint.sort_values(
            "date"
        )

        df_checkpoint.to_csv(
            OUTPUT_FILE,
            index=False,
        )

        print(
            f"CHECKPOINT SAVED: {len(results)} months"
        )

    except Exception as exc:

        print(
            f"\nERROR processing {month_key}: {exc}"
        )

        print(
            "Stopping so the failed month can be investigated."
        )

        raise

    time.sleep(1)


# ============================================================
# FINAL QA
# ============================================================

df = pd.read_csv(OUTPUT_FILE)

df["date"] = pd.to_datetime(df["date"])

df = df.sort_values("date").reset_index(drop=True)

expected_dates = pd.date_range(
    START,
    END,
    freq="MS",
)

actual_dates = pd.DatetimeIndex(
    df["date"]
)

missing_dates = expected_dates.difference(
    actual_dates
)

unexpected_dates = actual_dates.difference(
    expected_dates
)

duplicate_dates = df["date"].duplicated().sum()

coverage_pass = (
    df["coverage_fraction"] >= 0.95
).all()

rainfall_valid = (
    np.isfinite(df["rainfall_mm_month"])
    & (df["rainfall_mm_month"] >= 0)
).all()

final_pass = (
    len(df) == len(expected_dates)
    and len(missing_dates) == 0
    and len(unexpected_dates) == 0
    and duplicate_dates == 0
    and coverage_pass
    and rainfall_valid
)

df.to_csv(
    OUTPUT_FILE,
    index=False,
)

manifest = {
    "product": "GPM IMERG Monthly",
    "short_name": "GPM_3IMERGM",
    "version": "07",
    "product_file_version": "V07B",
    "period_start": str(START.date()),
    "period_end": str(END.date()),
    "expected_months": len(expected_dates),
    "actual_months": len(df),
    "jharkhand_gpm_cells": 703,
    "spatial_resolution": "0.1 degree",
    "source_variable": "precipitation",
    "source_units": "mm/hr",
    "derived_metric": "rainfall_mm_month",
    "conversion": (
        "monthly mean precipitation rate multiplied by "
        "calendar-month hours"
    ),
    "missing_value": -9999.9,
    "missing_dates": [
        str(x.date())
        for x in missing_dates
    ],
    "unexpected_dates": [
        str(x.date())
        for x in unexpected_dates
    ],
    "duplicate_dates": int(duplicate_dates),
    "coverage_pass": bool(coverage_pass),
    "rainfall_valid": bool(rainfall_valid),
    "status": (
        "FROZEN / ANALYSIS READY"
        if final_pass
        else "FAIL"
    ),
}

with open(
    MANIFEST_FILE,
    "w",
) as f:
    json.dump(
        manifest,
        f,
        indent=2,
    )

print("\n" + "=" * 70)
print("FINAL GPM PRODUCTION QA")
print("=" * 70)

print("Expected months:", len(expected_dates))
print("Actual months:", len(df))
print("Missing months:", len(missing_dates))
print("Unexpected months:", len(unexpected_dates))
print("Duplicate dates:", int(duplicate_dates))
print(
    "Coverage QA:",
    "PASS" if coverage_pass else "FAIL",
)
print(
    "Rainfall QA:",
    "PASS" if rainfall_valid else "FAIL",
)

print("\nOutput:")
print(OUTPUT_FILE)

print("\nManifest:")
print(MANIFEST_FILE)

print(
    "\nFINAL RESULT:",
    "PASS — GPM monthly Jharkhand dataset is ready"
    if final_pass
    else "FAIL — dataset requires investigation"
)

print("=" * 70)
