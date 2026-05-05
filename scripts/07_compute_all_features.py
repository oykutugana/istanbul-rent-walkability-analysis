"""
Tum 447 mahalle icin feature pipeline'i calistirir.
- Cache'li: cokerse kaldigi yerden devam eder
- Her 25 mahallede progress + checkpoint kaydeder
- Output: data/neighborhood_features.csv
"""
import pandas as pd
import numpy as np
import osmnx as ox
import os
import time
from math import radians, sin, cos, sqrt, atan2

COORD_PATH = '../data/neighborhood_coordinates.csv'
STATIONS_PATH = '../data/istanbul_rail_stations.csv'
OUTPUT_PATH = '../data/neighborhood_features.csv'


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def compute_metro_features(lat, lon, stations_df):
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
    try:
        gdf = ox.features_from_point((lat, lon), tags=tags, dist=dist_m)
        return len(gdf)
    except Exception:
        return 0


def compute_all_features(lat, lon, stations_df):
    metro = compute_metro_features(lat, lon, stations_df)
    poi = {
        'cafe_1km': count_poi(lat, lon, {"amenity": "cafe"}, 1000),
        'restaurant_1km': count_poi(lat, lon, {"amenity": "restaurant"}, 1000),
        'university_2km': count_poi(lat, lon, {"amenity": "university"}, 2000),
        'park_1km': count_poi(lat, lon, {"leisure": "park"}, 1000),
    }
    return {**metro, **poi}


# Yukle
coords = pd.read_csv(COORD_PATH)
stations = pd.read_csv(STATIONS_PATH)
print(f"Mahalle koordinatlari: {len(coords)}")
print(f"Istasyonlar: {len(stations)}")

# Cache yukle
if os.path.exists(OUTPUT_PATH):
    cached = pd.read_csv(OUTPUT_PATH)
    cached_keys = set(zip(cached['district'], cached['neighborhood']))
    print(f"Cache yuklendi: {len(cached)} mahalle daha onceden hesaplanmis")
else:
    cached = pd.DataFrame()
    cached_keys = set()

# Hesapla
results = []
total = len(coords)
start = time.time()

for i, row in coords.iterrows():
    district, nh = row['district'], row['neighborhood']

    if (district, nh) in cached_keys:
        continue

    lat, lon = row['lat'], row['lon']

    if pd.isna(lat) or pd.isna(lon):
        results.append({
            'district': district, 'neighborhood': nh,
            'nearest_metro_km': None, 'metro_500m': 0, 'metro_1km': 0,
            'weighted_1km': 0, 'cafe_1km': 0, 'restaurant_1km': 0,
            'university_2km': 0, 'park_1km': 0,
        })
        continue

    feat = compute_all_features(lat, lon, stations)
    results.append({
        'district': district, 'neighborhood': nh,
        **feat
    })

    # Her 25 mahallede checkpoint + progress
    if (i + 1) % 25 == 0:
        elapsed = time.time() - start
        done = i + 1 - len(cached_keys)
        remaining_count = total - i - 1
        if done > 0:
            avg_per_mahalle = elapsed / done
            eta = avg_per_mahalle * remaining_count
            print(
                f"  [{i + 1}/{total}] {elapsed / 60:.1f} dk gecti, ~{eta / 60:.1f} dk kaldi (~{avg_per_mahalle:.1f} sn/mahalle)")
        # Cache yaz
        df_partial = pd.concat([cached, pd.DataFrame(results)], ignore_index=True)
        df_partial.to_csv(OUTPUT_PATH, index=False)

# Final kaydet
df_final = pd.concat([cached, pd.DataFrame(results)], ignore_index=True)
df_final.to_csv(OUTPUT_PATH, index=False)

elapsed = time.time() - start
print(f"\n=== TAMAMLANDI ({elapsed / 60:.1f} dakika) ===")
print(f"Toplam mahalle: {len(df_final)}")
print(f"\nFeature ozet istatistikler:")
print(df_final[['nearest_metro_km', 'metro_500m', 'metro_1km',
                'cafe_1km', 'restaurant_1km', 'university_2km', 'park_1km']].describe().round(2))
print(f"\nKaydedildi: {OUTPUT_PATH}")