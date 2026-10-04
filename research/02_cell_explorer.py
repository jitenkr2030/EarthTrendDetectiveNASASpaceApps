import marimo

__generated_with = "0.25.0"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    from pathlib import Path

    return Path, mo, np, pd, plt


@app.cell
def _(Path, pd):
    DATA_DIR = Path("data/monthly")

    files = sorted(DATA_DIR.glob("????-??.csv"))

    if not files:
        raise FileNotFoundError(
            "No monthly CSV files found in data/monthly/"
        )

    frames = []

    for file in files:
        df = pd.read_csv(file)

        # Ensure month is available from filename if necessary
        if "month" not in df.columns:
            df["month"] = file.stem

        frames.append(df)

    all_data = pd.concat(frames, ignore_index=True)
    return all_data, files


@app.cell
def _(all_data, files, mo):
    months = sorted(all_data["month"].unique())

    mo.md(
        f"""
        # 🌍 EarthTrend Detective — Spatial Cell Explorer

        ## Dataset

        **Monthly files:** {len(files)}

        **Time period:** {months[0]} → {months[-1]}

        **Rows:** {len(all_data):,}

        **Unique cells:** {
            all_data[["row", "col"]].drop_duplicates().shape[0]
        }

        This notebook analyzes the spatial baseline of the
        **984 Jharkhand SMAP grid cells**.
        """
    )
    return


@app.cell
def _(all_data, mo):
    cells = (
        all_data[
            ["row", "col", "latitude", "longitude"]
        ]
        .drop_duplicates()
        .sort_values(["row", "col"])
        .reset_index(drop=True)
    )

    cell_labels = {}

    for i, cell in cells.iterrows():
        label = (
            f"Cell {i+1} | "
            f"row={int(cell['row'])}, "
            f"col={int(cell['col'])} | "
            f"lat={cell['latitude']:.4f}, "
            f"lon={cell['longitude']:.4f}"
        )

        cell_labels[label] = i

    cell_selector = mo.ui.dropdown(
        options=list(cell_labels.keys()),
        value=list(cell_labels.keys())[0],
        label="Select Jharkhand grid cell",
    )
    return cell_labels, cell_selector, cells


@app.cell
def _(cell_labels, cell_selector, cells, mo):
    selected_index = cell_labels[cell_selector.value]
    selected_cell = cells.iloc[selected_index]

    mo.md(
        f"""
        ## 📍 Selected SMAP Cell

        {cell_selector}

        **Grid row:** {int(selected_cell["row"])}

        **Grid column:** {int(selected_cell["col"])}

        **Latitude:** {selected_cell["latitude"]:.6f}

        **Longitude:** {selected_cell["longitude"]:.6f}
        """
    )
    return (selected_cell,)


@app.cell
def _(all_data, selected_cell):
    cell_data = all_data[
        (all_data["row"] == selected_cell["row"])
        & (all_data["col"] == selected_cell["col"])
    ].copy()

    cell_data = cell_data.sort_values("month")
    return (cell_data,)


@app.cell
def _(cell_data, plt):
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(
        cell_data["month"],
        cell_data["soil_moisture_mean"],
        marker="o",
    )

    ax.set_xlabel("Month")
    ax.set_ylabel("Surface soil moisture (m³/m³)")

    ax.set_title(
        "SMAP Surface Soil Moisture — Selected Jharkhand Cell"
    )

    ax.tick_params(axis="x", rotation=45)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    return (fig,)


@app.cell
def _(fig, mo):
    mo.mpl.interactive(fig)
    return


@app.cell
def _(cell_data, mo):
    display_data = cell_data[
        [
            "month",
            "soil_moisture_mean",
            "observations",
            "expected_observations",
            "coverage_fraction",
        ]
    ].copy()

    mo.vstack([
        mo.md("## 📊 Cell Monthly Observations"),
        mo.ui.table(display_data),
    ])
    return


@app.cell
def _(all_data, np):
    spatial_baseline = (
        all_data
        .groupby(
            ["row", "col", "latitude", "longitude"],
            as_index=False
        )
        .agg(
            mean_soil_moisture=(
                "soil_moisture_mean",
                "mean"
            ),
            median_soil_moisture=(
                "soil_moisture_mean",
                "median"
            ),
            min_soil_moisture=(
                "soil_moisture_mean",
                "min"
            ),
            max_soil_moisture=(
                "soil_moisture_mean",
                "max"
            ),
            std_soil_moisture=(
                "soil_moisture_mean",
                "std"
            ),
            months_available=(
                "month",
                "nunique"
            ),
        )
    )

    spatial_baseline["range_soil_moisture"] = (
        spatial_baseline["max_soil_moisture"]
        - spatial_baseline["min_soil_moisture"]
    )

    spatial_baseline["coefficient_of_variation"] = np.where(
        spatial_baseline["mean_soil_moisture"] != 0,
        spatial_baseline["std_soil_moisture"]
        / spatial_baseline["mean_soil_moisture"],
        np.nan,
    )

    spatial_baseline = spatial_baseline.sort_values(
        ["row", "col"]
    ).reset_index(drop=True)

    spatial_baseline.insert(
        0,
        "cell_id",
        range(1, len(spatial_baseline) + 1)
    )
    return (spatial_baseline,)


