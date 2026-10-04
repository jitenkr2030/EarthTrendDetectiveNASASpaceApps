import marimo

__generated_with = "0.25.0"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    from pathlib import Path
    import re

    return mo, pd, Path, re


@app.cell
def _(pd, Path, re):
    data_dir = Path("data/monthly")

    files = sorted(
        p for p in data_dir.glob("*.csv")
        if re.fullmatch(r"\d{4}-\d{2}\.csv", p.name)
    )

    if not files:
        raise ValueError("No monthly CSV files found.")

    available_months = [p.stem for p in files]

    expected_months = pd.period_range(
        available_months[0],
        available_months[-1],
        freq="M",
    ).astype(str).tolist()

    missing_months = sorted(
        set(expected_months) - {p.stem for p in files}
    )

    required = {
        "month", "row", "col", "latitude", "longitude",
        "soil_moisture_mean", "observations", "coverage_fraction",
    }

    results = []
    reference_grid = None

    for file in files:
        errors = []

        try:
            df = pd.read_csv(file)
            absent = required - set(df.columns)

            if absent:
                results.append({
                    "month": file.stem,
                    "rows": len(df),
                    "status": "FAIL",
                    "errors": "Missing columns: " + ", ".join(sorted(absent)),
                })
                continue

            numeric = [
                "row", "col", "latitude", "longitude",
                "soil_moisture_mean", "observations",
                "coverage_fraction",
            ]
            for col in numeric:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            n = len(df)
            unique_cells = df[["row", "col"]].drop_duplicates().shape[0]
            duplicate_cells = n - unique_cells

            month_values = df["month"].dropna().astype(str).str[:7].unique()
            if len(month_values) != 1 or month_values[0] != file.stem:
                errors.append("month does not match filename")

            if n != 984:
                errors.append(f"expected 984 rows; found {n}")
            if unique_cells != 984:
                errors.append(f"expected 984 unique cells; found {unique_cells}")
            if duplicate_cells:
                errors.append(f"{duplicate_cells} duplicate cells")

            sm = df["soil_moisture_mean"]
            valid_sm = sm.dropna()
            if sm.isna().any():
                errors.append(f"{int(sm.isna().sum())} missing soil-moisture values")
            if len(valid_sm) == 0 or (valid_sm < 0).any() or (valid_sm > 0.9).any():
                errors.append("soil moisture outside valid range 0–0.9")

            lat, lon = df["latitude"], df["longitude"]
            if lat.isna().any() or lon.isna().any():
                errors.append("missing coordinates")
            if (
                ((lat < -90) | (lat > 90)).fillna(True).any()
                or ((lon < -180) | (lon > 180)).fillna(True).any()
            ):
                errors.append("invalid coordinates")

            obs = df["observations"]
            valid_obs = obs.dropna()
            if (
                len(valid_obs) != n
                or (valid_obs <= 0).any()
                or (valid_obs % 1 != 0).any()
            ):
                errors.append("invalid observation counts")
            elif valid_obs.nunique() != 1:
                errors.append("observation counts differ across cells")

            coverage = df["coverage_fraction"]
            if (
                coverage.isna().any()
                or (coverage < 0.999999).any()
                or (coverage > 1.000001).any()
            ):
                errors.append("coverage is not 100% for every cell")

            grid = set(zip(df["row"].tolist(), df["col"].tolist()))
            if reference_grid is None and len(grid) == 984:
                reference_grid = grid
            grid_ok = reference_grid is not None and grid == reference_grid
            if not grid_ok:
                errors.append("grid differs from reference month")

            results.append({
                "month": file.stem,
                "rows": n,
                "unique_cells": unique_cells,
                "duplicate_cells": duplicate_cells,
                "observations_min": valid_obs.min() if len(valid_obs) else None,
                "observations_max": valid_obs.max() if len(valid_obs) else None,
                "coverage_min": coverage.min(),
                "coverage_max": coverage.max(),
                "soil_moisture_min": valid_sm.min() if len(valid_sm) else None,
                "soil_moisture_max": valid_sm.max() if len(valid_sm) else None,
                "grid_matches_reference": grid_ok,
                "status": "PASS" if not errors else "FAIL",
                "errors": "; ".join(errors),
            })

        except Exception as exc:
            results.append({
                "month": file.stem,
                "rows": 0,
                "status": "FAIL",
                "errors": f"Could not read/validate file: {exc}",
            })

    quality = pd.DataFrame(results)

    return quality, expected_months, missing_months


@app.cell
def _(mo, quality, expected_months, missing_months):
    total = len(quality)
    passed = int((quality["status"] == "PASS").sum()) if total else 0
    failed = int((quality["status"] == "FAIL").sum()) if total else 0

    overall_pass = (
        total == len(expected_months)
        and not missing_months
        and failed == 0
    )

    mo.md(f"""
    # 🛡️ EarthTrend Detective — Data Quality Gate

    **Study period:** {expected_months[0]} – {expected_months[-1]}

    **Expected months:** {len(expected_months)}

    **Monthly files inspected:** {total}

    **PASS:** {passed}

    **FAIL:** {failed}

    **Missing months:** {len(missing_months)}

    {"## ✅ OVERALL QUALITY GATE: PASS" if overall_pass else "## ❌ OVERALL QUALITY GATE: FAIL"}

    {"All expected monthly files passed the configured checks." if overall_pass else "Investigate failed files or missing months before scientific analysis."}

    {"**Missing months:** " + ", ".join(missing_months) if missing_months else ""}
    """)

    return


@app.cell
def _(mo, quality):
    display = quality.copy()

    for column in [
        "coverage_min", "coverage_max",
        "soil_moisture_min", "soil_moisture_max",
    ]:
        if column in display.columns:
            display[column] = display[column].round(4)

    mo.ui.table(display)
    return


@app.cell
def _(mo, quality):
    failed_rows = quality[quality["status"] == "FAIL"]

    if failed_rows.empty:
        result = mo.md("""
        ## Monthly checks passed

        No monthly file failed the configured checks. This does not
        establish a long-term climate or soil-moisture trend.
        """)
    else:
        result = mo.vstack([
            mo.md("## Files requiring investigation"),
            mo.ui.table(failed_rows),
        ])

    result

    return


if __name__ == "__main__":
    app.run()
