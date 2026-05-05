# scripts/15_v3_full_test.py

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import LinearRegression, RidgeCV, LassoCV
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

RANDOM_STATE = 42

df = pd.read_csv('../data/istanbul_emlak_with_geo.csv')
df = df[df['total_rooms'] <= 6].copy().reset_index(drop=True)
df['log_price'] = np.log1p(df['price'])

# Split
idx = df.index.to_numpy()
idx_temp, idx_test = train_test_split(idx, test_size=0.20, random_state=RANDOM_STATE)
idx_train, idx_val = train_test_split(idx_temp, test_size=0.25, random_state=RANDOM_STATE)

# District median (train-only)
dist_med = df.loc[idx_train].groupby('district')['price'].median()
df['dist_med_price'] = df['district'].map(dist_med).fillna(df.loc[idx_train]['price'].median())

# One-hot encode
df_enc = pd.get_dummies(df, columns=['room_count'], prefix='room', drop_first=True, dtype=int)
room_cols = [c for c in df_enc.columns if c.startswith('room_')]

# FINAL 10 numeric (VIF temizlenmis)
numeric_features = [
    'area_m2', 'total_rooms', 'walkability_score', 'dist_med_price',
    'nearest_metro_km', 'weighted_1km',
    'restaurant_1km', 'university_2km', 'park_1km',
    'is_district_center'
]
features = numeric_features + room_cols

X = df_enc[features]
y = df_enc['log_price']

X_train, X_val, X_test = X.loc[idx_train], X.loc[idx_val], X.loc[idx_test]
y_train, y_val, y_test = y.loc[idx_train], y.loc[idx_val], y.loc[idx_test]

# Scale
scaler = StandardScaler()
Xtr = scaler.fit_transform(X_train)
Xv = scaler.transform(X_val)
Xte = scaler.transform(X_test)

ytr_o = np.expm1(y_train)
yv_o = np.expm1(y_val)
yte_o = np.expm1(y_test)

print(f"Toplam feature: {len(features)} ({len(numeric_features)} numeric + {len(room_cols)} room dummy)")
print(f"Train: {len(idx_train)}, Val: {len(idx_val)}, Test: {len(idx_test)}\n")

def evaluate(name, model, Xtr, Xv, Xte):
    pred_tr = np.expm1(model.predict(Xtr))
    pred_v = np.expm1(model.predict(Xv))
    pred_te = np.expm1(model.predict(Xte))
    return {
        'Model': name,
        'Train R²': r2_score(ytr_o, pred_tr),
        'Val R²': r2_score(yv_o, pred_v),
        'Test R²': r2_score(yte_o, pred_te),
        'Test RMSE': np.sqrt(mean_squared_error(yte_o, pred_te)),
        'Test MAE': mean_absolute_error(yte_o, pred_te),
    }

results = []

# 1) Baseline (sadece area_m2)
b = LinearRegression()
b.fit(Xtr[:, [0]], y_train)
results.append(evaluate('Baseline (area_m2)', b, Xtr[:, [0]], Xv[:, [0]], Xte[:, [0]]))

# 2) Multiple LR
mlr = LinearRegression()
mlr.fit(Xtr, y_train)
results.append(evaluate('Multiple LR', mlr, Xtr, Xv, Xte))

# 3) Polynomial deg 1, 2, 3 (plain LR)
num_idx = list(range(len(numeric_features)))
dum_idx = list(range(len(numeric_features), Xtr.shape[1]))

for deg in [1, 2, 3]:
    poly = PolynomialFeatures(degree=deg, include_bias=False)
    Xtr_p = np.hstack([poly.fit_transform(Xtr[:, num_idx]), Xtr[:, dum_idx]])
    Xv_p = np.hstack([poly.transform(Xv[:, num_idx]), Xv[:, dum_idx]])
    Xte_p = np.hstack([poly.transform(Xte[:, num_idx]), Xte[:, dum_idx]])

    m = LinearRegression()
    m.fit(Xtr_p, y_train)
    res = evaluate(f'Polynomial deg {deg} (plain LR)', m, Xtr_p, Xv_p, Xte_p)
    res['n_features'] = Xtr_p.shape[1]
    res['max_coef'] = np.abs(m.coef_).max()
    results.append(res)

# 4) Polynomial deg 2, 3 (Ridge)
for deg in [2, 3]:
    poly = PolynomialFeatures(degree=deg, include_bias=False)
    Xtr_p = np.hstack([poly.fit_transform(Xtr[:, num_idx]), Xtr[:, dum_idx]])
    Xv_p = np.hstack([poly.transform(Xv[:, num_idx]), Xv[:, dum_idx]])
    Xte_p = np.hstack([poly.transform(Xte[:, num_idx]), Xte[:, dum_idx]])

    m = RidgeCV(alphas=[0.01, 0.1, 1, 10, 100, 1000], cv=5)
    m.fit(Xtr_p, y_train)
    res = evaluate(f'Polynomial deg {deg} Ridge (α={m.alpha_})', m, Xtr_p, Xv_p, Xte_p)
    res['n_features'] = Xtr_p.shape[1]
    results.append(res)

# 5) Ridge (base feature set)
ridge = RidgeCV(alphas=[0.001, 0.01, 0.1, 1, 10, 100, 1000], cv=5)
ridge.fit(Xtr, y_train)
results.append(evaluate(f'Ridge (α={ridge.alpha_})', ridge, Xtr, Xv, Xte))

# 6) Lasso
lasso = LassoCV(alphas=[0.0001, 0.001, 0.01, 0.1, 1], cv=5, max_iter=20000, random_state=RANDOM_STATE)
lasso.fit(Xtr, y_train)
results.append(evaluate(f'Lasso (α={lasso.alpha_})', lasso, Xtr, Xv, Xte))
n_zero = (lasso.coef_ == 0).sum()

# Print
df_results = pd.DataFrame(results)
print("=" * 100)
print("V3 MODEL TEST SONUCLARI")
print("=" * 100)
for col in ['Train R²', 'Val R²', 'Test R²']:
    df_results[col] = df_results[col].apply(lambda x: f"{x:.4f}" if isinstance(x, (int, float)) and abs(x) < 100 else f"{x:.2e}")
df_results['Test RMSE'] = df_results['Test RMSE'].apply(lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else x)
df_results['Test MAE'] = df_results['Test MAE'].apply(lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else x)
print(df_results.to_string(index=False))

print(f"\nLasso zeroed feature sayisi: {n_zero}/{len(features)}")
print(f"\nLasso zeroed features:")
zeroed = [features[i] for i, c in enumerate(lasso.coef_) if c == 0.0]
for f in zeroed:
    print(f"  - {f}")

# Coefficient analizi (Multiple LR)
print(f"\n=== Multiple LR Top 10 Coefficient ===")
coefs = pd.DataFrame({'feature': features, 'coef': mlr.coef_, 'abs': np.abs(mlr.coef_)})
print(coefs.sort_values('abs', ascending=False).head(10).to_string(index=False))