"""
03_fetch_pois.py

Overpass API'den Istanbul'un tum POI'lerini cek (transit, restoran, kafe, universite, park).
Tek seferlik sehir capinda sorgu - geocoded noktalar icin radius-based sayim sonradan
04_compute_features.py'de yapilir.

Ozellikler:
* Cache: her kategori cektikten sonra disk'e yazar (raw_*.json)
* Yeniden calistirilirsa cache hit olur, API'ye sormaz
* Overpass query timeout: 300 sn (Istanbul buyuk bolge)

Run:
    python 03_fetch_pois.py
"""

import json
import time
import requests
from pathlib import Path

# Paths
OUT_DIR = Path("../data/poi_raw")

# Overpass
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
TIMEOUT_SEC  = 300

# Istanbul bbox (S, W, N, E)
BBOX = "40.80,28.50,41.30,29.50"

# POI kategorileri ve sorgulari
QUERIES = {
    "transit": f"""
        [out:json][timeout:{TIMEOUT_SEC}];
        (
          node["railway"="station"]({BBOX});
          node["railway"="halt"]({BBOX});
          node["railway"="tram_stop"]({BBOX});
          node["public_transport"="station"]({BBOX});
          node["station"="subway"]({BBOX});
          node["station"="light_rail"]({BBOX});
        );
        out body;
    """,
    "restaurants": f"""
        [out:json][timeout:{TIMEOUT_SEC}];
        node["amenity"="restaurant"]({BBOX});
        out body;
    """,
    "cafes": f"""
        [out:json][timeout:{TIMEOUT_SEC}];
        node["amenity"="cafe"]({BBOX});
        out body;
    """,
    "universities": f"""
        [out:json][timeout:{TIMEOUT_SEC}];
        (
          node["amenity"="university"]({BBOX});
          way["amenity"="university"]({BBOX});
          relation["amenity"="university"]({BBOX});
        );
        out center;
    """,
    "parks": f"""
        [out:json][timeout:{TIMEOUT_SEC}];
        (
          node["leisure"="park"]({BBOX});
          way["leisure"="park"]({BBOX});
          relation["leisure"="park"]({BBOX});
        );
        out center;
    """,
}


def fetch_category(name, query, max_retries=3):
    """Tek bir kategori icin Overpass sorgusu."""
    out_file = OUT_DIR / f"raw_{name}.json"
    if out_file.exists():
        with open(out_file) as f:
            data = json.load(f)
        n = len(data.get("elements", []))
        print(f"  [cache] {name}: {n:,} elements")
        return data

    print(f"  Fetching {name}...")
    for attempt in range(max_retries):
        try:
            r = requests.post(
                OVERPASS_URL,
                data={"data": query},
                timeout=TIMEOUT_SEC + 30,
                headers={"User-Agent": "IstanbulRentAnalysis/1.0"},
            )
            if r.status_code == 200:
                data = r.json()
                n = len(data.get("elements", []))
                OUT_DIR.mkdir(parents=True, exist_ok=True)
                with open(out_file, "w") as f:
                    json.dump(data, f)
                print(f"    -> {n:,} elements saved to {out_file.name}")
                return data
            elif r.status_code in (429, 504):
                wait = 30 * (attempt + 1)
                print(f"    [retry {attempt+1}] HTTP {r.status_code}, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"    HTTP {r.status_code}: {r.text[:200]}")
                return None
        except requests.RequestException as e:
            print(f"    Network error (attempt {attempt+1}): {e}")
            time.sleep(20)

    return None


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Fetching Istanbul POIs from Overpass API\n")

    summary = {}
    for name, query in QUERIES.items():
        data = fetch_category(name, query)
        summary[name] = len(data["elements"]) if data else 0
        # Kategoriler arasi nezaket gecikmesi
        time.sleep(2)

    print("\n" + "=" * 50)
    print("Summary:")
    for name, count in summary.items():
        print(f"  {name:15s} {count:>7,}")
    print(f"\nFiles saved to {OUT_DIR}/")


if __name__ == "__main__":
    main()