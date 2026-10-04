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
            "latitude",
            "longitude",
            "soil_moisture_mean",
        }

        missing = required - set(df.columns)

        if missing:
            raise ValueError(
                f"{file.name}: missing columns "
                f"{sorted(missing)}"
            )

        dt = pd.to_datetime(
            df["month"],
            errors="raise"
        )

        df["month"] = dt.dt.to_period("M").astype(str)
        df["year"] = dt.dt.year
        df["month_number"] = dt.dt.month

        frames.append(df)

    all_data = pd.concat(
        frames,
        ignore_index=True
    )

    return all_data, files


@app.cell
def _(all_data):
    def assign_season(month_number):
        if month_number in [1, 2]:
            return "Winter"

        if month_number in [3, 4, 5]:
            return "Pre-monsoon"

        if month_number in [6, 7, 8, 9]:
            return "Monsoon"

        return "Post-monsoon"

    all_data["season"] = (
        all_data["month_number"]
        .apply(assign_season)
    )

    season_order = [
        "Winter",
        "Pre-monsoon",
        "Monsoon",
        "Post-monsoon",
    ]

    return season_order


@app.cell
def _(all_data, pd):
    all_data["season"] = pd.Categorical(
        all_data["season"],
        categories=[
            "Winter",
            "Pre-monsoon",
            "Monsoon",
            "Post-monsoon",
        ],
        ordered=True,
    )

    monthly_cell = (
        all_data[
            [
                "row",
                "col",
                "latitude",
                "longitude",
                "year",
                "month",
                "month_number",
                "season",
                "soil_moisture_mean",
            ]
        ]
        .groupby(
            [
                "row",
                "col",
                "latitude",
                "longitude",
                "year",
                "month",
                "month_number",
                "season",
            ],
            observed=True,
        )
        .agg(
            soil_moisture=(
                "soil_moisture_mean",
                "mean"
            )
        )
        .reset_index()
    )

    return monthly_cell


@app.cell
def _(monthly_cell):
    seasonal = (
        monthly_cell
        .groupby(
            [
                "row",
                "col",
                "latitude",
                "longitude",
                "season",
            ],
            observed=True,
        )
        .agg(
            seasonal_mean=(
                "soil_moisture",
                "mean"
            ),
            seasonal_std=(
                "soil_moisture",
                "std"
            ),
            months_available=(
                "month",
                "nunique"
            ),
            years_available=(
                "year",
                "nunique"
            ),
        )
        .reset_index()
    )

    seasonal["seasonal_std"] = (
        seasonal["seasonal_std"]
        .fillna(0)
    )

    return seasonal


@app.cell
def _(seasonal):
    # Extract each season explicitly.
    # This avoids fragile pivot-table column naming.

    winter = (
        seasonal[
            seasonal["season"] == "Winter"
        ]
        [
            [
                "row",
                "col",
                "latitude",
                "longitude",
                "seasonal_mean",
                "seasonal_std",
                "months_available",
                "years_available",
            ]
        ]
        .rename(
            columns={
                "seasonal_mean": "winter_mean",
                "seasonal_std": "winter_std",
                "months_available": "winter_months",
                "years_available": "winter_years",
            }
        )
    )

    pre_monsoon = (
        seasonal[
            seasonal["season"] == "Pre-monsoon"
        ]
        [
            [
                "row",
                "col",
                "latitude",
                "longitude",
                "seasonal_mean",
                "seasonal_std",
                "months_available",
                "years_available",
            ]
        ]
        .rename(
            columns={
                "seasonal_mean": "pre_monsoon_mean",
                "seasonal_std": "pre_monsoon_std",
                "months_available": "pre_monsoon_months",
                "years_available": "pre_monsoon_years",
            }
        )
    )

    monsoon = (
        seasonal[
            seasonal["season"] == "Monsoon"
        ]
        [
            [
                "row",
                "col",
                "latitude",
                "longitude",
                "seasonal_mean",
                "seasonal_std",
                "months_available",
                "years_available",
            ]
        ]
        .rename(
            columns={
                "seasonal_mean": "monsoon_mean",
                "seasonal_std": "monsoon_std",
                "months_available": "monsoon_months",
                "years_available": "monsoon_years",
            }
        )
    )

    post_monsoon = (
        seasonal[
            seasonal["season"] == "Post-monsoon"
        ]
        [
            [
                "row",
                "col",
                "latitude",
                "longitude",
                "seasonal_mean",
                "seasonal_std",
                "months_available",
                "years_available",
            ]
        ]
        .rename(
            columns={
                "seasonal_mean": "post_monsoon_mean",
                "seasonal_std": "post_monsoon_std",
                "months_available": "post_monsoon_months",
                "years_available": "post_monsoon_years",
            }
        )
    )

    return winter, pre_monsoon, monsoon, post_monsoon


