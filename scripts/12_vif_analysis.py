# scripts/12_vif_analysis.py

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant

df = pd.read_csv('../data/istanbul_emlak_with_geo.csv')
df = df[df['total_rooms'] <= 6].copy().reset_index(drop=True)

# Train split (VIF train uzerinden hesaplanir)
df['log_price'] = np.log1p(df['price'])
df['area_x_walk'] = df['area_m2'] * df['walkability_score']

idx = df.index.to_numpy()
idx_temp, idx_test = train_test_split(idx, test_size=0.20, random_state=42)
idx_train, idx_val = train_test_split(idx_temp, test_size=0.25, random_state=42)

dist_med = df.loc[idx_train].groupby('district')['price'].median()
df['dist_med_price'] = df['district'].map(dist_med).fillna(df.loc[idx_train]['price'].median())

# Sadece numeric feature'lar (room dummy'leri VIF'te lazim degil)
all_numeric = ['area_m2', 'total_rooms', 'walkability_score', 'area_x_walk', 'dist_med_price',
               'nearest_metro_km', 'metro_500m', 'metro_1km', 'weighted_1km',
               'cafe_1km', 'restaurant_1km', 'university_2km', 'park_1km',
               'is_periphery', 'is_district_center']

X_train = df.loc[idx_train, all_numeric].copy()
X_train = add_constant(X_train)

print("=== VIF Degerleri (Train Set) ===")
print("(VIF > 5: yuksek collinearity, VIF > 10: ciddi)")
print()
vif_data = []
for i, col in enumerate(X_train.columns):
    if col == 'const':
        continue
    vif = variance_inflation_factor(X_train.values, i)
    vif_data.append({'feature': col, 'VIF': vif})

vif_df = pd.DataFrame(vif_data).sort_values('VIF', ascending=False)
print(vif_df.to_string(index=False))

print("\n=== Korelasyon Matrisi (Metro feature'lar arasi) ===")
metro_cols = ['nearest_metro_km', 'metro_500m', 'metro_1km', 'weighted_1km']
print(df.loc[idx_train, metro_cols].corr().round(3).to_string())

print("\n=== Karar Onerisi ===")
high_vif = vif_df[vif_df['VIF'] > 5]
if len(high_vif) > 0:
    print(f"VIF > 5 olan {len(high_vif)} feature var:")
    for _, row in high_vif.iterrows():
        print(f"  - {row['feature']}: VIF = {row['VIF']:.2f}")
    print("\nBunlardan birini/birkacini cikarmak gerekir.")
else:
    print("Tum feature'lar VIF < 5, multicollinearity sorun degil.")