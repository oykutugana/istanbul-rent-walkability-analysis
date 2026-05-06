"""
02_geocode_locations.py

Unique konumlari Nominatim ile geocode eder. 3 katmanli fallback stratejisi:

    Strateji 1: "{neighborhood}, {sub_district}, {district}, Istanbul, Turkey"
    Strateji 2: "{sub_district}, {district}, Istanbul, Turkey"
    Strateji 3: "{district}, Istanbul, Turkey"   (is_district_center=1 flag'i atilir)

Ozellikler:
* Cache (geocode_cache.json) - kesilirse devam eder, ayni sorguyu 2 kez sormaz
* Rate limit: 1.1 sn/istek (Nominatim ToS)
* Bounding box dogrulama - Istanbul disi sonuclari reddet
* Progress save - her 25 konumda bir disk'e yazar

Run:
    python 02_geocode_locations.py
"""

import json
import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

# Paths
INPUT  = Path("../data/unique_locations.csv")
OUTPUT = Path("../data/geocoded_locations.csv")
CACHE  = Path("../data/geocode_cache.json")

# Nominatim
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT    = "IstanbulRentAnalysis/1.0 (academic project; contact: github.com/oykutugana)"
SLEEP_SEC     = 1.1  # Nominatim free tier ToS

# Istanbul bbox (S, W, N, E) - sonuclari dogrulamak icin
IST_BBOX = (40.80, 28.50, 41.30, 29.50)

# Save progress every N items
SAVE_EVERY = 25


def load_cache():
    if CACHE.exists():
        with open(CACHE) as f:
            return json.load(f)
    return {}


def save_cache(cache):
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE, "w") as f:
        json.dump(cache, f, indent=1, ensure_ascii=False)


def in_istanbul(lat, lon):
    """Istanbul bbox icinde mi?"""
    return IST_BBOX[0] <= lat <= IST_BBOX[2] and IST_BBOX[1] <= lon <= IST_BBOX[3]


def query_nominatim(query, cache, max_retries=3):
    """Cache hit varsa direkt dondur, yoksa Nominatim'e sor."""
    if query in cache:
        return cache[query]

    headers = {"User-Agent": USER_AGENT}
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "countrycodes": "tr",
        "addressdetails": 1,
    }

    for attempt in range(max_retries):
        try:
            r = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=20)
            time.sleep(SLEEP_SEC)
            if r.status_code == 200:
                results = r.json()
                if results:
                    res = results[0]
                    lat, lon = float(res["lat"]), float(res["lon"])
                    if in_istanbul(lat, lon):
                        record = {"lat": lat, "lon": lon, "display": res.get("display_name", "")}
                        cache[query] = record
                        return record
                    else:
                        # Yanlis sehir - kaydet ki tekrar sorma
                        cache[query] = None
                        return None
                else:
                    cache[query] = None
                    return None
            elif r.status_code in (429, 503):
                # Rate-limited - bekle ve tekrar dene
                wait = 5 * (attempt + 1)
                print(f"    [retry {attempt+1}] HTTP {r.status_code}, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"    Unexpected HTTP {r.status_code} for query: {query!r}")
                return None
        except requests.RequestException as e:
            print(f"    Network error (attempt {attempt+1}): {e}")
            time.sleep(5)

    return None


def build_queries(district, sub_district, neighborhood):
    """3 katmanli fallback sorgu listesi."""
    return [
        (1, f"{neighborhood}, {sub_district}, {district}, Istanbul, Turkey"),
        (2, f"{sub_district}, {district}, Istanbul, Turkey"),
        (3, f"{district}, Istanbul, Turkey"),
    ]


def geocode_with_fallback(district, sub_district, neighborhood, cache):
    """3 stratejiyi sirayla dene, ilk basarili olani dondur."""
    queries = build_queries(district, sub_district, neighborhood)
    for strategy, q in queries:
        result = query_nominatim(q, cache)
        if result is not None:
            return {
                "lat": result["lat"],
                "lon": result["lon"],
                "geocode_strategy": strategy,
                "is_district_center": int(strategy == 3),
                "display_name": result.get("display", ""),
            }
    return {
        "lat": None,
        "lon": None,
        "geocode_strategy": None,
        "is_district_center": None,
        "display_name": "",
    }


def main():
    unique = pd.read_csv(INPUT)
    print(f"Loaded {len(unique):,} unique locations from {INPUT.name}")

    cache = load_cache()
    print(f"Cache: {len(cache):,} entries\n")

    results = []
    strategy_counts = {1: 0, 2: 0, 3: 0, None: 0}
    t0 = time.time()

    for i, row in unique.iterrows():
        out = geocode_with_fallback(
            row["district"], row["sub_district"], row["neighborhood"], cache
        )
        results.append({**row.to_dict(), **out})
        strategy_counts[out["geocode_strategy"]] += 1

        # Progress
        if (i + 1) % 10 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (len(unique) - i - 1) / rate if rate > 0 else 0
            print(
                f"[{i+1:4d}/{len(unique)}] "
                f"S1={strategy_counts[1]} S2={strategy_counts[2]} S3={strategy_counts[3]} "
                f"FAIL={strategy_counts[None]} | "
                f"rate={rate:.1f}/s | ETA={eta/60:.1f}min"
            )

        # Disk'e ara kayit
        if (i + 1) % SAVE_EVERY == 0:
            pd.DataFrame(results).to_csv(OUTPUT, index=False)
            save_cache(cache)

    # Final save
    df_out = pd.DataFrame(results)
    df_out.to_csv(OUTPUT, index=False)
    save_cache(cache)

    print("\n" + "=" * 60)
    print("Geocoding complete.")
    print(f"  Strategy 1 (mahalle):  {strategy_counts[1]:4d}")
    print(f"  Strategy 2 (semt):     {strategy_counts[2]:4d}")
    print(f"  Strategy 3 (ilce):     {strategy_counts[3]:4d}")
    print(f"  Failed:                {strategy_counts[None]:4d}")
    print(f"\n  Coverage: {(1 - strategy_counts[None]/len(unique))*100:.1f}%")
    print(f"  Saved to {OUTPUT}")
    print(f"  Cache:   {CACHE}  ({len(cache)} entries)")


if __name__ == "__main__":
    main()