@app.cell
def _(
    pd,
    winter,
    pre_monsoon,
    monsoon,
    post_monsoon,
):
    # Start from the complete spatial grid.
    spatial = (
        winter[
            [
                "row",
                "col",
                "latitude",
                "longitude",
            ]
        ]
        .drop_duplicates()
        .copy()
    )

    spatial = spatial.merge(
        winter,
        on=[
            "row",
            "col",
            "latitude",
            "longitude",
        ],
        how="left",
    )

    spatial = spatial.merge(
        pre_monsoon,
        on=[
            "row",
            "col",
            "latitude",
            "longitude",
        ],
        how="outer",
    )

    spatial = spatial.merge(
        monsoon,
        on=[
            "row",
            "col",
            "latitude",
            "longitude",
        ],
        how="outer",
    )

    spatial = spatial.merge(
        post_monsoon,
        on=[
            "row",
            "col",
            "latitude",
            "longitude",
        ],
        how="outer",
    )

    spatial = spatial.drop_duplicates(
        subset=[
            "row",
            "col",
            "latitude",
            "longitude",
        ]
    )

    spatial["cell_id"] = (
        "R"
        + spatial["row"].astype(int).astype(str)
        + "_C"
        + spatial["col"].astype(int).astype(str)
    )

    return spatial


@app.cell
def _(spatial):
    season_columns = [
        "winter_mean",
        "pre_monsoon_mean",
        "monsoon_mean",
        "post_monsoon_mean",
    ]

    spatial["seasonal_mean_available"] = (
        spatial[season_columns]
        .notna()
        .sum(axis=1)
    )

    spatial["monsoon_minus_pre_monsoon"] = (
        spatial["monsoon_mean"]
        - spatial["pre_monsoon_mean"]
    )

    spatial["seasonal_max"] = (
        spatial[season_columns]
        .max(axis=1)
    )

    spatial["seasonal_min"] = (
        spatial[season_columns]
        .min(axis=1)
    )

    spatial["seasonal_range"] = (
        spatial["seasonal_max"]
        - spatial["seasonal_min"]
    )

    spatial["seasonal_mean"] = (
        spatial[season_columns]
        .mean(axis=1)
    )

    spatial["seasonal_std_across_seasons"] = (
        spatial[season_columns]
        .std(axis=1)
    )

    spatial["seasonal_cv"] = (
        spatial["seasonal_std_across_seasons"]
        / spatial["seasonal_mean"]
    )

    spatial["all_four_seasons"] = (
        spatial["seasonal_mean_available"] == 4
    )

    numeric_columns = spatial.select_dtypes(
        include="number"
    ).columns

    spatial[numeric_columns] = (
        spatial[numeric_columns]
        .round(6)
    )

    return spatial


@app.cell
def _(mo, files, all_data, spatial):
    complete = int(
        spatial["all_four_seasons"].sum()
    )

    mo.vstack([
        mo.md("""
        # 🌧️ EarthTrend Detective — Spatial Seasonality

        ## Research question

        **Do different parts of Jharkhand respond to the seasonal
        cycle in different ways?**

        For each of the 984 SMAP grid cells, this analysis calculates
        seasonal surface-soil-moisture statistics.

        **Winter:** January–February

        **Pre-monsoon:** March–May

        **Monsoon:** June–September

        **Post-monsoon:** October–December

        ### Scientific limitation

        The current record covers only **April 2015 – December 2016**.

        Therefore these results are exploratory seasonal patterns,
        not long-term climatological normals.

        2015 is incomplete at the beginning of the record, while
        Winter currently has only 2016 observations.
        """),

        mo.md(
            f"**Monthly files:** {len(files)}  |  "
            f"**Monthly cell records:** {len(all_data):,}  |  "
            f"**Spatial cells:** {spatial['cell_id'].nunique():,}"
        ),

        mo.md(
            f"**Cells with all four seasonal means:** "
            f"{complete:,}"
        ),
    ])

    return


