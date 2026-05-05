"""
Hizli Random Forest testi: yeni feature'lar bir arada ne kadar guclu?
P2 ile karsilastirir.
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error

df = pd.read_csv('../data/istanbul_emlak_with_geo.csv')
df['log_price'] = np.log1p(df['price'])

# Ortak split
y = df['log_price']
y_orig = df['price']

# Set 1: Sadece P1/P2 feature'lari (eski set)
old_feats = ['area_m2', 'total_rooms', 'walkability_score']
df_old = df.copy()
df_old = pd.get_dummies(df_old, columns=['room_count'], prefix='room', drop_first=True)
room_cols = [c for c in df_old.columns if c.startswith('room_')]
X_old = df_old[old_feats + room_cols]

# Set 2: P1/P2 feature'lari + yeni geo feature'lar
new_geo = ['nearest_metro_km', 'metro_500m', 'metro_1km', 'weighted_1km',
           'cafe_1km', 'restaurant_1km', 'university_2km', 'park_1km',
           'is_periphery', 'is_district_center']
X_new = df_old[old_feats + new_geo + room_cols]

results = {}
for name, X in [('Eski (P2 feature set)', X_old), ('Yeni (eski + geo)', X_new)]:
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
    yte_orig = np.expm1(yte)

    rf = RandomForestRegressor(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1)
    rf.fit(Xtr, ytr)
    pred = np.expm1(rf.predict(Xte))

    r2 = r2_score(yte_orig, pred)
    rmse = np.sqrt(mean_squared_error(yte_orig, pred))
    results[name] = (r2, rmse, rf, X.columns.tolist())
    print(f"\n=== {name} ===")
    print(f"Test R²: {r2:.4f}")
    print(f"Test RMSE: {rmse:,.0f} TL")
    print(f"Feature sayisi: {X.shape[1]}")

# Karsilastirma
old_r2, old_rmse, _, _ = results['Eski (P2 feature set)']
new_r2, new_rmse, new_rf, new_cols = results['Yeni (eski + geo)']
print(f"\n=== FARK ===")
print(f"R² iyilesmesi: +{new_r2 - old_r2:.4f} ({100 * (new_r2 - old_r2) / old_r2:+.1f}%)")
print(f"RMSE iyilesmesi: {new_rmse - old_rmse:+,.0f} TL")

# Yeni feature importance
print(f"\n=== YENI FEATURE'LARIN ONEMI (Random Forest) ===")
imp = pd.Series(new_rf.feature_importances_, index=new_cols)
imp_sorted = imp.sort_values(ascending=False).head(15)
for f, v in imp_sorted.items():
    print(f"  {f:<25} {v:.4f}")