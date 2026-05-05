"""
FAIL durumundaki 19 mahalleyi 3 perifer ilcenin merkez koordinatlarina atar.
Tum mahalleler icin is_periphery flag'i ekler.
"""
import pandas as pd

COORD_PATH = '../data/neighborhood_coordinates.csv'

# Manuel ilce merkez koordinatlari (Google Maps dogrulamali)
DISTRICT_CENTERS = {
    'silivri':  (41.0741, 28.2466),
    'sile':     (41.1747, 29.6128),
    'catalca':  (41.1431, 28.4631),
}

PERIPHERY_DISTRICTS = set(DISTRICT_CENTERS.keys())

coords = pd.read_csv(COORD_PATH)
print(f"Yuklenen: {len(coords)} mahalle")
print(f"Strategy oncesi: {coords['strategy'].value_counts().to_dict()}")

# FAIL'leri duzelt
fail_count = 0
for i, row in coords.iterrows():
    if row['strategy'] == 'FAIL':
        district = row['district']
        if district in DISTRICT_CENTERS:
            lat, lon = DISTRICT_CENTERS[district]
            coords.at[i, 'lat'] = lat
            coords.at[i, 'lon'] = lon
            coords.at[i, 'strategy'] = 'manual_district_center'
            coords.at[i, 'place_type'] = 'manual'
            coords.at[i, 'address'] = f"{district} ilce merkezi (manuel)"
            fail_count += 1
        else:
            print(f"UYARI: {district} icin manuel koordinat yok!")

print(f"\nDuzeltilen FAIL sayisi: {fail_count}")

# is_periphery flag ekle
coords['is_periphery'] = coords['district'].isin(PERIPHERY_DISTRICTS).astype(int)

print(f"\nStrategy sonrasi: {coords['strategy'].value_counts().to_dict()}")
print(f"is_periphery=1 mahalle sayisi: {coords['is_periphery'].sum()}")

# Bbox sanity check
out_of_bbox = coords[
    (coords['lat'] < 40.80) | (coords['lat'] > 41.30) |
    (coords['lon'] < 28.10) | (coords['lon'] > 29.70)
]
print(f"\nBbox disinda kalan: {len(out_of_bbox)}")
if len(out_of_bbox) > 0:
    print(out_of_bbox[['district', 'neighborhood', 'lat', 'lon']].to_string(index=False))

# Final NaN kontrolu
nan_count = coords['lat'].isna().sum()
print(f"\nLAT NaN olan: {nan_count}")
if nan_count > 0:
    print("UYARI: Hala NaN koordinat var!")
    print(coords[coords['lat'].isna()][['district', 'neighborhood']].to_string(index=False))

coords.to_csv(COORD_PATH, index=False)
print(f"\nKaydedildi: {COORD_PATH}")