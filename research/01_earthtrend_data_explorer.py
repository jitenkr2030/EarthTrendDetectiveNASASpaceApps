import marimo

__generated_with = "0.25.0"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import matplotlib.pyplot as plt
    from pathlib import Path

    return Path, mo, pd, plt


@app.cell
def _(Path, pd):
    DATA_DIR = Path("data/monthly")
    files = sorted(DATA_DIR.glob("2015-*.csv"))

    rows = []

    for file in files:
        df = pd.read_csv(file)

        rows.append({
            "month": df["month"].iloc[0],
            "cells": len(df),
            "observations_min": int(df["observations"].min()),
            "observations_max": int(df["observations"].max()),
            "mean_soil_moisture": df["soil_moisture_mean"].mean(),
        })

    monthly_summary = pd.DataFrame(rows)
    return files, monthly_summary


@app.cell
def _(mo, monthly_summary):
    mo.md(f"""
    # 🌍 EarthTrend Detective — Data Explorer

    **Study region:** Jharkhand, India

    **Dataset:** NASA SMAP L4 Surface Soil Moisture

    **Period:** {monthly_summary["month"].min()}
    → {monthly_summary["month"].max()}

    **Monthly datasets:** {len(monthly_summary)}

    **Grid cells:** 984
    """)
    return


@app.cell
def _(mo, monthly_summary):
    mo.vstack([
        mo.md("## Monthly Dataset Validation"),
        mo.ui.table(monthly_summary),
    ])
    return


@app.cell
def _(monthly_summary, plt):
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(
        monthly_summary["month"],
        monthly_summary["mean_soil_moisture"],
        marker="o",
    )

    ax.set_xlabel("Month")
    ax.set_ylabel("Surface soil moisture (m³/m³)")
    ax.set_title("Jharkhand — Monthly Mean Surface Soil Moisture")

    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    return (fig,)


@app.cell
def _(fig, mo):
    mo.mpl.interactive(fig)
    return


@app.cell
def _(files, mo):
    options = {
        file.stem: file
        for file in files
    }

    month_selector = mo.ui.dropdown(
        options=list(options.keys()),
        value=list(options.keys())[0],
        label="Select month",
    )
    return month_selector, options


@app.cell
def _(mo, month_selector, options, pd):
    selected_file = options[month_selector.value]
    selected_df = pd.read_csv(selected_file)

    mean_value = selected_df["soil_moisture_mean"].mean()
    min_value = selected_df["soil_moisture_mean"].min()
    max_value = selected_df["soil_moisture_mean"].max()

    mo.vstack([
        month_selector,

        mo.md(
            f"""
            ### Selected month: {month_selector.value}

            **Cells:** {len(selected_df)}

            **Mean:** {mean_value:.6f} m³/m³

            **Minimum:** {min_value:.6f}

            **Maximum:** {max_value:.6f}
            """
        ),

        mo.ui.table(selected_df.head(20)),
    ])
    return


if __name__ == "__main__":
    app.run()
