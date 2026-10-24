#!/usr/bin/env python3

import os
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

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

DEFAULT_WORKERS = 8
EXPECTED_CELLS = 984

INVENTORY_FILE = "data/smap_granule_inventory.csv"
MASK_FILE = "data/jharkhand_smap_mask.csv"

MONTHLY_DIR = "data/monthly"
CHECKPOINT_DIR = "data/checkpoints_parallel"
LOG_DIR = "logs"


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
        f"failed_granules_parallel_{month}.csv"
    )


# =========================================================
# Inventory
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
# Mask
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

    rr = (
        mask["row"].to_numpy(dtype=int)
        - R1
    )

    cc = (
        mask["col"].to_numpy(dtype=int)
        - C1
    )

    if np.any(rr < 0) or np.any(rr >= (R2 - R1)):
        raise ValueError("Mask row indices outside extraction window.")

    if np.any(cc < 0) or np.any(cc >= (C2 - C1)):
        raise ValueError("Mask column indices outside extraction window.")

    return mask, rr, cc


# =========================================================
# DAP4 URL
# =========================================================

def to_dap4_url(url):

    if url.startswith("https://"):
        return "dap4://" + url[len("https://"):]

    if url.startswith("http://"):
        return "dap4://" + url[len("http://"):]

    if url.startswith("dap4://"):
        return url

    raise ValueError(
        f"Unsupported OPeNDAP URL: {url}"
    )


# =========================================================
# NASA fetch with retry
# =========================================================

def fetch_granule(index, row, rr, cc):

    title = str(row["title"])
    original_url = str(row["opendap_url"])
    url = to_dap4_url(original_url)

    last_error = None
    started = time.perf_counter()

    for attempt in range(MAX_RETRIES):

        try:

            ds = open_url(url)

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
                    f"Unexpected shape {values.shape}; "
                    f"expected {expected_shape}"
                )

            selected = values[rr, cc]

            valid = (
                np.isfinite(selected)
                & (selected >= 0.0)
                & (selected <= 0.9)
            )

            elapsed = time.perf_counter() - started

            return {
                "index": index,
                "title": title,
                "time_start": str(row["time_start"]),
                "opendap_url": original_url,
                "values": selected,
                "valid": valid,
                "success": True,
                "elapsed": elapsed,
                "error": "",
            }

        except Exception as exc:

            last_error = exc

            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAYS[attempt])

    elapsed = time.perf_counter() - started

    return {
        "index": index,
        "title": title,
        "time_start": str(row["time_start"]),
        "opendap_url": original_url,
        "values": None,
        "valid": None,
        "success": False,
        "elapsed": elapsed,
        "error": (
            f"{type(last_error).__name__}: "
            f"{last_error}"
        ),
    }


# =========================================================
# Atomic checkpoint save
# =========================================================

def save_checkpoint(
    month,
    completed,
    sums,
    counts
):

    os.makedirs(
        CHECKPOINT_DIR,
        exist_ok=True
    )

    final_path = checkpoint_path(month)

    temp_path = final_path + ".tmp.npz"

    np.savez_compressed(
        temp_path,
        completed=completed.astype(np.bool_),
        sums=sums,
        counts=counts,
    )

    os.replace(
        temp_path,
        final_path
    )


# =========================================================
# Load checkpoint
# =========================================================

def load_or_create_checkpoint(
    month,
    n_granules,
    n_cells
):

    path = checkpoint_path(month)

    if not os.path.exists(path):

        return (
            np.zeros(
                n_granules,
                dtype=bool
            ),
            np.zeros(
                n_cells,
                dtype=np.float64
            ),
            np.zeros(
                n_cells,
                dtype=np.int64
            ),
        )

    print()
    print("Existing parallel checkpoint found:")
    print(path)

    data = np.load(path)

    if "completed" not in data:
        raise ValueError(
            "Checkpoint is not a parallel checkpoint."
        )

    completed = data["completed"].copy()
    sums = data["sums"].copy()
    counts = data["counts"].copy()

    if len(completed) != n_granules:
        raise ValueError(
            "Checkpoint granule count does not match inventory."
        )

    if len(sums) != n_cells:
        raise ValueError(
            "Checkpoint sums do not match mask."
        )

    if len(counts) != n_cells:
        raise ValueError(
            "Checkpoint counts do not match mask."
        )

    return completed, sums, counts


# =========================================================
# Failed logging
# =========================================================