@app.cell
def _(mo, spatial):
    summary = pd.DataFrame([
        {
            "metric": "Cells analyzed",
            "value": len(spatial),
        },
        {
            "metric": "Cells with all four seasons",
            "value": int(
                spatial["all_four_seasons"].sum()
            ),
        },
        {
            "metric": "Mean winter moisture",
            "value": round(
                spatial["winter_mean"].mean(),
                5,
            ),
        },
        {
            "metric": "Mean pre-monsoon moisture",
            "value": round(
                spatial["pre_monsoon_mean"].mean(),
                5,
            ),
        },
        {
            "metric": "Mean monsoon moisture",
            "value": round(
                spatial["monsoon_mean"].mean(),
                5,
            ),
        },
        {
            "metric": "Mean post-monsoon moisture",
            "value": round(
                spatial["post_monsoon_mean"].mean(),
                5,
            ),
        },
        {
            "metric": "Mean monsoon - pre-monsoon",
            "value": round(
                spatial["monsoon_minus_pre_monsoon"].mean(),
                5,
            ),
        },
        {
            "metric": "Mean seasonal range",
            "value": round(
                spatial["seasonal_range"].mean(),
                5,
            ),
        },
    ])

    mo.vstack([
        mo.md("## Spatial seasonality summary"),
        mo.ui.table(summary),
    ])

    return summary


@app.cell
def _(mo, spatial):
    response_columns = [
        "cell_id",
        "latitude",
        "longitude",
        "pre_monsoon_mean",
        "monsoon_mean",
        "monsoon_minus_pre_monsoon",
        "seasonal_range",
    ]

    strongest = (
        spatial
        .dropna(
            subset=[
                "pre_monsoon_mean",
                "monsoon_mean",
            ]
        )
        .sort_values(
            "monsoon_minus_pre_monsoon",
            ascending=False,
        )
        [response_columns]
        .head(10)
    )

    weakest = (
        spatial
        .dropna(
            subset=[
                "pre_monsoon_mean",
                "monsoon_mean",
            ]
        )
        .sort_values(
            "monsoon_minus_pre_monsoon",
            ascending=True,
        )
        [response_columns]
        .head(10)
    )

    mo.vstack([
        mo.md(
            "## 10 cells with largest monsoon response"
        ),
        mo.ui.table(strongest),

        mo.md(
            "## 10 cells with smallest monsoon response"
        ),
        mo.ui.table(weakest),
    ])

    return strongest, weakest


@app.cell
def _(mo, spatial):
    display_columns = [
        "cell_id",
        "latitude",
        "longitude",
        "winter_mean",
        "pre_monsoon_mean",
        "monsoon_mean",
        "post_monsoon_mean",
        "monsoon_minus_pre_monsoon",
        "seasonal_range",
        "seasonal_cv",
        "winter_months",
        "pre_monsoon_months",
        "monsoon_months",
        "post_monsoon_months",
        "all_four_seasons",
    ]

    mo.vstack([
        mo.md(
            "## Complete spatial seasonality table"
        ),
        mo.ui.table(
            spatial[
                display_columns
            ].sort_values("cell_id")
        ),
    ])

    return