@app.cell
def _(mo, spatial_baseline):
    mo.md(f"""
    ## 🗺️ Spatial Baseline

    **Cells analyzed:** {len(spatial_baseline)}

    **Mean of cell means:**
    {spatial_baseline["mean_soil_moisture"].mean():.6f}

    **Wettest cell mean:**
    {spatial_baseline["mean_soil_moisture"].max():.6f}

    **Driest cell mean:**
    {spatial_baseline["mean_soil_moisture"].min():.6f}

    **Average spatial standard deviation:**
    {spatial_baseline["std_soil_moisture"].mean():.6f}
    """)
    return


@app.cell
def _(mo, spatial_baseline):
    wettest = (
        spatial_baseline
        .sort_values("mean_soil_moisture", ascending=False)
        .head(10)
    )

    driest = (
        spatial_baseline
        .sort_values("mean_soil_moisture", ascending=True)
        .head(10)
    )

    mo.vstack([
        mo.md("## 💧 10 Wettest Cells by Mean Soil Moisture"),
        mo.ui.table(
            wettest[
                [
                    "cell_id",
                    "latitude",
                    "longitude",
                    "mean_soil_moisture",
                    "std_soil_moisture",
                    "months_available",
                ]
            ]
        ),

        mo.md("## 🏜️ 10 Driest Cells by Mean Soil Moisture"),
        mo.ui.table(
            driest[
                [
                    "cell_id",
                    "latitude",
                    "longitude",
                    "mean_soil_moisture",
                    "std_soil_moisture",
                    "months_available",
                ]
            ]
        ),
    ])
    return


@app.cell
def _(mo, spatial_baseline):
    mo.vstack([
        mo.md("## 📊 All 984 Spatial Cells"),

        mo.ui.table(
            spatial_baseline[
                [
                    "cell_id",
                    "row",
                    "col",
                    "latitude",
                    "longitude",
                    "mean_soil_moisture",
                    "median_soil_moisture",
                    "min_soil_moisture",
                    "max_soil_moisture",
                    "std_soil_moisture",
                    "range_soil_moisture",
                    "coefficient_of_variation",
                    "months_available",
                ]
            ]
        ),
    ])
    return


@app.cell
def _(mo, plt, spatial_baseline):
    fig_mean, ax_mean = plt.subplots(figsize=(9, 7))

    scatter_mean = ax_mean.scatter(
        spatial_baseline["longitude"],
        spatial_baseline["latitude"],
        c=spatial_baseline["mean_soil_moisture"],
        s=18,
    )

    ax_mean.set_xlabel("Longitude")
    ax_mean.set_ylabel("Latitude")

    ax_mean.set_title(
        "Spatial Baseline — Mean Surface Soil Moisture"
    )

    fig_mean.colorbar(
        scatter_mean,
        ax=ax_mean,
        label="Mean soil moisture (m³/m³)"
    )

    ax_mean.grid(True, alpha=0.2)

    fig_mean.tight_layout()

    mo.mpl.interactive(fig_mean)
    return


@app.cell
def _(mo, plt, spatial_baseline):
    fig_std, ax_std = plt.subplots(figsize=(9, 7))

    scatter_std = ax_std.scatter(
        spatial_baseline["longitude"],
        spatial_baseline["latitude"],
        c=spatial_baseline["std_soil_moisture"],
        s=18,
    )

    ax_std.set_xlabel("Longitude")
    ax_std.set_ylabel("Latitude")

    ax_std.set_title(
        "Spatial Variability — Standard Deviation"
    )

    fig_std.colorbar(
        scatter_std,
        ax=ax_std,
        label="Standard deviation (m³/m³)"
    )

    ax_std.grid(True, alpha=0.2)

    fig_std.tight_layout()

    mo.mpl.interactive(fig_std)
    return


@app.cell
def _(mo, plt, spatial_baseline):
    fig_range, ax_range = plt.subplots(figsize=(9, 7))

    scatter_range = ax_range.scatter(
        spatial_baseline["longitude"],
        spatial_baseline["latitude"],
        c=spatial_baseline["range_soil_moisture"],
        s=18,
    )

    ax_range.set_xlabel("Longitude")
    ax_range.set_ylabel("Latitude")

    ax_range.set_title(
        "Spatial Variability — Soil Moisture Range"
    )

    fig_range.colorbar(
        scatter_range,
        ax=ax_range,
        label="Range (m³/m³)"
    )

    ax_range.grid(True, alpha=0.2)

    fig_range.tight_layout()

    mo.mpl.interactive(fig_range)
    return


if __name__ == "__main__":
    app.run()
