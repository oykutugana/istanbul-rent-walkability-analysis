"""
04_compute_features.py

Geocoded mahalle merkezleri etrafinda POI sayimlari yapar, feature'a cevirir,
P1 listings ile merge edip P2 input'unu uretir.

Hesaplanan feature'lar:
* nearest_metro_km     - en yakin metro/Marmaray istasyonuna haversine mesafesi
* metro_500m, metro_1km - 500m/1km icindeki istasyon sayisi
* weighted_1km         - 1km icindeki agirlikli istasyon sayisi (metro=1.0, tram=0.7, vs.)
* cafe_1km             - 1km icindeki kafe sayisi
* restaurant_1km       - 1km icindeki restoran sayisi
* university_2km       - 2km icindeki universite sayisi
* park_1km             - 1km icindeki park sayisi
* is_periphery         - sehir merkezinden 15km+ flag
* is_district_center   - geocode strategy 3 fallback flag (geocoded_locations'tan)

Run:
    python 04_compute_features.py
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

# Paths
GEOCODED   = Path("../data/geocoded_locations.csv")
POI_DIR    = Path("../data/poi_raw")
LISTINGS   = Path("../data/istanbul_emlak_final.csv")
OUTPUT     = Path("../data/istanbul_emlak_with_geo.csv")

# Sehir merkezi (Eminonu civari) - is_periphery icin referans
CITY_CENTER = (41.0186, 28.9784)
PERIPHERY_KM = 15.0

# Istasyon agirliklari
STATION_WEIGHTS = {
    "subway":     1.0,   # Metro
    "light_rail": 0.7,   # Hafif metro / Marmaray hafif kisim
    "tram_stop":  0.7,   # Tramvay
    "tram":       0.7,
    "halt":       0.5,   # Banliyo halt
    "station":    0.5,   # Genel "station" tag - default
    "default":    0.5,
}


def haversine_km(lat1, lon1, lat2, lon2):
    """Vectorized haversine. lat/lon scalar veya array olabilir."""
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def load_pois(name):
    """raw_*.json'dan lat/lon ve tag bilgisini cekip DataFrame'e cevir."""
    path = POI_DIR / f"raw_{name}.json"
    with open(path) as f:
        data = json.load(f)

    rows = []
    for el in data["elements"]:
        # node = lat/lon direkt; way/relation = center.lat/lon
        if "lat" in el and "lon" in el:
            lat, lon = el["lat"], el["lon"]
        elif "center" in el:
            lat, lon = el["center"]["lat"], el["center"]["lon"]
        else:
            continue
        tags = el.get("tags", {})
        rows.append({"lat": lat, "lon": lon, "tags": tags})
    return pd.DataFrame(rows)


def classify_station(tags):
    """Istasyon tipini sinifla -> agirlik dondur."""
    if tags.get("station") == "subway":
        return STATION_WEIGHTS["subway"]
    if tags.get("station") == "light_rail":
        return STATION_WEIGHTS["light_rail"]
    if tags.get("railway") == "tram_stop":
        return STATION_WEIGHTS["tram_stop"]
    if tags.get("railway") == "halt":
        return STATION_WEIGHTS["halt"]
    if tags.get("public_transport") == "station":
        return STATION_WEIGHTS["station"]
    if tags.get("railway") == "station":
        # Fark gozetilmemis - default 0.5
        return STATION_WEIGHTS["station"]
    return STATION_WEIGHTS["default"]


def compute_features_for_centroid(lat, lon, transit, restaurants, cafes, universities, parks):
    """Tek bir mahalle merkezi icin tum feature'lari hesapla."""
    feats = {}

    # Transit
    if len(transit) > 0:
        d = haversine_km(lat, lon, transit["lat"].values, transit["lon"].values)
        feats["nearest_metro_km"] = float(d.min())
        feats["metro_500m"] = int((d <= 0.5).sum())
        feats["metro_1km"]  = int((d <= 1.0).sum())
        # Agirlikli sayim
        within_1km = d <= 1.0
        feats["weighted_1km"] = float((transit["weight"].values[within_1km]).sum())
    else:
        feats.update({"nearest_metro_km": np.nan, "metro_500m": 0,
                      "metro_1km": 0, "weighted_1km": 0.0})

    # Restoran (1km)
    if len(restaurants) > 0:
        d = haversine_km(lat, lon, restaurants["lat"].values, restaurants["lon"].values)
        feats["restaurant_1km"] = int((d <= 1.0).sum())
    else:
        feats["restaurant_1km"] = 0

    # Kafe (1km)
    if len(cafes) > 0:
        d = haversine_km(lat, lon, cafes["lat"].values, cafes["lon"].values)
        feats["cafe_1km"] = int((d <= 1.0).sum())
    else:
        feats["cafe_1km"] = 0

    # Universite (2km - daha genis cunku ogrenci ulasimi)
    if len(universities) > 0:
        d = haversine_km(lat, lon, universities["lat"].values, universities["lon"].values)
        feats["university_2km"] = int((d <= 2.0).sum())
    else:
        feats["university_2km"] = 0

    # Park (1km)
    if len(parks) > 0:
        d = haversine_km(lat, lon, parks["lat"].values, parks["lon"].values)
        feats["park_1km"] = int((d <= 1.0).sum())
    else:
        feats["park_1km"] = 0

    # Periphery flag
    d_center = haversine_km(lat, lon, CITY_CENTER[0], CITY_CENTER[1])
    feats["is_periphery"] = int(d_center > PERIPHERY_KM)

    return feats


