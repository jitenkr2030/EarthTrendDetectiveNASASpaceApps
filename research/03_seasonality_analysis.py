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
    data_dir = Path("data/monthly")

    # Automatically discover every YYYY-MM.csv monthly dataset.
    files = sorted(data_dir.glob("????-??.csv"))

    if not files:
        raise FileNotFoundError(
            "No monthly CSV files found in data/monthly/"
        )

    frames = []

    for file in files:
        df = pd.read_csv(file)

        if "month" not in df.columns:
            raise ValueError(f"'month' column missing in {file.name}")

        df["source_file"] = file.name
        frames.append(df)

    all_data = pd.concat(frames, ignore_index=True)

    all_data["month"] = pd.to_datetime(
        all_data["month"], errors="raise"
    ).dt.to_period("M").astype(str)

    all_data["month_number"] = pd.to_datetime(
        all_data["month"]
    ).dt.month

    all_data["year"] = pd.to_datetime(
        all_data["month"]
    ).dt.year

    all_data["soil_moisture_mean"] = pd.to_numeric(
        all_data["soil_moisture_mean"], errors="coerce"
    )

    # One spatial summary per month: each monthly file contributes
    # one state-wide mean, based on its grid-cell observations.
    monthly_summary = (
        all_data.groupby("month")
        .agg(
            mean_soil_moisture=("soil_moisture_mean", "mean"),
            median_soil_moisture=("soil_moisture_mean", "median"),
            spatial_std=("soil_moisture_mean", "std"),
            minimum=("soil_moisture_mean", "min"),
            maximum=("soil_moisture_mean", "max"),
            cells=("soil_moisture_mean", "count"),
        )
        .reset_index()
    )

    monthly_summary["month_number"] = pd.to_datetime(
        monthly_summary["month"]
    ).dt.month

    monthly_summary["year"] = pd.to_datetime(
        monthly_summary["month"]
    ).dt.year

    monthly_summary["month_name"] = pd.to_datetime(
        monthly_summary["month"]
    ).dt.strftime("%b %Y")

    return all_data, files, monthly_summary


@app.cell
def _(all_data, monthly_summary, pd):
    # Exploratory calendar-month comparison across available years.
    # Months with one year of data are less informative than those
    # represented in both 2015 and 2016.
    seasonal_summary = (
        monthly_summary.groupby("month_number")
        .agg(
            mean_soil_moisture=("mean_soil_moisture", "mean"),
            variation_between_months=("mean_soil_moisture", "std"),
            years_observed=("year", "nunique"),
            monthly_values=("month", "count"),
        )
        .reset_index()
    )

    seasonal_summary["month_name"] = pd.to_datetime(
        seasonal_summary["month_number"], format="%m"
    ).dt.strftime("%B")

    # Keep calendar order, January to December.
    seasonal_summary = seasonal_summary.sort_values(
        "month_number"
    ).reset_index(drop=True)

    # Cell-specific calendar-month baseline. This is exploratory,
    # not a long-term climatological normal.
    cell_baseline = (
        all_data.groupby(["row", "col", "month_number"])[
            "soil_moisture_mean"
        ]
        .mean()
        .rename("seasonal_baseline")
        .reset_index()
    )

    anomaly_data = all_data.merge(
        cell_baseline,
        on=["row", "col", "month_number"],
        how="left",
        validate="many_to_one",
    )

    anomaly_data["anomaly"] = (
        anomaly_data["soil_moisture_mean"]
        - anomaly_data["seasonal_baseline"]
    )

    anomaly_summary = (
        anomaly_data.groupby("month")
        .agg(
            mean_anomaly=("anomaly", "mean"),
            cells=("anomaly", "count"),
        )
        .reset_index()
    )

    anomaly_summary["mean_anomaly"] = (
        anomaly_summary["mean_anomaly"].round(5)
    )

    return seasonal_summary, anomaly_summary


@app.cell
def _(mo, files, monthly_summary, seasonal_summary):
    mo.vstack([
        mo.md("""
        # 🌧️ EarthTrend Detective — Seasonality Analysis

        This notebook explores monthly and calendar-season patterns
        in NASA SMAP surface soil moisture across the Jharkhand grid.

        **Study period:** April 2015 – December 2016

        **Interpretation:** This is exploratory analysis using a short
        record. It is not a long-term climate trend or established
        climatological normal.
        """),
        mo.md(
            f"**Monthly files loaded:** {len(files)}  \n"
            f"**Monthly summaries:** {len(monthly_summary)}"
        ),
        mo.md("## Calendar-month summary"),
        mo.ui.table(seasonal_summary),
    ])

    return


@app.cell
def _(plt, monthly_summary, mo):
    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(
        monthly_summary["month"],
        monthly_summary["mean_soil_moisture"],
        marker="o",
    )

    ax.set_xlabel("Month")
    ax.set_ylabel("Mean surface soil moisture (m³/m³)")
    ax.set_title("Jharkhand: Monthly Mean Surface Soil Moisture")
    ax.tick_params(axis="x", rotation=60)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    mo.mpl.interactive(fig)

    return


@app.cell
def _(mo, monthly_summary):
    display_monthly = monthly_summary.copy()

    numeric_columns = [
        "mean_soil_moisture",
        "median_soil_moisture",
        "spatial_std",
        "minimum",
        "maximum",
    ]

    display_monthly[numeric_columns] = (
        display_monthly[numeric_columns].round(5)
    )

    mo.vstack([
        mo.md("## Monthly spatial summary"),
        mo.md(
            "Each row summarizes the 984 grid cells for one month. "
            "The spatial standard deviation describes differences "
            "among cells in that month; it is not measurement uncertainty."
        ),
        mo.ui.table(display_monthly),
    ])

    return


@app.cell
def _(mo, anomaly_summary):
    mo.vstack([
        mo.md("## Exploratory soil-moisture anomalies"),
        mo.md("""
        Each cell's observation is compared with that same cell's
        average for the corresponding calendar month in the available
        dataset.

        **Positive anomaly:** above that cell's available-record
        calendar-month average.

        **Negative anomaly:** below that cell's available-record
        calendar-month average.

        Because the baseline uses this short dataset itself, these
        anomalies are relative comparisons, not proof of drought,
        climate change, or unusual conditions against a long-term norm.
        """),
        mo.ui.table(anomaly_summary),
    ])

    return


if __name__ == "__main__":
    app.run()
