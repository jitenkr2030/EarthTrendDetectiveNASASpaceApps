import requests

CONCEPT_ID = "C3480440870-NSIDC_CPRD"

url = "https://cmr.earthdata.nasa.gov/search/granules.json"

params = {
    "collection_concept_id": CONCEPT_ID,
    "bounding_box": "83.3,21.9,87.9,25.3",
    "temporal": "2015-04-01T00:00:00Z,2015-04-30T23:59:59Z",
    "page_size": 10,
    "sort_key": "-start_date",
}

response = requests.get(url, params=params, timeout=60)
response.raise_for_status()

data = response.json()

entries = data["feed"]["entry"]

print("\nSMAP GRANULE SEARCH")
print("==================")
print("Dataset: SPL4SMGP V008")
print("Region : Jharkhand bounding box")
print("Period : April 2015")
print("Found  :", len(entries))

for i, item in enumerate(entries, 1):
    print(f"\n[{i}]")
    print("Granule :", item.get("title"))
    print("ID      :", item.get("id"))
    print("Time    :", item.get("time_start"))

    for link in item.get("links", []):
        href = link.get("href", "")
        if href.endswith((".h5", ".hdf5", ".nc", ".nc4")):
            print("Data    :", href)
