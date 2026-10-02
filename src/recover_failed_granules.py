#!/usr/bin/env python3

import os
import time
import argparse
import numpy as np
import pandas as pd
from pydap.client import open_url


# =========================================================
# Configuration
# =========================================================

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

EXPECTED_CELLS = 984


# =========================================================
# Paths
# =========================================================

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


def recovered_log_path(month):
    return os.path.join(
        LOG_DIR,
        f"recovered_granules_{month}.csv"
    )


# =========================================================
# Load inventory
# =========================================================

def load_month_inventory(month):

    inventory = pd.read_csv(INVENTORY_FILE)

    inventory["time_start"] = pd.to_datetime(
        inventory["time_start"],
        utc=True
    )

    inventory["month"] = (
        inventory["time_start"]
        .dt.strftime("%Y-%m")
    )

    result = inventory[
        inventory["month"] == month
    ].copy()

    result = (
        result
        .sort_values("time_start")
        .reset_index(drop=True)
    )

    if result.empty:
        raise ValueError(
            f"No inventory records found for {month}"
        )

    return result


# =========================================================
# Load mask
# =========================================================

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

    if len(mask) != EXPECTED_CELLS:
        raise ValueError(
            f"Expected {EXPECTED_CELLS} mask cells, "
            f"found {len(mask)}"
        )

    return mask


# =========================================================
# NASA retry
# =========================================================

def open_with_retry(url):

    last_error = None

    for attempt in range(MAX_RETRIES):

        try:

            print(
                f"    NASA open attempt "
                f"{attempt + 1}/{MAX_RETRIES}"
            )

            return open_url(url)

        except Exception as exc:

            last_error = exc

            print(
                f"    Open failed: "
                f"{type(exc).__name__}: {exc}"
            )

            if attempt < MAX_RETRIES - 1:

                delay = RETRY_DELAYS[attempt]

                print(
                    f"    Waiting {delay}s before retry..."
                )

                time.sleep(delay)

    raise last_error


# =========================================================
# Load checkpoint
# =========================================================

def load_checkpoint(month, n_cells):

    path = checkpoint_path(month)

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Checkpoint not found: {path}"
        )

    data = np.load(path)

    next_index = int(
        data["next_index"][0]
    )

    sums = data["sums"].copy()
    counts = data["counts"].copy()

    if len(sums) != n_cells:
        raise ValueError(
            "Checkpoint sums do not match mask."
        )

    if len(counts) != n_cells:
        raise ValueError(
            "Checkpoint counts do not match mask."
        )

    return next_index, sums, counts


# =========================================================
# Save checkpoint
# =========================================================

def save_checkpoint(
    month,
    next_index,
    sums,
    counts
):

    np.savez_compressed(
        checkpoint_path(month),
        next_index=np.array([next_index]),
        sums=sums,
        counts=counts,
    )


# =========================================================
# Recovered log
# =========================================================

def load_recovered_titles(month):

    path = recovered_log_path(month)

    if not os.path.exists(path):
        return set()

    df = pd.read_csv(path)

    if "title" not in df.columns:
        return set()

    return set(
        df["title"]
        .dropna()
        .astype(str)
    )


def log_recovered(
    month,
    index,
    title,
    time_start,
    url
):

    path = recovered_log_path(month)

    row = pd.DataFrame([
        {
            "month": month,
            "index": index,
            "title": title,
            "time_start": time_start,
            "opendap_url": url,
            "status": "RECOVERED",
        }
    ])

    write_header = not os.path.exists(path)

    row.to_csv(
        path,
        mode="a",
        header=write_header,
        index=False
    )


# =========================================================
# Rebuild monthly output
# =========================================================

def rebuild_output(
    month,
    mask,
    sums,
    counts,
    expected
):

    mean_values = np.full(
        len(mask),
        np.nan,
        dtype=np.float64
    )

    valid_cells = counts > 0

    mean_values[valid_cells] = (
        sums[valid_cells]
        / counts[valid_cells]
    )

    output = mask.copy()

    output["month"] = month
    output["soil_moisture_mean"] = mean_values
    output["observations"] = counts
    output["expected_observations"] = expected
    output["coverage_fraction"] = (
        counts / expected
    )

    output.to_csv(
        output_path(month),
        index=False
    )

    return output


# =========================================================
# Main recovery
# =========================================================

