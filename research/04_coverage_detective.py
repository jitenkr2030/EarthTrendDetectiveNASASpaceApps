import marimo

__generated_with = "0.25.0"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import matplotlib.pyplot as plt
    from pathlib import Path

    return mo, pd, plt, Path


@app.cell
def _(Path, pd):
    DATA_DIR = Path("data/monthly")

    files = sorted(DATA_DIR.glob("2015-*.csv"))

    frames = []

    for file in files:
        df = pd.read_csv(file)
        frames.append(df)

    all_data = pd.concat(frames, ignore_index=True)

    return all_data, files


@app.cell
def _(all_data, pd):
    expected_months = sorted(all_data["month"].unique())

    expected_count = len(expected_months)

    cell_coverage = (
        all_data
        .groupby(["row", "col", "latitude", "longitude"])
        .agg(
            months_available=("month", "nunique"),
            observations_total=("observations", "sum"),
            minimum_monthly_coverage=("coverage_fraction", "min"),
            mean_monthly_coverage=("coverage_fraction", "mean"),
        )
        .reset_index()
    )

    cell_coverage["expected_months"] = expected_count

    cell_coverage["coverage_fraction"] = (
        cell_coverage["months_available"]
        / cell_coverage["expected_months"]
    )

    cell_coverage["coverage_percent"] = (
        cell_coverage["coverage_fraction"] * 100
    )

    return cell_coverage, expected_months


@app.cell
def _(cell_coverage, expected_months, mo):
    total_cells = len(cell_coverage)

    complete_cells = (
        cell_coverage["months_available"]
        == len(expected_months)
    ).sum()

    incomplete_cells = total_cells - complete_cells

    min_coverage = cell_coverage["coverage_percent"].min()
    max_coverage = cell_coverage["coverage_percent"].max()

    mo.md(
        f"""
        # 🔎 EarthTrend Detective — Coverage Analysis

        **Months currently available:** {len(expected_months)}

        **Period:** {expected_months[0]} → {expected_months[-1]}

        **Grid cells:** {total_cells}

        **Complete cells:** {complete_cells}

        **Incomplete cells:** {incomplete_cells}

        **Minimum cell coverage:** {min_coverage:.1f}%

        **Maximum cell coverage:** {max_coverage:.1f}%

        > This analysis evaluates data completeness. It does **not**
        determine whether soil moisture has increased or decreased.
        """
    )

    return


@app.cell
def _(cell_coverage, mo):
    coverage_table = cell_coverage[
        [
            "row",
            "col",
            "latitude",
            "longitude",
            "months_available",
            "expected_months",
            "coverage_percent",
            "observations_total",
            "minimum_monthly_coverage",
            "mean_monthly_coverage",
        ]
    ].copy()

    coverage_table["coverage_percent"] = (
        coverage_table["coverage_percent"].round(2)
    )

    mo.ui.table(coverage_table.head(100))

    return


@app.cell
def _(cell_coverage, plt):
    fig, ax = plt.subplots(figsize=(9, 5))

    ax.hist(
        cell_coverage["coverage_percent"],
        bins=20,
    )

    ax.set_xlabel("Cell data coverage (%)")
    ax.set_ylabel("Number of cells")
    ax.set_title("Distribution of Cell Data Coverage")

    ax.grid(True, alpha=0.3)

    fig.tight_layout()

    return fig


@app.cell
def _(fig, mo):
    mo.mpl.interactive(fig)

    return


@app.cell
def _(all_data, mo):
    monthly_coverage = (
        all_data
        .groupby("month")
        .agg(
            cells=("row", "nunique"),
            observations_min=("observations", "min"),
            observations_max=("observations", "max"),
            coverage_min=("coverage_fraction", "min"),
            coverage_mean=("coverage_fraction", "mean"),
            coverage_max=("coverage_fraction", "max"),
        )
        .reset_index()
    )

    monthly_coverage["coverage_min_percent"] = (
        monthly_coverage["coverage_min"] * 100
    )

    monthly_coverage["coverage_mean_percent"] = (
        monthly_coverage["coverage_mean"] * 100
    )

    monthly_coverage["coverage_max_percent"] = (
        monthly_coverage["coverage_max"] * 100
    )

    mo.vstack([
        mo.md("## Monthly Coverage"),
        mo.ui.table(
            monthly_coverage[
                [
                    "month",
                    "cells",
                    "observations_min",
                    "observations_max",
                    "coverage_min_percent",
                    "coverage_mean_percent",
                    "coverage_max_percent",
                ]
            ]
        ),
    ])

    return monthly_coverage


if __name__ == "__main__":
    app.run()