def log_failure(
    month,
    result
):

    os.makedirs(
        LOG_DIR,
        exist_ok=True
    )

    path = failed_log_path(month)

    row = pd.DataFrame([
        {
            "month": month,
            "index": result["index"],
            "title": result["title"],
            "time_start": result["time_start"],
            "opendap_url": result["opendap_url"],
            "status": "FAILED",
            "error": result["error"],
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

    os.makedirs(
        MONTHLY_DIR,
        exist_ok=True
    )

    output.to_csv(
        output_path(month),
        index=False
    )


# =========================================================
# Main processing
# =========================================================

def process_month(
    month,
    workers,
    limit=None
):

    print("=" * 70)
    print("EARTH TREND DETECTIVE — PARALLEL PRODUCTION EXTRACTION")
    print("=" * 70)
    print(f"Month:              {month}")
    print(f"Workers:            {workers}")
    print(f"Grid window:        {(R2-R1)} x {(C2-C1)}")
    print(f"Mask cells:         {EXPECTED_CELLS}")
    print("Protocol:           DAP4")
    print()

    inventory = load_month_inventory(month)

    if limit is not None:
        inventory = inventory.head(limit).copy()

    mask, rr, cc = load_mask()

    n_granules = len(inventory)

    print(f"Granules:            {n_granules}")

    completed, sums, counts = (
        load_or_create_checkpoint(
            month,
            n_granules,
            EXPECTED_CELLS
        )
    )

    already_done = int(
        completed.sum()
    )

    pending_indices = [
        i
        for i in range(n_granules)
        if not completed[i]
    ]

    print(f"Already completed:   {already_done}")
    print(f"Pending:             {len(pending_indices)}")
    print()

    if not pending_indices:

        print("All granules already completed.")

        expected = n_granules

        rebuild_output(
            month,
            mask,
            sums,
            counts,
            expected
        )

        print(
            f"Output rebuilt: {output_path(month)}"
        )

        return

    started = time.perf_counter()

    success_count = 0
    failure_count = 0

    with ThreadPoolExecutor(
        max_workers=workers
    ) as executor:

        futures = {}

        for index in pending_indices:

            row = inventory.iloc[index]

            future = executor.submit(
                fetch_granule,
                index,
                row,
                rr,
                cc
            )

            futures[future] = index

        finished = 0

        for future in as_completed(futures):

            result = future.result()

            index = result["index"]

            finished += 1

            if result["success"]:

                values = result["values"]
                valid = result["valid"]

                sums[valid] += values[valid]
                counts[valid] += 1

                completed[index] = True

                success_count += 1

                # Important:
                # checkpoint is updated only by the main thread
                # after aggregation has completed.
                save_checkpoint(
                    month,
                    completed,
                    sums,
                    counts
                )

                print(
                    f"[{finished:04d}/{len(pending_indices):04d}] "
                    f"OK   "
                    f"{result['elapsed']:6.2f}s "
                    f"valid={int(valid.sum()):3d} "
                    f"{result['title']}"
                )

            else:

                failure_count += 1

                log_failure(
                    month,
                    result
                )

                print(
                    f"[{finished:04d}/{len(pending_indices):04d}] "
                    f"FAIL "
                    f"{result['elapsed']:6.2f}s "
                    f"{result['title']}"
                )

                print(
                    f"       {result['error']}"
                )

    elapsed = time.perf_counter() - started

    completed_total = int(
        completed.sum()
    )

    remaining = (
        n_granules
        - completed_total
    )

    print()
    print("=" * 70)
    print("EXTRACTION RESULT")
    print("=" * 70)
    print(f"Total granules:       {n_granules}")
    print(f"Completed this run:   {success_count}")
    print(f"Failed this run:      {failure_count}")
    print(f"Completed overall:    {completed_total}")
    print(f"Remaining:            {remaining}")
    print(f"Wall time:            {elapsed:.2f} sec")

    if success_count > 0:
        print(
            f"Run avg/granule:      "
            f"{elapsed / success_count:.2f} sec"
        )

    print()

    if remaining > 0:

        print("WARNING: Some granules remain incomplete.")
        print()
        print(
            "The checkpoint has been saved."
        )
        print(
            "Run the same command again to retry "
            "the remaining granules."
        )

        return

    # =====================================================
    # Complete month
    # =====================================================

    expected = n_granules

    rebuild_output(
        month,
        mask,
        sums,
        counts,
        expected
    )

    print(
        f"Monthly output:      {output_path(month)}"
    )

    coverage = counts / expected

    print(
        f"Minimum coverage:    {coverage.min():.4f}"
    )

    print(
        f"Maximum coverage:    {coverage.max():.4f}"
    )

    print(
        f"Mean coverage:       {coverage.mean():.4f}"
    )

    if np.all(counts == expected):

        print()
        print("QUALITY CHECK:       PASS")
        print(
            "All 984 Jharkhand cells have "
            "complete observations."
        )

    else:

        print()
        print("QUALITY CHECK:       WARNING")
        print(
            f"Cells with complete coverage: "
            f"{int(np.sum(counts == expected))}/{EXPECTED_CELLS}"
        )


# =========================================================
# CLI
# =========================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Parallel DAP4 SMAP monthly extraction "
            "for Jharkhand."
        )
    )

    parser.add_argument(
        "month",
        help="Month in YYYY-MM format"
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=(
            f"Number of concurrent workers "
            f"(default: {DEFAULT_WORKERS})"
        )
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Process only the first N granules "
            "from the monthly inventory."
        )
    )

    args = parser.parse_args()

    if not 1 <= args.workers <= 16:
        raise ValueError(
            "Workers must be between 1 and 16."
        )

    if args.limit is not None:
        if args.limit < 1:
            raise ValueError("--limit must be >= 1")

    process_month(
        args.month,
        args.workers,
        args.limit
    )


if __name__ == "__main__":
    main()
