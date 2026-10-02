import requests

url = "https://cmr.earthdata.nasa.gov/search/collections.json"

params = {
    "keyword": "SMAP soil moisture",
    "page_size": 20,
}

response = requests.get(url, params=params, timeout=30)
response.raise_for_status()

data = response.json()

print("\nNASA SMAP DATASETS")
print("==================")

for item in data["feed"]["entry"]:
    print("\nShort Name :", item.get("short_name"))
    print("Version    :", item.get("version_id"))
    print("Title      :", item.get("title"))
    print("Concept ID :", item.get("id"))
