from pathlib import Path
import json
import math
import time

import numpy as np
import pandas as pd
from scipy.stats import false_discovery_control


# ============================================================
# EARTH TREND DETECTIVE
# MODULE 13 - SPATIAL TREND & HOTSPOT DETECTION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "analysis"
    / "smap_seasonal_cell_trends.csv"
)

OUTPUT_DIR = BASE_DIR / "data" / "analysis"

OUTPUT_FILE = (
    OUTPUT_DIR
    / "smap_spatial_trend_hotspots.csv"
)

SUMMARY_FILE = (
    OUTPUT_DIR
    / "smap_spatial_trend_summary.csv"
)

SIGNIFICANT_FILE = (
    OUTPUT_DIR
    / "smap_significant_spatial_cells.csv"
)

MANIFEST_FILE = (
    OUTPUT_DIR
    / "smap_spatial_trend_manifest.json"
)

ALPHA = 0.05

EXPECTED_CELLS = 984
EXPECTED_CELL_SEASON_ROWS = 3936

SEASONS = [
    "winter",
    "pre-monsoon",
    "monsoon",
    "post-monsoon",
]


# ============================================================
# BENJAMINI-HOCHBERG FDR
# ============================================================

def benjamini_hochberg(p_values):
    """
    Benjamini-Hochberg FDR adjusted p-values.

    Returns adjusted p-values in the same order
    as the input.
    """

    p = np.asarray(p_values, dtype=float)

    n = len(p)

    if n == 0:
        return np.array([], dtype=float)

    order = np.argsort(p)

    sorted_p = p[order]

    adjusted = np.empty(n, dtype=float)

    running_min = 1.0

    for i in range(n - 1, -1, -1):

        rank = i + 1

        value = (
            sorted_p[i]
            * n
            / rank
        )

        running_min = min(
            running_min,
            value
        )

        adjusted[i] = running_min

    result = np.empty(n, dtype=float)

    result[order] = np.minimum(
        adjusted,
        1.0
    )

    return result


# ============================================================
# GRID NEIGHBOR DETECTION
# ============================================================

def build_neighbors(cells):
    """
    Build 8-connected spatial neighbors using row/col.

    A cell is considered adjacent if:
        abs(row difference) <= 1
        abs(col difference) <= 1
        and it is not itself.
    """

    lookup = {
        (int(row), int(col)): True
        for row, col in zip(
            cells["row"],
            cells["col"]
        )
    }

    neighbors = {}

    for row, col in lookup.keys():

        current = []

        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:

                if dr == 0 and dc == 0:
                    continue

                key = (
                    row + dr,
                    col + dc
                )

                if key in lookup:
                    current.append(key)

        neighbors[(row, col)] = current

    return neighbors


# ============================================================
# MAIN
# ============================================================

