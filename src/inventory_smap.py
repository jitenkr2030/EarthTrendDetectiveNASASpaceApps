import requests
import csv
import time

CONCEPT_ID = "C3480440870-NSIDC_CPRD"

START = "2015-01-01T00:00:00Z"
END   = "2026-09-20T23:59:59Z"

CMR_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"

OUTPUT = "data/smap_granule_inventory.csv"

PAGE_SIZE = 2000


def get_page(page_num):
    params = {
        "collection_concept_id": CONCEPT_ID,
        "temporal": f"{START},{END}",
        "page_size": PAGE_SIZE,
        "page_num": page_num,
        "sort_key": "start_date",
    }

    response = requests.get(
        CMR_URL,
        params=params,
        timeout=120,
    )

    response.raise_for_status()

    return response.json()["feed"]["entry"]


def extract_opendap_url(entry):
    for link in entry.get("links", []):
        href = link.get("href", "")

        if "opendap.earthdata.nasa.gov" in href:
            return href

    return ""


def main():
    print("========================================")
    print("EARTH TREND DETECTIVE")
    print("SMAP LONG-TERM GRANULE INVENTORY")
    print("========================================")

    rows = []
    page = 1

    while True:
        print(f"\nFetching CMR page {page}...")

        entries = get_page(page)

        print("Granules returned:", len(entries))

        if not entries:
            break

        for entry in entries:
            title = entry.get("title", "")
            time_start = entry.get("time_start", "")
            time_end = entry.get("time_end", "")
            opendap_url = extract_opendap_url(entry)

            if opendap_url:
                rows.append({
                    "title": title,
                    "time_start": time_start,
                    "time_end": time_end,
                    "opendap_url": opendap_url,
                })

        if len(entries) < PAGE_SIZE:
            break

        page += 1

        time.sleep(1)

    rows.sort(key=lambda x: x["time_start"])

    with open(OUTPUT, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "title",
                "time_start",
                "time_end",
                "opendap_url",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)

    print("\n========================================")
    print("INVENTORY COMPLETE")
    print("========================================")

    print("Total OPeNDAP granules:", len(rows))
    print("Output:", OUTPUT)

    if rows:
        print("\nFirst granule:")
        print(rows[0]["title"])
        print(rows[0]["time_start"])

        print("\nLast granule:")
        print(rows[-1]["title"])
        print(rows[-1]["time_start"])

        print("\nFirst OPeNDAP URL:")
        print(rows[0]["opendap_url"])


if __name__ == "__main__":
    main()
