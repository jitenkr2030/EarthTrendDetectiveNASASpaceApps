import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd


# ============================================================
# CONFIG
# ============================================================

INVENTORY = Path("data/smap_granule_inventory.csv")
MONTHLY_DIR = Path("data/monthly")
FAILED_LOG_DIR = Path("logs")

EXPECTED_CELLS = 984


# ============================================================
# INVENTORY
# ============================================================

def load_months():
    df = pd.read_csv(INVENTORY)

    if "time_start" not in df.columns:
        raise ValueError("Inventory missing time_start column")

    df["time_start"] = pd.to_datetime(df["time_start"], utc=True)

    months = (
        df["time_start"]
        .dt.to_period("M")
        .astype(str)
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    # March 2015 is partial and intentionally excluded.
    months = [m for m in months if m >= "2015-04"]

    return months


# ============================================================
# VALIDATION
# ============================================================

def validate_month(month):
    output_file = MONTHLY_DIR / f"{month}.csv"

    if not output_file.exists():
        print(f"❌ Missing output: {output_file}")
        return False

    df = pd.read_csv(output_file)

    required = {
        "month",
        "row",
        "col",
        "latitude",
        "longitude",
        "soil_moisture_mean",
        "observations",
        "expected_observations",
        "coverage_fraction",
    }

    missing_columns = required - set(df.columns)

    if missing_columns:
        print(f"❌ Missing columns: {sorted(missing_columns)}")
        return False

    # --------------------------------------------------------
    # Cell count
    # --------------------------------------------------------

    if len(df) != EXPECTED_CELLS:
        print(
            f"❌ Cell count mismatch: "
            f"{len(df)} / {EXPECTED_CELLS}"
        )
        return False

    # --------------------------------------------------------
    # Duplicate cells
    # --------------------------------------------------------

    duplicates = df.duplicated(["row", "col"]).sum()

    if duplicates:
        print(f"❌ Duplicate cells: {duplicates}")
        return False

    # --------------------------------------------------------
    # Month
    # --------------------------------------------------------

    if df["month"].astype(str).nunique() != 1:
        print("❌ Multiple month values found")
        return False

    if str(df["month"].iloc[0]) != month:
        print(
            f"❌ Month mismatch: "
            f"file={df['month'].iloc[0]} expected={month}"
        )
        return False

    # --------------------------------------------------------
    # Soil moisture
    # --------------------------------------------------------

    if df["soil_moisture_mean"].isna().any():
        print("❌ Missing soil moisture values")
        return False

    invalid_sm = (
        (df["soil_moisture_mean"] < 0)
        | (df["soil_moisture_mean"] > 0.9)
    ).sum()

    if invalid_sm:
        print(f"❌ Invalid soil moisture values: {invalid_sm}")
        return False

    # --------------------------------------------------------
    # Coordinates
    # --------------------------------------------------------

    if df["latitude"].isna().any() or df["longitude"].isna().any():
        print("❌ Missing coordinates")
        return False

    # --------------------------------------------------------
    # Observations
    # --------------------------------------------------------

    if df["observations"].isna().any():
        print("❌ Missing observation counts")
        return False

    if df["expected_observations"].isna().any():
        print("❌ Missing expected observation counts")
        return False

    # --------------------------------------------------------
    # STRICT TEMPORAL COMPLETENESS
    # --------------------------------------------------------

    if not (df["observations"] == df["expected_observations"]).all():
        print("❌ Temporal completeness FAILED")

        print(
            df.loc[
                df["observations"] != df["expected_observations"],
                [
                    "row",
                    "col",
                    "observations",
                    "expected_observations",
                    "coverage_fraction",
                ],
            ].head(10).to_string(index=False)
        )

        return False

    # --------------------------------------------------------
    # Coverage
    # --------------------------------------------------------

    if not (df["coverage_fraction"] == 1.0).all():
        print("❌ Coverage is not 100%")
        return False

    # --------------------------------------------------------
    # PASS
    # --------------------------------------------------------

    print(
        f"✅ VALIDATED {month}: "
        f"{len(df)} cells | "
        f"{int(df['observations'].min())}/"
        f"{int(df['expected_observations'].min())} observations | "
        f"100% coverage"
    )

    return True


# ============================================================
# FAILED GRANULE DETECTION
# ============================================================

def failed_log_exists(month):
    failed_log = FAILED_LOG_DIR / f"failed_granules_{month}.csv"

    if not failed_log.exists():
        return False

    try:
        df = pd.read_csv(failed_log)

        if df.empty:
            return False

        return True

    except Exception:
        return True


# ============================================================
# RUN EXTRACTOR
# ============================================================

def run_extractor(month):
    print()
    print("=" * 70)
    print(f"EXTRACTING {month}")
    print("=" * 70)

    result = subprocess.run(
        [
            sys.executable,
            "src/extract_monthly_production.py",
            month,
        ]
    )

    return result.returncode == 0


# ============================================================
# RUN AUTOMATIC RECOVERY
# ============================================================

def run_recovery(month):
    print()
    print("=" * 70)
    print(f"AUTOMATIC RECOVERY: {month}")
    print("=" * 70)

    result = subprocess.run(
        [
            sys.executable,
            "src/recover_failed_granules.py",
            month,
        ]
    )

    return result.returncode == 0


# ============================================================
# PROCESS MONTH
# ============================================================

def process_month(month):
    output_file = MONTHLY_DIR / f"{month}.csv"

    print()
    print("#" * 70)
    print(f"PROCESSING MONTH: {month}")
    print("#" * 70)

    # --------------------------------------------------------
    # Existing output
    # --------------------------------------------------------

    if output_file.exists():

        print(f"📄 Existing output found: {output_file}")

        # First validate existing output.
        if validate_month(month):

            # Even if output is valid, check whether a failed
            # log exists. A failed log means the historical
            # extraction had missing granules.
            if failed_log_exists(month):

                print(
                    f"⚠️ Failed-granule log exists for {month}. "
                    f"Checking automatic recovery..."
                )

                if not run_recovery(month):
                    print(f"❌ Recovery failed: {month}")
                    return False

                return validate_month(month)

            print(f"⏭️ SKIP {month}: already complete")
            return True

        print(
            f"⚠️ Existing output failed strict validation. "
            f"Rebuilding {month}."
        )

    # --------------------------------------------------------
    # Extraction
    # --------------------------------------------------------

    if not run_extractor(month):
        print(f"❌ Extraction process failed: {month}")
        return False

    # --------------------------------------------------------
    # Automatic recovery
    # --------------------------------------------------------

    if failed_log_exists(month):

        print(
            f"⚠️ Failed granules detected for {month}."
        )

        if not run_recovery(month):
            print(f"❌ Automatic recovery failed: {month}")
            return False

    # --------------------------------------------------------
    # Final validation
    # --------------------------------------------------------

    if not validate_month(month):
        print(f"❌ FINAL VALIDATION FAILED: {month}")
        return False

    return True


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="EarthTrend Detective monthly production pipeline"
    )

    parser.add_argument(
        "--start",
        help="Start month YYYY-MM",
    )

    parser.add_argument(
        "--end",
        help="End month YYYY-MM",
    )

    args = parser.parse_args()

    months = load_months()

    if args.start:
        months = [m for m in months if m >= args.start]

    if args.end:
        months = [m for m in months if m <= args.end]

    if not months:
        print("❌ No months selected")
        return 1

    print()
    print("=" * 70)
    print("EARTH TREND DETECTIVE")
    print("MONTHLY PRODUCTION PIPELINE")
    print("=" * 70)
    print()
    print(f"Months selected: {len(months)}")
    print(f"Range: {months[0]} → {months[-1]}")
    print()
    print("Strict completeness requirement:")
    print(f"  Cells: {EXPECTED_CELLS}")
    print("  Coverage: 100%")
    print("  Observations must equal expected observations")
    print()

    completed = []
    failed = []

    for month in months:

        try:
            success = process_month(month)

        except KeyboardInterrupt:
            print()
            print("⚠️ Pipeline interrupted by user.")
            return 130

        except Exception as exc:
            print()
            print(f"❌ Unexpected error in {month}: {exc}")
            success = False

        if success:
            completed.append(month)
        else:
            failed.append(month)

            print()
            print("🛑 STOPPING PIPELINE")
            print(f"Failed month: {month}")
            break

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("PIPELINE SUMMARY")
    print("=" * 70)

    print(f"Completed: {len(completed)}")

    if completed:
        print("  " + ", ".join(completed))

    print(f"Failed: {len(failed)}")

    if failed:
        print("  " + ", ".join(failed))

    print()

    if failed:
        print("❌ OVERALL STATUS: FAILED")
        return 1

    print("✅ OVERALL STATUS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