def main():

    start_time = time.time()

    print("=" * 70)
    print("EARTH TREND DETECTIVE")
    print("MODULE 13 - SPATIAL TREND & HOTSPOT DETECTION")
    print("=" * 70)

    # ========================================================
    # 1. LOAD
    # ========================================================

    print("\n[1/9] Loading seasonal cell trends...")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    print(f"Loaded rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    if len(df) != EXPECTED_CELL_SEASON_ROWS:
        raise ValueError(
            f"Expected {EXPECTED_CELL_SEASON_ROWS:,} rows, "
            f"found {len(df):,}."
        )

    # ========================================================
    # 2. VALIDATE
    # ========================================================

    print("\n[2/9] Validating input...")

    required = {
        "season",
        "row",
        "col",
        "latitude",
        "longitude",
        "years_available",
        "sen_slope_per_year",
        "kendall_tau",
        "p_value",
        "significant_at_0_05",
        "trend_class",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing columns: {sorted(missing)}"
        )

    df["season"] = df["season"].astype(str)

    df["row"] = pd.to_numeric(
        df["row"],
        errors="coerce"
    )

    df["col"] = pd.to_numeric(
        df["col"],
        errors="coerce"
    )

    df["latitude"] = pd.to_numeric(
        df["latitude"],
        errors="coerce"
    )

    df["longitude"] = pd.to_numeric(
        df["longitude"],
        errors="coerce"
    )

    df["sen_slope_per_year"] = pd.to_numeric(
        df["sen_slope_per_year"],
        errors="coerce"
    )

    df["kendall_tau"] = pd.to_numeric(
        df["kendall_tau"],
        errors="coerce"
    )

    df["p_value"] = pd.to_numeric(
        df["p_value"],
        errors="coerce"
    )

    if df[
        [
            "row",
            "col",
            "latitude",
            "longitude",
            "sen_slope_per_year",
            "kendall_tau",
            "p_value",
        ]
    ].isna().any().any():

        raise ValueError(
            "Input contains invalid numeric values."
        )

    if not set(df["season"]).issubset(set(SEASONS)):
        raise ValueError(
            "Unexpected season found."
        )

    if (df["p_value"] < 0).any() or (
        df["p_value"] > 1
    ).any():

        raise ValueError(
            "Invalid p-values detected."
        )

    # ========================================================
    # 3. GRID VALIDATION
    # ========================================================

    print("\n[3/9] Validating spatial grid...")

    unique_cells = (
        df[
            [
                "row",
                "col",
                "latitude",
                "longitude",
            ]
        ]
        .drop_duplicates(
            subset=["row", "col"]
        )
    )

    if len(unique_cells) != EXPECTED_CELLS:
        raise ValueError(
            f"Expected {EXPECTED_CELLS} cells, "
            f"found {len(unique_cells)}."
        )

    season_counts = (
        df.groupby("season")[
            ["row", "col"]
        ]
        .apply(
            lambda x: len(
                x.drop_duplicates()
            ),
            include_groups=False,
        )
        .to_dict()
    )

    for season in SEASONS:

        count = int(
            season_counts.get(
                season,
                0
            )
        )

        print(
            f"{season:15s} "
            f"cells={count}"
        )

        if count != EXPECTED_CELLS:
            raise ValueError(
                f"{season}: expected "
                f"{EXPECTED_CELLS} cells, "
                f"found {count}."
            )

    print("Spatial grid validation: PASS")

    # ========================================================
    # 4. RAW SIGNIFICANCE
    # ========================================================

    print("\n[4/9] Evaluating raw statistical significance...")

    df["raw_significant"] = (
        df["p_value"] < ALPHA
    )

    raw_count = int(
        df["raw_significant"].sum()
    )

    print(
        f"Raw p < {ALPHA}: "
        f"{raw_count:,} cell-season results"
    )

    # ========================================================
    # 5. FDR CORRECTION
    # ========================================================

    print(
        "\n[5/9] Applying Benjamini-Hochberg FDR correction..."
    )

    df["fdr_p_value"] = np.nan

    # Correction is performed separately for each season.
    #
    # This is appropriate because each season represents
    # a separate scientific family of spatial hypotheses.

    for season in SEASONS:

        mask = (
            df["season"] == season
        )

        p_values = df.loc[
            mask,
            "p_value"
        ].to_numpy(
            dtype=float
        )

        adjusted = benjamini_hochberg(
            p_values
        )

        df.loc[
            mask,
            "fdr_p_value"
        ] = adjusted

    df["fdr_significant"] = (
        df["fdr_p_value"] < ALPHA
    )

    fdr_count = int(
        df["fdr_significant"].sum()
    )

    print(
        f"FDR-adjusted p < {ALPHA}: "
        f"{fdr_count:,} cell-season results"
    )

    # ========================================================
    # 6. SPATIAL NEIGHBOR ANALYSIS
    # ========================================================

    print("\n[6/9] Building spatial neighborhood structure...")

    neighbors = build_neighbors(
        unique_cells
    )

    neighbor_counts = [
        len(v)
        for v in neighbors.values()
    ]

    print(
        f"Mean neighbors/cell: "
        f"{np.mean(neighbor_counts):.2f}"
    )

    print(
        f"Minimum neighbors/cell: "
        f"{np.min(neighbor_counts)}"
    )

    print(
        f"Maximum neighbors/cell: "
        f"{np.max(neighbor_counts)}"
    )

    # Map each season to significant cells
    significant_sets = {}

    for season in SEASONS:

        sub = df[
            (df["season"] == season)
            & (df["fdr_significant"])
        ]

        significant_sets[season] = {
            (
                int(r),
                int(c)
            )
            for r, c in zip(
                sub["row"],
                sub["col"]
            )
        }

    # ========================================================
    # 7. SPATIAL CLUSTER CLASSIFICATION
    # ========================================================

    print("\n[7/9] Classifying spatial evidence...")

    spatial_cluster_counts = {}

    cluster_labels = []

    for index, record in df.iterrows():

        season = record["season"]

        key = (
            int(record["row"]),
            int(record["col"])
        )

        slope = float(
            record["sen_slope_per_year"]
        )

        fdr_significant = bool(
            record["fdr_significant"]
        )

        season_significant = (
            significant_sets[season]
        )

        neighbor_keys = neighbors.get(
            key,
            []
        )

        significant_neighbors = sum(
            1
            for neighbor in neighbor_keys
            if neighbor in season_significant
        )

        same_direction_neighbors = 0

        if slope > 0:

            same_direction_neighbors = sum(
                1
                for neighbor in neighbor_keys
                if neighbor in season_significant
                and float(
                    df.loc[
                        (
                            (df["season"] == season)
                            & (df["row"] == neighbor[0])
                            & (df["col"] == neighbor[1])
                        ),
                        "sen_slope_per_year",
                    ].iloc[0]
                ) > 0
            )

        elif slope < 0:

            same_direction_neighbors = sum(
                1
                for neighbor in neighbor_keys
                if neighbor in season_significant
                and float(
                    df.loc[
                        (
                            (df["season"] == season)
                            & (df["row"] == neighbor[0])
                            & (df["col"] == neighbor[1])
                        ),
                        "sen_slope_per_year",
                    ].iloc[0]
                ) < 0
            )

        # ----------------------------------------------------
        # Classification
        # ----------------------------------------------------

        if not fdr_significant:

            label = "not-significant"

        elif (
            fdr_significant
            and same_direction_neighbors >= 2
        ):

            label = "spatial-hotspot"

        elif (
            fdr_significant
            and significant_neighbors >= 1
        ):

            label = "spatial-cluster"

        else:

            label = "isolated-significant"

        cluster_labels.append(
            label
        )

    df["spatial_class"] = cluster_labels

    # ========================================================
    # 8. SUMMARY
    # ========================================================

    print("\n[8/9] Creating spatial summaries...")

    summary_rows = []

    for season in SEASONS:

        sub = df[
            df["season"] == season
        ]

        raw = int(
            sub["raw_significant"].sum()
        )

        fdr = int(
            sub["fdr_significant"].sum()
        )

        hotspots = int(
            (
                sub["spatial_class"]
                == "spatial-hotspot"
            ).sum()
        )

        clusters = int(
            (
                sub["spatial_class"]
                == "spatial-cluster"
            ).sum()
        )

        isolated = int(
            (
                sub["spatial_class"]
                == "isolated-significant"
            ).sum()
        )

        increasing = int(
            (
                sub["sen_slope_per_year"]
                > 0
            ).sum()
        )

        decreasing = int(
            (
                sub["sen_slope_per_year"]
                < 0
            ).sum()
        )

        mean_slope = float(
            sub["sen_slope_per_year"].mean()
        )

        summary_rows.append(
            {
                "season": season,
                "cells": len(sub),
                "raw_significant": raw,
                "fdr_significant": fdr,
                "spatial_hotspots": hotspots,
                "spatial_clusters": clusters,
                "isolated_significant": isolated,
                "increasing_cells": increasing,
                "decreasing_cells": decreasing,
                "mean_sen_slope_per_year": mean_slope,
                "fdr_significant_fraction": (
                    fdr / len(sub)
                ),
            }
        )

    summary_df = pd.DataFrame(
        summary_rows
    )

    print("\nSPATIAL SUMMARY")
    print("-" * 70)

    for _, result in summary_df.iterrows():

        print(
            f"{result['season']:15s} "
            f"raw={int(result['raw_significant']):3d} "
            f"FDR={int(result['fdr_significant']):3d} "
            f"hotspot={int(result['spatial_hotspots']):3d} "
            f"cluster={int(result['spatial_clusters']):3d} "
            f"isolated={int(result['isolated_significant']):3d}"
        )

    # --------------------------------------------------------
    # Significant inventory
    # --------------------------------------------------------

    significant_df = df[
        df["fdr_significant"]
    ].copy()

    significant_df = significant_df[
        [
            "season",
            "row",
            "col",
            "latitude",
            "longitude",
            "sen_slope_per_year",
            "kendall_tau",
            "p_value",
            "fdr_p_value",
            "trend_class",
            "spatial_class",
        ]
    ].sort_values(
        [
            "season",
            "fdr_p_value",
        ]
    )

    # ========================================================
    # 9. WRITE + VALIDATE
    # ========================================================

    print("\n[9/9] Writing outputs...")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    summary_df.to_csv(
        SUMMARY_FILE,
        index=False
    )

    significant_df.to_csv(
        SIGNIFICANT_FILE,
        index=False
    )

    # Reload
    check_main = pd.read_csv(
        OUTPUT_FILE
    )

    check_summary = pd.read_csv(
        SUMMARY_FILE
    )

    check_significant = pd.read_csv(
        SIGNIFICANT_FILE
    )

    if len(check_main) != EXPECTED_CELL_SEASON_ROWS:
        raise ValueError(
            "Main spatial output validation failed."
        )

    if len(check_summary) != 4:
        raise ValueError(
            "Summary output validation failed."
        )

    if len(check_significant) != fdr_count:
        raise ValueError(
            "Significant inventory validation failed."
        )

    if check_main[
        [
            "season",
            "row",
            "col",
        ]
    ].duplicated().any():

        raise ValueError(
            "Duplicate season-cell results found."
        )

    # ========================================================
    # MANIFEST
    # ========================================================

    hotspot_count = int(
        (
            df["spatial_class"]
            == "spatial-hotspot"
        ).sum()
    )

    cluster_count = int(
        (
            df["spatial_class"]
            == "spatial-cluster"
        ).sum()
    )

    isolated_count = int(
        (
            df["spatial_class"]
            == "isolated-significant"
        ).sum()
    )

    manifest = {
        "module": "13_spatial_trend",
        "status": "PASS",

        "input": str(INPUT_FILE),

        "dataset": {
            "cells": EXPECTED_CELLS,
            "cell_season_rows": EXPECTED_CELL_SEASON_ROWS,
            "seasons": SEASONS,
        },

        "statistics": {
            "alpha": ALPHA,
            "raw_significant_results": raw_count,
            "fdr_significant_results": fdr_count,
            "spatial_hotspot_results": hotspot_count,
            "spatial_cluster_results": cluster_count,
            "isolated_significant_results": isolated_count,
        },

        "multiple_testing": {
            "method": "Benjamini-Hochberg FDR",
            "family": "each season separately",
            "threshold": ALPHA,
        },

        "spatial_method": {
            "grid": "SMAP row/col grid",
            "connectivity": "8-connected",
            "hotspot_rule":
                "FDR-significant cell with at least "
                "2 same-direction FDR-significant neighbors",
            "cluster_rule":
                "FDR-significant cell with at least "
                "1 FDR-significant neighbor",
        },

        "interpretation_note":
            "Spatial hotspot labels indicate statistical "
            "and local spatial clustering evidence. "
            "They do not by themselves establish a "
            "physical cause or causal mechanism.",

        "outputs": {
            "main": str(OUTPUT_FILE),
            "summary": str(SUMMARY_FILE),
            "significant_inventory": str(SIGNIFICANT_FILE),
            "manifest": str(MANIFEST_FILE),
        },

        "validation": {
            "main_rows_pass":
                len(check_main) == EXPECTED_CELL_SEASON_ROWS,
            "summary_rows_pass":
                len(check_summary) == 4,
            "significant_inventory_pass":
                len(check_significant) == fdr_count,
            "duplicate_check_pass":
                not check_main[
                    [
                        "season",
                        "row",
                        "col",
                    ]
                ].duplicated().any(),
            "status":
                "PASS",
        },
    }

    with open(
        MANIFEST_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            manifest,
            f,
            indent=2
        )

    elapsed = time.time() - start_time

    # ========================================================
    # FINAL
    # ========================================================

    print("\n" + "=" * 70)
    print("MODULE 13 COMPLETE")
    print("=" * 70)

    print(
        f"Input cell-season results: "
        f"{len(check_main):,}"
    )

    print(
        f"Raw significant: "
        f"{raw_count:,}"
    )

    print(
        f"FDR significant: "
        f"{fdr_count:,}"
    )

    print(
        f"Spatial hotspots: "
        f"{hotspot_count:,}"
    )

    print(
        f"Spatial clusters: "
        f"{cluster_count:,}"
    )

    print(
        f"Isolated significant: "
        f"{isolated_count:,}"
    )

    print("\nOutputs:")
    print(OUTPUT_FILE)
    print(SUMMARY_FILE)
    print(SIGNIFICANT_FILE)
    print(MANIFEST_FILE)

    print(
        f"\nRuntime: {elapsed:.2f} seconds"
    )

    print("\nSTATUS: PASS")
    print("=" * 70)


if __name__ == "__main__":
    main()
