"""
5 ornek mahalle icin full feature pipeline test.
- Mahalle koordinati (cache'den)
- Haversine ile metro mesafesi
- OSMnx ile POI sayimi
"""
import pandas as pd
import numpy as np
import osmnx as ox
from math import radians, sin, cos, sqrt, atan2

COORD_PATH = '../data/neighborhood_coordinates.csv'
STATIONS_PATH = '../data/istanbul_rail_stations.csv'

# Yukle
coords = pd.read_csv(COORD_PATH)
stations = pd.read_csv(STATIONS_PATH)
print(f"Mahalle koordinatlari: {len(coords)}")
print(f"Istasyonlar: {len(stations)}")


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def compute_metro_features(lat, lon, stations_df):
    """Bir koordinat icin metro feature'larini hesaplar."""
    dists = stations_df.apply(
        lambda r: haversine(lat, lon, r['lat'], r['lon']), axis=1
    )

    main_rail = stations_df['category'].isin(['metro', 'marmaray'])

    return {
        'nearest_metro_km': round(dists[main_rail].min(), 3),
        'metro_500m': int(((dists <= 0.5) & main_rail).sum()),
        'metro_1km': int(((dists <= 1.0) & main_rail).sum()),
        'weighted_1km': round((stations_df.loc[dists <= 1.0, 'weight']).sum(), 2),
    }


def count_poi(lat, lon, tags, dist_m):
    """OSMnx ile POI sayar."""
    try:
        gdf = ox.features_from_point((lat, lon), tags=tags, dist=dist_m)
        return len(gdf)
    except Exception:
        return 0


def compute_all_features(lat, lon, stations_df):
    """Tum feature'lari hesaplar."""
    metro = compute_metro_features(lat, lon, stations_df)

    poi = {
        'cafe_1km': count_poi(lat, lon, {"amenity": "cafe"}, 1000),
        'restaurant_1km': count_poi(lat, lon, {"amenity": "restaurant"}, 1000),
        'university_2km': count_poi(lat, lon, {"amenity": "university"}, 2000),
        'park_1km': count_poi(lat, lon, {"leisure": "park"}, 1000),
    }
    return {**metro, **poi}


# Pilot mahalleler
pilot = [
    ("besiktas", "bebek"),
    ("besiktas", "dikilitas"),
    ("fatih", "aksaray"),
    ("esenyurt", "merkez"),
    ("kadikoy", "caferaga"),
]

print(
    f"\n{'Mahalle':<22} {'Ilce':<12} {'metro_km':<9} {'m_500':<6} {'m_1k':<5} {'cafe':<5} {'rest':<5} {'univ':<5} {'park':<5}")
print("-" * 100)

for district, nh in pilot:
    row = coords[(coords['district'] == district) & (coords['neighborhood'] == nh)]
    if row.empty:
        print(f"{nh:<22} {district:<12} KOORDINAT BULUNAMADI")
        continue

    lat, lon = row['lat'].iloc[0], row['lon'].iloc[0]
    feat = compute_all_features(lat, lon, stations)

    print(f"{nh:<22} {district:<12} "
          f"{feat['nearest_metro_km']:<9} "
          f"{feat['metro_500m']:<6} "
          f"{feat['metro_1km']:<5} "
          f"{feat['cafe_1km']:<5} "
          f"{feat['restaurant_1km']:<5} "
          f"{feat['university_2km']:<5} "
          f"{feat['park_1km']:<5}")