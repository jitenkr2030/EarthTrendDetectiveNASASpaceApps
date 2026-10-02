#!/usr/bin/env python3

import os
import time
import argparse
import numpy as np
import pandas as pd
from pydap.client import open_url


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

R1, R2 = 465, 509
C1, C2 = 2820, 2870

SM_PATH = "/Geophysical_Data/sm_surface"

MAX_RETRIES = 4
RETRY_DELAYS = [5, 10, 20, 40]

INVENTORY_FILE = "data/smap_granule_inventory.csv"
MASK_FILE = "data/jharkhand_smap_mask.csv"

MONTHLY_DIR = "data/monthly"
CHECKPOINT_DIR = "data/checkpoints"
LOG_DIR = "logs"


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def load_month_inventory(month):
    inventory = pd.read_csv(INVENTORY_FILE)

    inventory["time_start"] = pd.to_datetime(
        inventory["time_start"],
        utc=True
    )

    inventory["month"] = inventory["time_start"].dt.strftime("%Y-%m")

    result = inventory[
        inventory["month"] == month
    ].copy()

    result = result.sort_values("time_start").reset_index(drop=True)

    return result


def load_mask():
    mask = pd.read_csv(MASK_FILE)

    required = {
        "row",
        "col",
        "latitude",
        "longitude",
    }

    missing = required - set(mask.columns)

    if missing:
        raise ValueError(
            f"Mask missing columns: {sorted(missing)}"
        )

    return mask


def open_with_retry(url):
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            ds = open_url(url)
            return ds

        except Exception as exc:
            last_error = exc

            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]

                print(
                    f"  Retry {attempt + 1}/{MAX_RETRIES - 1} "
                    f"in {delay}s..."
                )

                time.sleep(delay)

    raise last_error


def checkpoint_path(month):
    return os.path.join(
        CHECKPOINT_DIR,
        f"{month}.npz"
    )


def output_path(month):
    return os.path.join(
        MONTHLY_DIR,
        f"{month}.csv"
    )


def failed_log_path(month):
    return os.path.join(
        LOG_DIR,
        f"failed_granules_{month}.csv"
    )


# ---------------------------------------------------------
# Checkpoint
# ---------------------------------------------------------

def save_checkpoint(
    month,
    next_index,
    sums,
    counts
):
    path = checkpoint_path(month)

    np.savez_compressed(
        path,
        next_index=np.array([next_index]),
        sums=sums,
        counts=counts,
    )


def load_checkpoint(month):
    path = checkpoint_path(month)

    if not os.path.exists(path):
        return None

    data = np.load(path)

    return {
        "next_index": int(data["next_index"][0]),
        "sums": data["sums"],
        "counts": data["counts"],
    }


# ---------------------------------------------------------
# Failed granule logging
# ---------------------------------------------------------

def log_failed_granule(
    month,
    index,
    title,
    time_start,
    url,
    error
):
    path = failed_log_path(month)

    row = pd.DataFrame([
        {
            "month": month,
            "index": index,
            "title": title,
            "time_start": time_start,
            "opendap_url": url,
            "error": str(error),
        }
    ])

    write_header = not os.path.exists(path)

    row.to_csv(
        path,
        mode="a",
        header=write_header,
        index=False
    )


# ---------------------------------------------------------
# Main extraction
# ---------------------------------------------------------

