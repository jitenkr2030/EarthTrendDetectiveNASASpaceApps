#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pathlib import Path

MONTHLY_DIR = Path("data/monthly")
EXPECTED_CELLS = 984


def is_valid_month_output(month: str) -> bool:
    path = MONTHLY_DIR / f"{month}.csv"

    if not path.exists():
        return False

    try:
        import pandas as pd

        df = pd.read_csv(path)

        required = {
            "month",
            "soil_moisture_mean",
            "observations",
            "expected_observations",
            "coverage_fraction",
        }

        if not required.issubset(df.columns):
            return False

        if len(df) != EXPECTED_CELLS:
            return False

        if df["soil_moisture_mean"].isna().any():
            return False

        if (df["coverage_fraction"] < 1.0).any():
            return False

        return True

    except Exception:
        return False


def run_month(month: str, workers: int):
    print()
    print("=" * 70)
    print(f"YEAR RUNNER → {month}")
    print("=" * 70)

    if is_valid_month_output(month):
        print(f"SKIP: {month}.csv already passes 984-cell quality check.")
        return True

    cmd = [
        sys.executable,
        "src/extract_monthly_parallel.py",
        month,
        "--workers",
        str(workers),
    ]

    print("Running:")
    print(" ".join(cmd))
    print()

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print()
        print("=" * 70)
        print(f"STOPPED: {month}")
        print(f"Exit code: {result.returncode}")
        print("=" * 70)
        return False

    if not is_valid_month_output(month):
        print()
        print("=" * 70)
        print(f"QUALITY CHECK FAILED: {month}")
        print("Output does not contain 984 complete cells.")
        print("=" * 70)
        return False

    print()
    print(f"PASS: {month}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Earth Trend Detective yearly SMAP extraction runner"
    )

    parser.add_argument(
        "year",
        type=int,
        help="Year to process, e.g. 2018",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        choices=range(1, 17),
        help="Parallel DAP4 workers (default: 8)",
    )

    args = parser.parse_args()

    if args.year < 2015 or args.year > 2100:
        raise ValueError("Year must be between 2015 and 2100.")

    print("=" * 70)
    print("EARTH TREND DETECTIVE — YEARLY PRODUCTION EXTRACTION")
    print("=" * 70)
    print(f"Year:                {args.year}")
    print(f"Workers:             {args.workers}")
    print(f"Expected cells/month:{EXPECTED_CELLS}")
    print("=" * 70)

    passed = []
    failed = []

    for month_number in range(1, 13):
        month = f"{args.year}-{month_number:02d}"

        # 2015 data begins in April.
        if args.year == 2015 and month_number < 4:
            print(f"SKIP: {month} — dataset begins in April 2015.")
            continue

        # Future months may not exist in the inventory.
        if not run_month(month, args.workers):
            failed.append(month)
            break

        passed.append(month)

    print()
    print("=" * 70)
    print("YEAR EXTRACTION SUMMARY")
    print("=" * 70)

    print(f"Passed: {len(passed)}")

    if passed:
        print("Completed months:")
        for month in passed:
            print(f"  PASS  {month}")

    if failed:
        print()
        print("Failed/stopped month:")
        for month in failed:
            print(f"  FAIL  {month}")

        print()
        print("Rerun the same command to resume from the failed month.")

        sys.exit(1)

    print()
    print(f"YEAR {args.year}: COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