def recover_month(month):

    print("=" * 70)
    print("EarthTrend Detective — Automatic Failed-Granule Recovery")
    print("=" * 70)
    print(f"Month: {month}")
    print("=" * 70)

    failed_path = failed_log_path(month)

    if not os.path.exists(failed_path):

        print("\nNo failed-granule log found.")
        print("Nothing to recover.")
        return True

    inventory = load_month_inventory(month)
    mask = load_mask()

    expected = len(inventory)
    n_cells = len(mask)

    next_index, sums, counts = load_checkpoint(
        month,
        n_cells
    )

    print(f"Expected granules: {expected}")
    print(f"Mask cells:        {n_cells}")
    print(f"Checkpoint index:  {next_index}")

    # -----------------------------------------------------
    # Read failed log
    # -----------------------------------------------------

    failed_df = pd.read_csv(
        failed_path
    )

    if failed_df.empty:

        print("\nFailed log is empty.")
        return True

    required = {
        "index",
        "title",
        "time_start",
        "opendap_url",
    }

    missing = required - set(failed_df.columns)

    if missing:
        raise ValueError(
            f"Failed log missing columns: {sorted(missing)}"
        )

    # Remove duplicate failures
    failed_df = (
        failed_df
        .drop_duplicates(
            subset=["title"],
            keep="first"
        )
        .reset_index(drop=True)
    )

    recovered_titles = load_recovered_titles(
        month
    )

    print(
        f"Failed granules listed: "
        f"{len(failed_df)}"
    )

    print(
        f"Already recovered: "
        f"{len(recovered_titles)}"
    )

    # -----------------------------------------------------
    # If already complete, don't double-count
    # -----------------------------------------------------

    if np.all(counts == expected):

        print()
        print(
            "All cells already have "
            f"{expected}/{expected} observations."
        )

        print(
            "No recovery will be applied."
        )

        rebuild_output(
            month,
            mask,
            sums,
            counts,
            expected
        )

        print("\nSTATUS: ALREADY COMPLETE")

        return True

    # -----------------------------------------------------
    # Prepare mask indices
    # -----------------------------------------------------

    rr = (
        mask["row"].to_numpy(dtype=int)
        - R1
    )

    cc = (
        mask["col"].to_numpy(dtype=int)
        - C1
    )

    if np.any(rr < 0) or np.any(
        rr >= (R2 - R1)
    ):
        raise ValueError(
            "Mask row outside extraction window."
        )

    if np.any(cc < 0) or np.any(
        cc >= (C2 - C1)
    ):
        raise ValueError(
            "Mask column outside extraction window."
        )

    # -----------------------------------------------------
    # Recover each failed granule
    # -----------------------------------------------------

    recovered_now = 0
    still_failed = 0

    for _, row in failed_df.iterrows():

        title = str(row["title"])

        if title in recovered_titles:

            print(
                f"\nSKIP already recovered: {title}"
            )

            continue

        index = int(row["index"])
        time_start = row["time_start"]
        url = str(row["opendap_url"])

        print()
        print("-" * 70)
        print(
            f"RECOVERING [{index + 1}/{expected}]"
        )
        print(title)
        print(time_start)
        print("-" * 70)

        try:

            ds = open_with_retry(url)

            values = np.asarray(
                ds[SM_PATH][R1:R2, C1:C2]
            ).squeeze()

            values = values.astype(
                np.float64,
                copy=False
            )

            expected_shape = (
                R2 - R1,
                C2 - C1
            )

            if values.shape != expected_shape:

                raise ValueError(
                    f"Unexpected array shape: "
                    f"{values.shape}; "
                    f"expected {expected_shape}"
                )

            selected = values[rr, cc]

            valid = (
                np.isfinite(selected)
                & (selected >= 0.0)
                & (selected <= 0.9)
            )

            valid_count = int(
                valid.sum()
            )

            print(
                f"Grid shape:     {values.shape}"
            )

            print(
                f"Selected cells: {len(selected)}"
            )

            print(
                f"Valid cells:    "
                f"{valid_count}/{n_cells}"
            )

            if not valid.all():

                raise ValueError(
                    "Recovered granule does not "
                    "contain valid data for all "
                    f"{n_cells} cells."
                )

            # ---------------------------------------------
            # Safety against accidental double recovery
            # ---------------------------------------------

            before_min = int(counts.min())
            before_max = int(counts.max())

            sums += selected
            counts += 1

            after_min = int(counts.min())
            after_max = int(counts.max())

            print(
                f"Observation counts: "
                f"{before_min}-{before_max} "
                f"→ {after_min}-{after_max}"
            )

            log_recovered(
                month,
                index,
                title,
                time_start,
                url
            )

            recovered_now += 1

            save_checkpoint(
                month,
                next_index,
                sums,
                counts
            )

            print("Recovery: PASS")

        except Exception as exc:

            still_failed += 1

            print(
                f"RECOVERY FAILED: "
                f"{type(exc).__name__}: {exc}"
            )

    # -----------------------------------------------------
    # Rebuild output
    # -----------------------------------------------------

    output = rebuild_output(
        month,
        mask,
        sums,
        counts,
        expected
    )

    coverage_min = float(
        output["coverage_fraction"].min()
    )

    coverage_max = float(
        output["coverage_fraction"].max()
    )

    observations_min = int(
        output["observations"].min()
    )

    observations_max = int(
        output["observations"].max()
    )

    # -----------------------------------------------------
    # Final status
    # -----------------------------------------------------

    print()
    print("=" * 70)
    print("RECOVERY SUMMARY")
    print("=" * 70)

    print(f"Month:              {month}")
    print(f"Expected granules:  {expected}")
    print(f"Recovered now:      {recovered_now}")
    print(f"Still failed:       {still_failed}")
    print(f"Cells:              {n_cells}")
    print(
        f"Observations:       "
        f"{observations_min}-{observations_max}"
    )
    print(
        f"Coverage:           "
        f"{coverage_min:.6f}-{coverage_max:.6f}"
    )

    print(
        f"Output:             "
        f"{output_path(month)}"
    )

    print(
        f"Checkpoint:         "
        f"{checkpoint_path(month)}"
    )

    print(
        f"Recovery log:       "
        f"{recovered_log_path(month)}"
    )

    print("=" * 70)

    if (
        still_failed == 0
        and np.all(counts == expected)
    ):

        print("STATUS: PASS")
        print(
            f"{month}: 100% temporal recovery complete."
        )

        return True

    print("STATUS: INCOMPLETE")

    return False


# =========================================================
# CLI
# =========================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "Automatically recover failed NASA SMAP "
            "granules for a month."
        )
    )

    parser.add_argument(
        "month",
        help="Month in YYYY-MM format"
    )

    args = parser.parse_args()

    ok = recover_month(
        args.month
    )

    raise SystemExit(
        0 if ok else 1
    )
