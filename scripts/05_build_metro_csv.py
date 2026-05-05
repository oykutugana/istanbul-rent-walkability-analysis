"""
OSMnx ile Istanbul rayli sistem (metro/marmaray/tramvay/funikuler) istasyonlarini ceker.
Kategorize eder, agirliklandirir, CSV'ye kaydeder.
"""
import osmnx as ox
import pandas as pd

OUTPUT_PATH = '../data/istanbul_rail_stations.csv'

print("OSMnx sorgusu basliyor ...")

istanbul_polygon = ox.geocode_to_gdf("İstanbul, Türkiye")
gdf = ox.features_from_polygon(
    istanbul_polygon.geometry.iloc[0],
    tags={"railway": ["station", "halt"]}
)

print(f"Cekildi: {len(gdf)} istasyon")

# Koordinatlari cikart
gdf['lat'] = gdf.geometry.apply(lambda g: g.centroid.y if g else None)
gdf['lon'] = gdf.geometry.apply(lambda g: g.centroid.x if g else None)
gdf = gdf.dropna(subset=['name', 'lat', 'lon']).reset_index(drop=True)


# Kategorize
def categorize(row):
    st = str(row.get('station', '')).lower()
    rw = str(row.get('railway', '')).lower()
    nw = str(row.get('network', '')).lower()

    if st == 'subway':
        return 'metro'
    if 'marmaray' in nw:
        return 'marmaray'
    if st == 'light_rail':
        return 'tram'
    if st == 'funicular':
        return 'funicular'
    if st == 'train' or 'tcdd' in nw or 'devlet demiryollari' in nw:
        return 'commuter_train'
    if rw == 'halt':
        return 'halt'
    if any(m in nw for m in ['m1', 'm2', 'm3', 'm4', 'm5', 'm7', 'm8', 'm9', 'm11', 'istanbul metro']):
        return 'metro'
    return 'other'


gdf['category'] = gdf.apply(categorize, axis=1)

# Agirlik atama
weight_map = {
    'metro': 1.0, 'marmaray': 1.0, 'tram': 0.7,
    'halt': 0.5, 'funicular': 0.5, 'commuter_train': 0.3, 'other': 0.5,
}
gdf['weight'] = gdf['category'].map(weight_map)

print("\n=== Kategori dagilimi ===")
print(gdf['category'].value_counts())

# Final CSV
final = gdf[['name', 'category', 'weight', 'lat', 'lon']].copy()
final.to_csv(OUTPUT_PATH, index=False)
print(f"\nKaydedildi: {OUTPUT_PATH}")
print(f"Toplam: {len(final)} istasyon")
print(final.head(5))