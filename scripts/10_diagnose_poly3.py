"""
Polynomial deg 3 patlamasinin sebebini test et.
Ridge ile deg 3 calisir mi?
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import LinearRegression, Ridge, RidgeCV
from sklearn.metrics import r2_score, mean_squared_error

df = pd.read_csv('../data/istanbul_emlak_with_geo.csv')
df['log_price'] = np.log1p(df['price'])
df['area_x_walk'] = df['area_m2'] * df['walkability_score']
df_enc = pd.get_dummies(df, columns=['room_count'], prefix='room', drop_first=True, dtype=int)
room_cols = [c for c in df_enc.columns if c.startswith('room_')]

idx = df_enc.index.to_numpy()
idx_temp, idx_test = train_test_split(idx, test_size=0.20, random_state=42)
idx_train, idx_val = train_test_split(idx_temp, test_size=0.25, random_state=42)

dist_med = df.loc[idx_train].groupby('district')['price'].median()
df_enc['dist_med_price'] = df_enc['district'].map(dist_med).fillna(df.loc[idx_train]['price'].median())

old_numeric = ['area_m2', 'total_rooms', 'walkability_score', 'area_x_walk', 'dist_med_price']
geo_numeric = ['nearest_metro_km', 'metro_500m', 'metro_1km', 'weighted_1km',
               'cafe_1km', 'restaurant_1km', 'university_2km', 'park_1km',
               'is_periphery', 'is_district_center']

features = old_numeric + geo_numeric + room_cols
X = df_enc[features]
y = df_enc['log_price']

X_train, X_val, X_test = X.loc[idx_train], X.loc[idx_val], X.loc[idx_test]
y_train, y_val, y_test = y.loc[idx_train], y.loc[idx_val], y.loc[idx_test]

scaler = StandardScaler()
Xtr = scaler.fit_transform(X_train)
Xv = scaler.transform(X_val)
Xte = scaler.transform(X_test)

ytr_o = np.expm1(y_train)
yv_o = np.expm1(y_val)
yte_o = np.expm1(y_test)

num_idx = list(range(len(old_numeric) + len(geo_numeric)))
dum_idx = list(range(len(old_numeric) + len(geo_numeric), Xtr.shape[1]))

print("=== TEST 1: Plain LinearRegression deg 3 ===")
poly = PolynomialFeatures(degree=3, include_bias=False)
Xtr_p = np.hstack([poly.fit_transform(Xtr[:, num_idx]), Xtr[:, dum_idx]])
Xv_p = np.hstack([poly.transform(Xv[:, num_idx]), Xv[:, dum_idx]])
Xte_p = np.hstack([poly.transform(Xte[:, num_idx]), Xte[:, dum_idx]])
print(f"Feature sayisi: {Xtr_p.shape[1]}")

m = LinearRegression()
m.fit(Xtr_p, y_train)
print(f"Test R²: {r2_score(yte_o, np.expm1(m.predict(Xte_p))):.4f}")
print(f"En buyuk coefficient: {np.abs(m.coef_).max():.2e}")
print(f"Coefficient sayisi: {len(m.coef_)}")

print("\n=== TEST 2: Ridge alpha=1.0 deg 3 ===")
r = Ridge(alpha=1.0)
r.fit(Xtr_p, y_train)
print(f"Train R²: {r2_score(ytr_o, np.expm1(r.predict(Xtr_p))):.4f}")
print(f"Val R²: {r2_score(yv_o, np.expm1(r.predict(Xv_p))):.4f}")
print(f"Test R²: {r2_score(yte_o, np.expm1(r.predict(Xte_p))):.4f}")
print(f"En buyuk coefficient: {np.abs(r.coef_).max():.2e}")

print("\n=== TEST 3: RidgeCV deg 3 (optimal alpha) ===")
rcv = RidgeCV(alphas=[0.01, 0.1, 1, 10, 100, 1000], cv=5)
rcv.fit(Xtr_p, y_train)
print(f"Optimal alpha: {rcv.alpha_}")
print(f"Train R²: {r2_score(ytr_o, np.expm1(rcv.predict(Xtr_p))):.4f}")
print(f"Val R²: {r2_score(yv_o, np.expm1(rcv.predict(Xv_p))):.4f}")
print(f"Test R²: {r2_score(yte_o, np.expm1(rcv.predict(Xte_p))):.4f}")

print("\n=== TEST 4: deg 2 karsilastirma (Plain LR) ===")
poly2 = PolynomialFeatures(degree=2, include_bias=False)
Xtr_p2 = np.hstack([poly2.fit_transform(Xtr[:, num_idx]), Xtr[:, dum_idx]])
Xv_p2 = np.hstack([poly2.transform(Xv[:, num_idx]), Xv[:, dum_idx]])
Xte_p2 = np.hstack([poly2.transform(Xte[:, num_idx]), Xte[:, dum_idx]])

m2 = LinearRegression()
m2.fit(Xtr_p2, y_train)
print(f"Feature sayisi: {Xtr_p2.shape[1]}")
print(f"Train R²: {r2_score(ytr_o, np.expm1(m2.predict(Xtr_p2))):.4f}")
print(f"Val R²: {r2_score(yv_o, np.expm1(m2.predict(Xv_p2))):.4f}")
print(f"Test R²: {r2_score(yte_o, np.expm1(m2.predict(Xte_p2))):.4f}")

print("\n=== ozet ===")
print("Deg 2 plain LR vs Deg 3 ridge: hangisi daha iyi karar verecegiz")