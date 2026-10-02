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

    return cells, cell_labels, cell_selector


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

    return selected_cell


@app.cell
def _(all_data, selected_cell):
    cell_data = all_data[
        (all_data["row"] == selected_cell["row"])
        & (all_data["col"] == selected_cell["col"])
    ].copy()

    cell_data = cell_data.sort_values("month")

    return cell_data


@app.cell
def _(cell_data, plt, selected_cell):
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

    ax.grid(True, alpha=0.3)

    fig.tight_layout()

    return fig


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


if __name__ == "__main__":
    app.run()
