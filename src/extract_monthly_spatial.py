from pydap.client import open_url
import pandas as pd
import numpy as np
import csv
import time
from datetime import datetime

INVENTORY = "data/smap_granule_inventory.csv"

OUTPUT = "data/smap_jharkhand_2015_04_spatial.csv"

# Jharkhand bounding-box grid
R1, R2 = 465, 509
C1, C2 = 2820, 2870

YEAR = 2015
MONTH = 4

print("========================================")
print("EARTH TREND DETECTIVE")
print("SPATIAL MONTHLY EXTRACTION")
print("========================================")

# --------------------------------------------------
# Load inventory
# --------------------------------------------------

df = pd.read_csv(INVENTORY)

df["time_start"] = pd.to_datetime(
    df["time_start"],
    utc=True
)

monthly = df[
    (df["time_start"].dt.year == YEAR)
    & (df["time_start"].dt.month == MONTH)
].copy()

monthly = monthly.sort_values("time_start").reset_index(drop=True)

print("\nMonth:", f"{YEAR}-{MONTH:02d}")
print("Granules:", len(monthly))

if len(monthly) == 0:
    raise RuntimeError("No granules found for requested month.")

# --------------------------------------------------
# Accumulators
# --------------------------------------------------

sum_values = np.zeros(
    (R2 - R1, C2 - C1),
    dtype=np.float64
)

count_values = np.zeros(
    (R2 - R1, C2 - C1),
    dtype=np.int32
)

# --------------------------------------------------
# Process granules
# --------------------------------------------------

for i, row in monthly.iterrows():

    print(
        f"\n[{i + 1}/{len(monthly)}]"
    )

    print(row["title"])

    url = row["opendap_url"]

    try:
        dataset = open_url(url)

        sm = dataset[
            "/Geophysical_Data/sm_surface"
        ][R1:R2, C1:C2]

        values = np.asarray(sm).astype(float)

        # NASA fill value
        values[values == -9999] = np.nan

        valid = np.isfinite(values)

        sum_values[valid] += values[valid]
        count_values[valid] += 1

        print(
            "Valid cells:",
            int(np.sum(valid)),
            "/",
            values.size
        )

    except Exception as e:

        print(
            "ERROR:",
            repr(e)
        )

    # Small delay to avoid hammering NASA endpoint
    time.sleep(0.2)

# --------------------------------------------------
# Calculate monthly mean
# --------------------------------------------------

monthly_mean = np.full(
    sum_values.shape,
    np.nan,
    dtype=np.float64
)

valid_cells = count_values > 0

monthly_mean[valid_cells] = (
    sum_values[valid_cells]
    / count_values[valid_cells]
)

# --------------------------------------------------
# Create cell coordinates
# --------------------------------------------------

# Read latitude/longitude from first granule
first_dataset = open_url(
    monthly.iloc[0]["opendap_url"]
)

lat = np.asarray(
    first_dataset["cell_lat"][R1:R2, C1:C2]
).astype(float)

lon = np.asarray(
    first_dataset["cell_lon"][R1:R2, C1:C2]
).astype(float
)

# --------------------------------------------------
# Write output
# --------------------------------------------------

with open(
    OUTPUT,
    "w",
    newline=""
) as f:

    writer = csv.writer(f)

    writer.writerow([
        "month",
        "row",
        "col",
        "latitude",
        "longitude",
        "mean_soil_moisture",
        "observations",
    ])

    for r in range(monthly_mean.shape[0]):

        for c in range(monthly_mean.shape[1]):

            writer.writerow([
                f"{YEAR}-{MONTH:02d}",
                R1 + r,
                C1 + c,
                lat[r, c],
                lon[r, c],
                monthly_mean[r, c],
                count_values[r, c],
            ])

# --------------------------------------------------
# Summary
# --------------------------------------------------

valid_output = np.isfinite(monthly_mean)

print("\n========================================")
print("SPATIAL EXTRACTION COMPLETE")
print("========================================")

print("Month:", f"{YEAR}-{MONTH:02d}")
print("Granules processed:", len(monthly))
print("Grid shape:", monthly_mean.shape)
print("Grid cells:", monthly_mean.size)
print("Cells with data:", int(np.sum(valid_output)))

if np.any(valid_output):

    print(
        "Minimum:",
        float(np.nanmin(monthly_mean))
    )

    print(
        "Maximum:",
        float(np.nanmax(monthly_mean))
    )

    print(
        "Mean:",
        float(np.nanmean(monthly_mean))
    )

    print(
        "Median:",
        float(np.nanmedian(monthly_mean))
    )

print("Output:", OUTPUT)

print("\n========================================")
print("PROTOTYPE COMPLETE")
print("========================================")
