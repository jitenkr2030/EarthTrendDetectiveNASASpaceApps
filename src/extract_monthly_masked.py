import pandas as pd
import numpy as np
from pathlib import Path
from pydap.client import open_url

INVENTORY = Path("data/smap_granule_inventory.csv")
MASK_FILE = Path("data/jharkhand_smap_mask.csv")
OUTPUT = Path("data/smap_jharkhand_2015_04_masked_v2.csv")

R1, R2 = 465, 509
C1, C2 = 2820, 2870

inventory = pd.read_csv(INVENTORY)
mask = pd.read_csv(MASK_FILE)

inventory["time_start"] = pd.to_datetime(
    inventory["time_start"], utc=True
)

monthly = inventory[
    (inventory["time_start"] >= "2015-04-01") &
    (inventory["time_start"] < "2015-05-01")
].copy()

print("April granules:", len(monthly))
print("Mask cells:", len(mask))

if len(mask) != 984:
    raise ValueError("Master mask must contain exactly 984 cells.")

sum_values = np.zeros(len(mask), dtype=np.float64)
valid_count = np.zeros(len(mask), dtype=np.int32)

for i, url in enumerate(monthly["opendap_url"], start=1):

    print(
        f"\rProcessing {i}/{len(monthly)}",
        end="",
        flush=True
    )

    ds = open_url(url)

    # SMAP L4 variable is inside Geophysical_Data
    sm = ds["/Geophysical_Data/sm_surface"]

    values = np.asarray(
        sm[R1:R2, C1:C2]
    ).astype(np.float64)

    # Invalid / fill values
    values[values < 0] = np.nan
    values[values > 0.9] = np.nan

    for j, cell in mask.iterrows():

        r = int(cell["row"]) - R1
        c = int(cell["col"]) - C1

        value = values[r, c]

        if np.isfinite(value):
            sum_values[j] += value
            valid_count[j] += 1

print()

result = mask.copy()

result["month"] = "2015-04"

result["soil_moisture_mean"] = np.where(
    valid_count > 0,
    sum_values / valid_count,
    np.nan
)

result["observations"] = valid_count

result = result[
    [
        "month",
        "row",
        "col",
        "latitude",
        "longitude",
        "soil_moisture_mean",
        "observations",
    ]
]

result.to_csv(OUTPUT, index=False)

print()
print("OUTPUT:", OUTPUT)
print("Cells:", len(result))
print(
    "Cells with data:",
    result["soil_moisture_mean"].notna().sum()
)

print("\nObservation count:")
print(result["observations"].describe())

print(
    "\nMean soil moisture:",
    result["soil_moisture_mean"].mean()
)

print(
    "Min soil moisture:",
    result["soil_moisture_mean"].min()
)

print(
    "Max soil moisture:",
    result["soil_moisture_mean"].max()
)
