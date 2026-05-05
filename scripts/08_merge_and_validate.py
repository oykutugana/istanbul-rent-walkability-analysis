"""
Mahalle-level feature'lari listing-level ana CSV'ye join eder.
Sanity check + gozlem analizi.
"""
import pandas as pd
import numpy as np

DATA_PATH = '../data/istanbul_emlak_final.csv'
COORD_PATH = '../data/neighborhood_coordinates.csv'
FEAT_PATH = '../data/neighborhood_features.csv'
OUTPUT_PATH = '../data/istanbul_emlak_with_geo.csv'

# Yukle
df = pd.read_csv(DATA_PATH)
coords = pd.read_csv(COORD_PATH)
feats = pd.read_csv(FEAT_PATH)

print(f"Ana dataset: {len(df)} listing")
print(f"Koordinatlar: {len(coords)} mahalle")
print(f"Feature'lar: {len(feats)} mahalle")

# Coords'tan strategy ve is_periphery'yi al
coord_extras = coords[['district', 'neighborhood', 'lat', 'lon', 'strategy', 'is_periphery']].copy()
coord_extras = coord_extras.rename(columns={'lat': 'nh_lat', 'lon': 'nh_lon', 'strategy': 'geocode_strategy'})

# Once feat'leri coord_extras ile birlestir (mahalle bazli, 447 satir)
nh_table = coord_extras.merge(feats, on=['district', 'neighborhood'], how='left')
print(f"\nMahalle tablosu: {len(nh_table)} satir, kolonlar: {nh_table.columns.tolist()}")

# Sanity: NaN feature var mi?
nan_cols = nh_table.isna().sum()
print(f"\nMahalle bazinda NaN sayilari:")
print(nan_cols[nan_cols > 0])

# is_geocoded_to_district_center flag (modele sinyal)
nh_table['is_district_center'] = nh_table['geocode_strategy'].isin(
    ['fallback', 'manual_district_center']
).astype(int)

# Listing'lere join
df_geo = df.merge(nh_table, on=['district', 'neighborhood'], how='left')
print(f"\nJoin sonrasi listing: {len(df_geo)}")

# Sanity check: kac listing eksik koordinat aldi
missing_coord = df_geo['nh_lat'].isna().sum()
print(f"Koordinat alamayan listing: {missing_coord}")

if missing_coord > 0:
    eksik = df_geo[df_geo['nh_lat'].isna()][['district', 'neighborhood']].drop_duplicates()
    print(f"\nKoordinatsiz mahalleler ({len(eksik)} adet):")
    print(eksik.to_string(index=False))

# Sanity: feature istatistikleri (listing seviyesinde, weighted by listing count)
print(f"\n=== LISTING-LEVEL FEATURE OZETI ===")
feat_cols = ['nearest_metro_km', 'metro_500m', 'metro_1km', 'weighted_1km',
             'cafe_1km', 'restaurant_1km', 'university_2km', 'park_1km']
print(df_geo[feat_cols].describe().round(2))

# Spot check: bilinen mahalleler
print(f"\n=== SPOT CHECK ===")
spot = [
    ('besiktas', 'bebek'),
    ('fatih', 'aksaray'),
    ('kadikoy', 'caferaga'),
    ('esenyurt', 'merkez'),
    ('sile', 'cavus'),
]
for d, n in spot:
    sub = df_geo[(df_geo['district'] == d) & (df_geo['neighborhood'] == n)].head(1)
    if len(sub) > 0:
        r = sub.iloc[0]
        print(f"{d}/{n}: metro={r['nearest_metro_km']:.2f}km, cafe={r['cafe_1km']}, "
              f"univ={r['university_2km']}, park={r['park_1km']}, periphery={r['is_periphery']}")

# Korelasyon: yeni feature'lar fiyatla nasil iliskili?
print(f"\n=== YENI FEATURE'LARIN FIYAT KORELASYONU ===")
for col in feat_cols:
    corr = df_geo[col].corr(df_geo['price'])
    print(f"  {col:<20}: {corr:+.3f}")

# P1'in walkability_score'u ile karsilastir (eger varsa)
if 'walkability_score' in df_geo.columns:
    print(f"\nP1 walkability_score korelasyonu (karsilastirma): "
          f"{df_geo['walkability_score'].corr(df_geo['price']):+.3f}")

# Kaydet
df_geo.to_csv(OUTPUT_PATH, index=False)
print(f"\nKaydedildi: {OUTPUT_PATH}")
print(f"Final shape: {df_geo.shape}")