from pydap.client import open_url
from datetime import datetime, timedelta
import requests
import csv
import time
import numpy as np

CONCEPT_ID = "C3480440870-NSIDC_CPRD"

BASE_URL = (
    "https://opendap.earthdata.nasa.gov/collections/"
    f"{CONCEPT_ID}/granules/"
)

# Exact test period
START = datetime(2015, 4, 25, 0, 0, 0)
END   = datetime(2015, 5, 1, 23, 59, 59)

# Jharkhand bounding-box grid
R1, R2 = 465, 509
C1, C2 = 2820, 2870

OUTPUT = "data/smap_jharkhand_test.csv"

CMR_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"


def get_granules():
    params = {
        "collection_concept_id": CONCEPT_ID,
        "temporal": (
            START.strftime("%Y-%m-%dT%H:%M:%SZ")
            + ","
            + END.strftime("%Y-%m-%dT%H:%M:%SZ")
        ),
        "page_size": 200,
        "sort_key": "start_date",
    }

    print("Searching NASA CMR...")

    response = requests.get(
        CMR_URL,
        params=params,
        timeout=60,
    )

    response.raise_for_status()

    entries = response.json()["feed"]["entry"]

    granules = []

    for entry in entries:

        title = entry["title"]

        dap_url = None

        for link in entry.get("links", []):

            href = link.get("href", "")

            if "opendap.earthdata.nasa.gov" in href:

                dap_url = href
                break

        if dap_url:

            granules.append({
                "title": title,
                "url": dap_url,
            })

    return granules


def decode_time(dataset):

    time_var = dataset["time"]

    raw_time = np.asarray(time_var).astype(float).reshape(-1)

    if len(raw_time) == 0:
        raise ValueError("NASA time variable is empty.")

    value = float(raw_time[0])

    units = time_var.attributes.get(
        "units",
        "seconds since 2000-01-01 11:58:55.816"
    )

    prefix = "seconds since "

    if units.startswith(prefix):

        origin_text = units[len(prefix):]

        origin = datetime.fromisoformat(
            origin_text
        )

    else:

        raise ValueError(
            f"Unsupported NASA time units: {units}"
        )

    timestamp = origin + timedelta(
        seconds=value
    )

    return timestamp


def extract_granule(granule):

    print("\nNASA:", granule["title"])

    dataset = open_url(granule["url"])

    # Use NASA internal observation timestamp
    timestamp = decode_time(dataset)

    print("NASA observation time:", timestamp.isoformat())

    # Exact spatial subset
    sm = dataset[
        "/Geophysical_Data/sm_surface"
    ][R1:R2, C1:C2]

    values = np.asarray(sm).astype(float)

    # NASA fill value
    values[values == -9999] = np.nan

    valid = np.isfinite(values)

    if not np.any(valid):

        return None

    mean_value = float(
        np.nanmean(values)
    )

    median_value = float(
        np.nanmedian(values)
    )

    return {
        "time": timestamp.strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ"
        ),
        "mean_soil_moisture": mean_value,
        "median_soil_moisture": median_value,
        "valid_cells": int(
            np.sum(valid)
        ),
        "total_cells": int(
            values.size
        ),
    }


def main():

    granules = get_granules()

    print(
        "\nGranules returned by CMR:",
        len(granules)
    )

    if not granules:

        print("No granules found.")
        return

    rows = []

    for i, granule in enumerate(
        granules,
        1
    ):

        print(
            f"\n[{i}/{len(granules)}]"
        )

        try:

            result = extract_granule(
                granule
            )

            if result:

                observation_time = datetime.strptime(
                    result["time"],
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                )

                # Enforce exact requested period
                if START <= observation_time <= END:

                    rows.append(result)

                    print(
                        "Included."
                    )

                    print(
                        "Mean soil moisture:",
                        f"{result['mean_soil_moisture']:.6f}",
                        "m3/m3"
                    )

                    print(
                        "Valid cells:",
                        f"{result['valid_cells']}/{result['total_cells']}"
                    )

                else:

                    print(
                        "Skipped: outside requested period."
                    )

        except Exception as e:

            print(
                "ERROR:",
                repr(e)
            )

        time.sleep(1)

    rows.sort(
        key=lambda x: x["time"]
    )

    with open(
        OUTPUT,
        "w",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "time",
                "mean_soil_moisture",
                "median_soil_moisture",
                "valid_cells",
                "total_cells",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)

    print("\n==============================")
    print("EARTH TREND DETECTIVE")
    print("==============================")

    print(
        "Output:",
        OUTPUT
    )

    print(
        "Observations:",
        len(rows)
    )

    if rows:

        print(
            "First:",
            rows[0]["time"]
        )

        print(
            "Last :",
            rows[-1]["time"]
        )


if __name__ == "__main__":
    main()