def process_month(month):
    print("=" * 70)
    print(f"EarthTrend Detective — Production Monthly Extraction")
    print(f"Month: {month}")
    print("=" * 70)

    os.makedirs(MONTHLY_DIR, exist_ok=True)
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    inventory = load_month_inventory(month)

    if inventory.empty:
        raise ValueError(
            f"No granules found for month: {month}"
        )

    mask = load_mask()

    print(f"Granules: {len(inventory)}")
    print(f"Jharkhand mask cells: {len(mask)}")

    if len(mask) != 984:
        raise ValueError(
            f"Expected 984 mask cells, found {len(mask)}"
        )

    # Convert mask coordinates to zero-based indices
    rr = mask["row"].to_numpy(dtype=int) - R1
    cc = mask["col"].to_numpy(dtype=int) - C1

    if np.any(rr < 0) or np.any(rr >= (R2 - R1)):
        raise ValueError("Mask row outside extraction window")

    if np.any(cc < 0) or np.any(cc >= (C2 - C1)):
        raise ValueError("Mask column outside extraction window")

    n_cells = len(mask)

    sums = np.zeros(n_cells, dtype=np.float64)
    counts = np.zeros(n_cells, dtype=np.int32)

    checkpoint = load_checkpoint(month)

    if checkpoint is not None:

        next_index = checkpoint["next_index"]

        saved_sums = checkpoint["sums"]
        saved_counts = checkpoint["counts"]

        if (
            len(saved_sums) != n_cells
            or len(saved_counts) != n_cells
        ):
            raise ValueError(
                "Checkpoint does not match current mask"
            )

        sums[:] = saved_sums
        counts[:] = saved_counts

        print(
            f"Checkpoint found. "
            f"Resuming from granule {next_index + 1}/"
            f"{len(inventory)}"
        )

    else:
        next_index = 0
        print("No checkpoint found. Starting from beginning.")

    failed = 0

    # -----------------------------------------------------
    # Granule loop
    # -----------------------------------------------------

    for i in range(next_index, len(inventory)):

        row = inventory.iloc[i]

        title = row["title"]
        time_start = row["time_start"]
        url = row["opendap_url"]

        print(
            f"\n[{i + 1}/{len(inventory)}] "
            f"{title}"
        )

        try:

            ds = open_with_retry(url)

            values = np.asarray(
                ds[SM_PATH][R1:R2, C1:C2]
            ).squeeze()

            values = values.astype(
                np.float64,
                copy=False
            )

            if values.shape != (R2 - R1, C2 - C1):
                raise ValueError(
                    f"Unexpected array shape: {values.shape}"
                )

            # Extract exactly the 984 Jharkhand cells
            selected = values[rr, cc]

            # SMAP valid range: 0–0.9 m3/m3
            valid = (
                np.isfinite(selected)
                & (selected >= 0.0)
                & (selected <= 0.9)
            )

            sums[valid] += selected[valid]
            counts[valid] += 1

            # Save checkpoint after EVERY successful granule
            save_checkpoint(
                month,
                i + 1,
                sums,
                counts
            )

            print(
                f"  Valid cells: "
                f"{int(valid.sum())}/{n_cells}"
            )

        except Exception as exc:

            failed += 1

            print(
                f"  FAILED: {type(exc).__name__}: {exc}"
            )

            log_failed_granule(
                month=month,
                index=i,
                title=title,
                time_start=time_start,
                url=url,
                error=exc
            )

            # Important:
            # We continue instead of killing the whole month.
            continue

    # -----------------------------------------------------
    # Monthly output
    # -----------------------------------------------------

    expected = len(inventory)

    mean_values = np.full(
        n_cells,
        np.nan,
        dtype=np.float64
    )

    valid_cells = counts > 0

    mean_values[valid_cells] = (
        sums[valid_cells]
        / counts[valid_cells]
    )

    coverage = counts / expected

    output = mask.copy()

    output["month"] = month
    output["soil_moisture_mean"] = mean_values
    output["observations"] = counts
    output["expected_observations"] = expected
    output["coverage_fraction"] = coverage

    path = output_path(month)

    output.to_csv(
        path,
        index=False
    )

    print("\n" + "=" * 70)
    print("MONTH COMPLETE")
    print("=" * 70)

    print(f"Month:              {month}")
    print(f"Expected granules:  {expected}")
    print(f"Failed granules:    {failed}")
    print(f"Cells:              {n_cells}")
    print(
        f"Cells with data:    "
        f"{int(valid_cells.sum())}"
    )

    print(
        f"Observation min:    "
        f"{counts.min()}"
    )

    print(
        f"Observation max:    "
        f"{counts.max()}"
    )

    valid_means = mean_values[np.isfinite(mean_values)]

    if len(valid_means):
        print(
            f"Mean soil moisture: "
            f"{valid_means.mean():.8f}"
        )

        print(
            f"Minimum:            "
            f"{valid_means.min():.8f}"
        )

        print(
            f"Maximum:            "
            f"{valid_means.max():.8f}"
        )

    print(f"\nOutput: {path}")

    if failed:
        print(
            f"Failed log: "
            f"{failed_log_path(month)}"
        )

    print(
        f"Checkpoint: "
        f"{checkpoint_path(month)}"
    )

    print("=" * 70)


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "Extract monthly SMAP soil moisture "
            "for the 984-cell Jharkhand mask."
        )
    )

    parser.add_argument(
        "month",
        help="Month in YYYY-MM format, e.g. 2015-05"
    )

    args = parser.parse_args()

    process_month(args.month)
