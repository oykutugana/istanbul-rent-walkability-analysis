"""
Yeni geo feature'larla P2'nin 5 modelini calistir.
Sayilari gor, sonra notebook'a guvenle yaz.
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import LinearRegression, RidgeCV, LassoCV
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

df = pd.read_csv('../data/istanbul_emlak_with_geo.csv')
df['log_price'] = np.log1p(df['price'])
df['area_x_walk'] = df['area_m2'] * df['walkability_score']
df_enc = pd.get_dummies(df, columns=['room_count'], prefix='room', drop_first=True, dtype=int)
room_cols = [c for c in df_enc.columns if c.startswith('room_')]

idx = df_enc.index.to_numpy()
idx_temp, idx_test = train_test_split(idx, test_size=0.20, random_state=42)
idx_train, idx_val = train_test_split(idx_temp, test_size=0.25, random_state=42)

# Train'den district_med_price hesapla (P2'deki gibi)
dist_med = df.loc[idx_train].groupby('district')['price'].median()
df_enc['dist_med_price'] = df_enc['district'].map(dist_med).fillna(df.loc[idx_train]['price'].median())

# Yeni feature seti = eski + geo
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

print(f"Toplam feature: {len(features)}")
print(f"Train: {Xtr.shape}, Val: {Xv.shape}, Test: {Xte.shape}\n")

# Baseline (sadece area_m2) - DEGISMEZ ama kontrol icin
b = LinearRegression()
b.fit(Xtr[:, [0]], y_train)
pred_v = np.expm1(b.predict(Xv[:, [0]]))
pred_te = np.expm1(b.predict(Xte[:, [0]]))
print(f"=== BASELINE (sadece area_m2) ===")
print(f"  Val R²: {r2_score(yv_o, pred_v):.4f}, Test R²: {r2_score(yte_o, pred_te):.4f}")
print(f"  Test RMSE: {np.sqrt(mean_squared_error(yte_o, pred_te)):,.0f}")

# Multiple LR
m = LinearRegression()
m.fit(Xtr, y_train)
pred_v = np.expm1(m.predict(Xv))
pred_te = np.expm1(m.predict(Xte))
print(f"\n=== MULTIPLE LR (eski + geo) ===")
print(f"  Train R²: {r2_score(ytr_o, np.expm1(m.predict(Xtr))):.4f}")
print(f"  Val R²: {r2_score(yv_o, pred_v):.4f}, Test R²: {r2_score(yte_o, pred_te):.4f}")
print(
    f"  Test RMSE: {np.sqrt(mean_squared_error(yte_o, pred_te)):,.0f}, MAE: {mean_absolute_error(yte_o, pred_te):,.0f}")

# Polynomial
num_idx = list(range(len(old_numeric) + len(geo_numeric)))
dum_idx = list(range(len(old_numeric) + len(geo_numeric), Xtr.shape[1]))

print(f"\n=== POLYNOMIAL (eski + geo) ===")
for deg in [1, 2, 3]:
    poly = PolynomialFeatures(degree=deg, include_bias=False)
    Xtr_p = np.hstack([poly.fit_transform(Xtr[:, num_idx]), Xtr[:, dum_idx]])
    Xv_p = np.hstack([poly.transform(Xv[:, num_idx]), Xv[:, dum_idx]])
    Xte_p = np.hstack([poly.transform(Xte[:, num_idx]), Xte[:, dum_idx]])

    mp = LinearRegression()
    mp.fit(Xtr_p, y_train)

    tr_r2 = r2_score(ytr_o, np.expm1(mp.predict(Xtr_p)))
    v_r2 = r2_score(yv_o, np.expm1(mp.predict(Xv_p)))
    te_r2 = r2_score(yte_o, np.expm1(mp.predict(Xte_p)))
    print(f"  Deg {deg} (n_feat={Xtr_p.shape[1]}): Train {tr_r2:.4f} | Val {v_r2:.4f} | Test {te_r2:.4f}")

# Ridge
r = RidgeCV(alphas=[0.001, 0.01, 0.1, 1, 10, 100, 1000], cv=5)
r.fit(Xtr, y_train)
pred_v = np.expm1(r.predict(Xv))
pred_te = np.expm1(r.predict(Xte))
print(f"\n=== RIDGE (eski + geo) ===")
print(f"  alpha: {r.alpha_}")
print(f"  Val R²: {r2_score(yv_o, pred_v):.4f}, Test R²: {r2_score(yte_o, pred_te):.4f}")

# Lasso
la = LassoCV(alphas=[0.0001, 0.001, 0.01, 0.1, 1], cv=5, max_iter=20000, random_state=42)
la.fit(Xtr, y_train)
pred_v = np.expm1(la.predict(Xv))
pred_te = np.expm1(la.predict(Xte))
zeroed = sum(c == 0 for c in la.coef_)
print(f"\n=== LASSO (eski + geo) ===")
print(f"  alpha: {la.alpha_}")
print(f"  Val R²: {r2_score(yv_o, pred_v):.4f}, Test R²: {r2_score(yte_o, pred_te):.4f}")
print(f"  Zeroed: {zeroed}/{len(la.coef_)}")
print(f"  Zeroed features: {[features[i] for i, c in enumerate(la.coef_) if c == 0]}")