def main():
    print("Loading geocoded locations and POIs...")
    geo = pd.read_csv(GEOCODED)
    print(f"  Geocoded:    {len(geo):,} ({geo['lat'].notna().sum()} with coords)")

    transit = load_pois("transit")
    transit["weight"] = transit["tags"].apply(classify_station)
    print(f"  Transit:     {len(transit):,}")

    restaurants  = load_pois("restaurants")
    print(f"  Restaurants: {len(restaurants):,}")

    cafes        = load_pois("cafes")
    print(f"  Cafes:       {len(cafes):,}")

    universities = load_pois("universities")
    print(f"  Universities:{len(universities):,}")

    parks        = load_pois("parks")
    print(f"  Parks:       {len(parks):,}")

    # Geocoded mahalleler icin feature'lari hesapla
    print("\nComputing features per neighborhood centroid...")
    feature_rows = []
    for i, row in geo.iterrows():
        if pd.isna(row["lat"]) or pd.isna(row["lon"]):
            # Geocode fail - feature'lar NaN, sonra district medianla doldurulur
            feats = {k: np.nan for k in [
                "nearest_metro_km", "metro_500m", "metro_1km", "weighted_1km",
                "restaurant_1km", "cafe_1km", "university_2km", "park_1km", "is_periphery"
            ]}
        else:
            feats = compute_features_for_centroid(
                row["lat"], row["lon"],
                transit, restaurants, cafes, universities, parks
            )
        feature_rows.append({
            "district": row["district"],
            "sub_district": row["sub_district"],
            "neighborhood": row["neighborhood"],
            "lat": row["lat"],
            "lon": row["lon"],
            "is_district_center": row["is_district_center"],
            **feats,
        })
        if (i + 1) % 100 == 0:
            print(f"  {i+1:,}/{len(geo):,}")

    geo_features = pd.DataFrame(feature_rows)

    # Listings ile merge
    print("\nMerging with listings...")
    listings = pd.read_csv(LISTINGS)
    print(f"  Listings: {len(listings):,}")

    merged = listings.merge(
        geo_features,
        on=["district", "sub_district", "neighborhood"],
        how="left",
    )
    print(f"  After merge: {len(merged):,}")

    # Eksik feature'lari district median ile doldur (geocoding fail edenler)
    geo_cols = ["nearest_metro_km", "metro_500m", "metro_1km", "weighted_1km",
                "cafe_1km", "restaurant_1km", "university_2km", "park_1km",
                "is_periphery", "is_district_center"]

    print("\nFilling missing geo features with district medians...")
    for col in geo_cols:
        before = merged[col].isna().sum()
        merged[col] = merged.groupby("district")[col].transform(
            lambda x: x.fillna(x.median())
        )
        # Ilce de bos ise global median
        merged[col] = merged[col].fillna(merged[col].median())
        after = merged[col].isna().sum()
        if before > 0:
            print(f"  {col}: filled {before - after} (remaining {after})")

    # Tip dogrulamasi - bool/int olmasi gereken kolonlar
    for col in ["metro_500m", "metro_1km", "restaurant_1km", "cafe_1km",
                "university_2km", "park_1km", "is_periphery", "is_district_center"]:
        merged[col] = merged[col].round().astype(int)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(OUTPUT, index=False)

    print("\n" + "=" * 60)
    print(f"Saved {len(merged):,} listings with geo features to:")
    print(f"  {OUTPUT}")
    print(f"\nGeo feature summary:")
    print(merged[geo_cols].describe().round(2))


if __name__ == "__main__":
    main()