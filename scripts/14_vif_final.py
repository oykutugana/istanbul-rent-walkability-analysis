# scripts/14_vif_final.py

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant

df = pd.read_csv('../data/istanbul_emlak_with_geo.csv')
df = df[df['total_rooms'] <= 6].copy().reset_index(drop=True)

idx = df.index.to_numpy()
idx_temp, idx_test = train_test_split(idx, test_size=0.20, random_state=42)
idx_train, idx_val = train_test_split(idx_temp, test_size=0.25, random_state=42)

dist_med = df.loc[idx_train].groupby('district')['price'].median()
df['dist_med_price'] = df['district'].map(dist_med).fillna(df.loc[idx_train]['price'].median())

# FINAL temiz feature seti (10 numeric)
final_numeric = [
    'area_m2', 'total_rooms', 'walkability_score', 'dist_med_price',
    'nearest_metro_km', 'weighted_1km',
    'restaurant_1km', 'university_2km', 'park_1km',
    'is_district_center'
]

X_train = df.loc[idx_train, final_numeric].copy()
X_train = add_constant(X_train)

print("=== VIF Final (10 feature) ===")
vif_data = []
for i, col in enumerate(X_train.columns):
    if col == 'const':
        continue
    vif = variance_inflation_factor(X_train.values, i)
    vif_data.append({'feature': col, 'VIF': vif})

vif_df = pd.DataFrame(vif_data).sort_values('VIF', ascending=False)
print(vif_df.to_string(index=False))

print(f"\nVIF > 5: {(vif_df['VIF'] > 5).sum()} feature")
print(f"VIF > 10: {(vif_df['VIF'] > 10).sum()} feature")
print(f"Max VIF: {vif_df['VIF'].max():.2f}")