@app.cell
def _(plt, spatial):
    map_data = spatial.dropna(
        subset=[
            "latitude",
            "longitude",
            "monsoon_minus_pre_monsoon",
        ]
    )

    fig_monsoon_response, ax_monsoon_response = plt.subplots(
        figsize=(10, 7)
    )

    scatter_monsoon_response = ax_monsoon_response.scatter(
        map_data["longitude"],
        map_data["latitude"],
        c=map_data[
            "monsoon_minus_pre_monsoon"
        ],
        s=18,
        alpha=0.8,
    )

    ax_monsoon_response.set_xlabel("Longitude")
    ax_monsoon_response.set_ylabel("Latitude")
    ax_monsoon_response.set_title(
        "Monsoon Response: "
        "Monsoon − Pre-monsoon"
    )

    fig_monsoon_response.colorbar(
        scatter_monsoon_response,
        ax=ax_monsoon_response,
        label="Δ soil moisture (m³/m³)",
    )

    ax_monsoon_response.grid(True, alpha=0.2)
    fig_monsoon_response.tight_layout()

    return fig_monsoon_response


@app.cell
def _(mo, fig_monsoon_response):
    mo.mpl.interactive(fig_monsoon_response)

    return


@app.cell
def _(plt, spatial):
    map_data_seasonal_range = spatial.dropna(
        subset=[
            "latitude",
            "longitude",
            "seasonal_range",
        ]
    )

    fig_seasonal_range, ax_seasonal_range = plt.subplots(
        figsize=(10, 7)
    )

    scatter_seasonal_range = ax_seasonal_range.scatter(
        map_data["longitude"],
        map_data["latitude"],
        c=map_data["seasonal_range"],
        s=18,
        alpha=0.8,
    )

    ax_seasonal_range.set_xlabel("Longitude")
    ax_seasonal_range.set_ylabel("Latitude")
    ax_seasonal_range.set_title(
        "Spatial Seasonal Range"
    )

    fig_seasonal_range.colorbar(
        scatter_seasonal_range,
        ax=ax_seasonal_range,
        label="Seasonal range (m³/m³)",
    )

    ax_seasonal_range.grid(True, alpha=0.2)
    fig_seasonal_range.tight_layout()

    return fig_seasonal_range


@app.cell
def _(mo, fig_seasonal_range):
    mo.mpl.interactive(fig_seasonal_range)

    return


@app.cell
def _(plt, spatial):
    map_data_monsoon = spatial.dropna(
        subset=[
            "latitude",
            "longitude",
            "monsoon_mean",
        ]
    )

    fig_monsoon, ax_monsoon = plt.subplots(
        figsize=(10, 7)
    )

    scatter_monsoon = ax_monsoon.scatter(
        map_data["longitude"],
        map_data["latitude"],
        c=map_data["monsoon_mean"],
        s=18,
        alpha=0.8,
    )

    ax_monsoon.set_xlabel("Longitude")
    ax_monsoon.set_ylabel("Latitude")
    ax_monsoon.set_title(
        "Spatial Distribution of "
        "Monsoon Soil Moisture"
    )

    fig_monsoon.colorbar(
        scatter_monsoon,
        ax=ax_monsoon,
        label="Monsoon soil moisture (m³/m³)",
    )

    ax_monsoon.grid(True, alpha=0.2)
    fig_monsoon.tight_layout()

    return fig_monsoon


@app.cell
def _(mo, fig_monsoon):
    mo.mpl.interactive(fig_monsoon)

    return


@app.cell
def _(mo):
    mo.md("""
    ## 🔬 How to interpret this analysis

    ### Monsoon − Pre-monsoon

    This measures the increase in surface soil moisture from the
    pre-monsoon period to the monsoon period.

    A larger positive value means a stronger seasonal increase in
    the current observation period.

    ### Seasonal range

    This is:

    **highest seasonal mean − lowest seasonal mean**

    A larger value means stronger seasonal variability.

    ### What this analysis does NOT establish

    These spatial differences do not prove that rainfall, elevation,
    soil type, land cover, drainage, or vegetation caused the pattern.

    Those variables can be investigated later as explanatory
    covariates.

    ### Scientific caution

    The dataset currently contains only 21 months.

    Therefore we should not describe any cell as permanently wet,
    permanently dry, or permanently more monsoon-responsive.

    Longer SMAP history is required for robust long-term conclusions.
    """)

    return


if __name__ == "__main__":
    app.run()
