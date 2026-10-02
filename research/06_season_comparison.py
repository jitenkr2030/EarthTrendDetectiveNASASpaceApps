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

    files = sorted(data_dir.glob("????-??.csv"))

    if not files:
        raise FileNotFoundError(
            "No monthly files found in data/monthly/"
        )

    frames = []

    for file in files:
        df = pd.read_csv(file)

        required = {
            "month",
            "row",
            "col",
            "soil_moisture_mean",
        }

        missing = required - set(df.columns)

        if missing:
            raise ValueError(
                f"{file.name}: missing columns "
                f"{sorted(missing)}"
            )

        df["month"] = pd.to_datetime(
            df["month"],
            errors="raise"
        ).dt.to_period("M").astype(str)

        df["year"] = pd.to_datetime(
            df["month"]
        ).dt.year

        df["month_number"] = pd.to_datetime(
            df["month"]
        ).dt.month

        frames.append(df)

    all_data = pd.concat(
        frames,
        ignore_index=True
    )

    return all_data, files


@app.cell
def _(all_data, pd):
    def assign_season(month):
        if month in [1, 2]:
            return "Winter"
        elif month in [3, 4, 5]:
            return "Pre-monsoon"
        elif month in [6, 7, 8, 9]:
            return "Monsoon"
        else:
            return "Post-monsoon"

    all_data["season"] = (
        all_data["month_number"]
        .map(assign_season)
    )

    season_order = [
        "Winter",
        "Pre-monsoon",
        "Monsoon",
        "Post-monsoon",
    ]

    all_data["season"] = pd.Categorical(
        all_data["season"],
        categories=season_order,
        ordered=True,
    )

    return season_order


@app.cell
def _(all_data, pd):
    # First calculate one mean for each month.
    monthly = (
        all_data
        .groupby(
            ["year", "month", "month_number", "season"],
            observed=True
        )
        ["soil_moisture_mean"]
        .mean()
        .reset_index()
    )

    return monthly


@app.cell
def _(monthly, pd):
    seasonal_yearly = (
        monthly
        .groupby(
            ["year", "season"],
            observed=True
        )
        .agg(
            mean_soil_moisture=(
                "soil_moisture_mean",
                "mean"
            ),
            months_available=(
                "month",
                "count"
            ),
        )
        .reset_index()
    )

    seasonal_yearly["mean_soil_moisture"] = (
        seasonal_yearly["mean_soil_moisture"]
        .round(5)
    )

    return seasonal_yearly


@app.cell
def _(monthly, pd):
    seasonal_overall = (
        monthly
        .groupby(
            "season",
            observed=True
        )
        .agg(
            mean_soil_moisture=(
                "soil_moisture_mean",
                "mean"
            ),
            min_monthly_mean=(
                "soil_moisture_mean",
                "min"
            ),
            max_monthly_mean=(
                "soil_moisture_mean",
                "max"
            ),
            months_available=(
                "month",
                "count"
            ),
            years_available=(
                "year",
                "nunique"
            ),
        )
        .reset_index()
    )

    for column in [
        "mean_soil_moisture",
        "min_monthly_mean",
        "max_monthly_mean",
    ]:
        seasonal_overall[column] = (
            seasonal_overall[column]
            .round(5)
        )

    return seasonal_overall


@app.cell
def _(mo, files, seasonal_overall, seasonal_yearly):
    mo.vstack([
        mo.md("""
        # 🌦️ EarthTrend Detective — Seasonal Comparison

        This analysis groups the available SMAP monthly observations
        into four exploratory seasons:

        - **Winter:** January–February
        - **Pre-monsoon:** March–May
        - **Monsoon:** June–September
        - **Post-monsoon:** October–December

        The objective is to describe the seasonal structure of
        surface soil moisture before attempting long-term trend
        analysis.

        **Important:** The current record is only April 2015 –
        December 2016. Seasonal values are therefore exploratory,
        not long-term climatological normals.
        """),

        mo.md(
            f"**Monthly files loaded:** {len(files)}"
        ),

        mo.md("## Overall seasonal comparison"),

        mo.ui.table(seasonal_overall),

        mo.md("## Year-wise seasonal comparison"),

        mo.ui.table(seasonal_yearly),
    ])

    return


@app.cell
def _(plt, seasonal_yearly):
    plot_data = seasonal_yearly.copy()

    fig, ax = plt.subplots(figsize=(10, 5))

    for year in sorted(plot_data["year"].unique()):
        subset = plot_data[
            plot_data["year"] == year
        ]

        ax.plot(
            subset["season"].astype(str),
            subset["mean_soil_moisture"],
            marker="o",
            label=str(year),
        )

    ax.set_xlabel("Season")
    ax.set_ylabel(
        "Mean surface soil moisture (m³/m³)"
    )

    ax.set_title(
        "Jharkhand Seasonal Soil Moisture — Year Comparison"
    )

    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.tight_layout()

    return fig


@app.cell
def _(mo, fig):
    mo.mpl.interactive(fig)

    return


@app.cell
def _(monthly, pd):
    year_comparison = (
        monthly
        .groupby("year")
        .agg(
            annual_mean=(
                "soil_moisture_mean",
                "mean"
            ),
            months_available=(
                "month",
                "count"
            ),
        )
        .reset_index()
    )

    year_comparison["annual_mean"] = (
        year_comparison["annual_mean"]
        .round(5)
    )

    return year_comparison


@app.cell
def _(mo, year_comparison):
    mo.vstack([
        mo.md("""
        ## Available-period annual comparison

        This table compares the mean of the available monthly
        observations within each year.

        It should **not** be interpreted as a complete annual
        climatological average when a year has incomplete months.
        """),

        mo.ui.table(year_comparison),
    ])

    return


@app.cell
def _(monthly, pd):
    # Identify the wettest and driest available monthly state-wide
    # averages in the current record.
    wettest = monthly.loc[
        monthly["soil_moisture_mean"].idxmax()
    ]

    driest = monthly.loc[
        monthly["soil_moisture_mean"].idxmin()
    ]

    extremes = pd.DataFrame([
        {
            "category": "Wettest available month",
            "month": wettest["month"],
            "mean_soil_moisture": round(
                wettest["soil_moisture_mean"], 5
            ),
        },
        {
            "category": "Driest available month",
            "month": driest["month"],
            "mean_soil_moisture": round(
                driest["soil_moisture_mean"], 5
            ),
        },
    ])

    return extremes


@app.cell
def _(mo, extremes):
    mo.vstack([
        mo.md("## Extremes in the current record"),

        mo.md("""
        These are descriptive extremes within the available
        April 2015–December 2016 dataset only. They are not
        drought or flood classifications.
        """),

        mo.ui.table(extremes),
    ])

    return


if __name__ == "__main__":
    app.run()
