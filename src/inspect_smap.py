import requests
import h5py
from pathlib import Path

URL = "https://data.nsidc.earthdatacloud.nasa.gov/nsidc-cumulus-prod-protected/SMAP/SPL4SMGP/008/2015/04/30/SMAP_L4_SM_gph_20150430T223000_Vv8010_001.h5"

output = Path("data/raw/test_smap.h5")

print("Downloading one SMAP granule...")
print("This is a test file only.")

response = requests.get(
    URL,
    auth=(
        requests.utils.get_auth_from_netrc(
            "https://data.nsidc.earthdatacloud.nasa.gov"
        )
        if hasattr(requests.utils, "get_auth_from_netrc")
        else None
    ),
    stream=True,
    timeout=120,
)

print("HTTP status:", response.status_code)

if response.status_code != 200:
    print(response.text[:1000])
    raise SystemExit("Download failed.")

output.parent.mkdir(parents=True, exist_ok=True)

with open(output, "wb") as f:
    for chunk in response.iter_content(chunk_size=1024 * 1024):
        if chunk:
            f.write(chunk)

print("Saved:", output)

print("\nHDF5 STRUCTURE")
print("==============")

with h5py.File(output, "r") as h5:
    def show(name, obj):
        if isinstance(obj, h5py.Dataset):
            print(
                f"{name} | shape={obj.shape} | dtype={obj.dtype}"
            )

    h5.visititems(show)
