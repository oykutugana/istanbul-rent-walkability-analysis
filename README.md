# **Istanbul Rental Market & Walkability Analysis** 

> **Project Link:** **[github.com/oykutugana/istanbul-rent-walkability-analysis](https://github.com/oykutugana/istanbul-rent-walkability-analysis)**

This project analyzes rental prices in Istanbul by combining traditional housing features with a custom-engineered Walkability Score and a Student Suitability Index. The goal is to identify the 'sweet spots' in the market — areas that optimize the trade-off between urban accessibility and rental affordability for students. Phase 2 builds regression models to predict rental prices, first with district-level features, then with a richer neighbourhood-level geographic feature set engineered from real-world map data.

---

## **Overview**
Istanbul's rental market is highly dynamic and influenced by diverse factors. While size and room count are standard, **urban accessibility** is often undervalued in data models. This project introduces a **"Walkability Score"** to quantify how proximity to transport, universities, and social hubs affects market value. It serves as a comprehensive guide for students and young professionals seeking optimal living conditions.

---

## **Dataset**

The analysis is built upon a high-quality, refined dataset of rental listings across Istanbul's 39 districts.

**Primary Data Source:** The raw data consists of real estate listings web-scraped from **Sahibinden.com**, Turkey's premier classifieds platform. After cleaning and outlier removal, the final dataset contains **11,733 listings**, ensuring the study reflects realistic residential market dynamics.

#### **Data Composition**
| Feature | Description |
| :--- | :--- |
| **Price (TL)** | Monthly rental fee (Target Variable). |
| **Area (m²)** | Gross square meters of the property. |
| **Room Count** | Number of rooms and living areas (e.g., 2+1, 3+1). |
| **Location** | District (39) and Neighbourhood (380) level granularity. |
| **Walkability Score** | Custom engineered feature (0-100), district-level. |
| **Student Score** | A weighted index (50% Walkability, 50% Per-Room Affordability) for optimal housing selection. |

#### **Data Cleaning & Refinement**
To ensure the model's reliability, we applied domain-based outlier filtering rather than purely statistical bounds:
* **Price Range:** 12,000 TL – 150,000 TL (removes typo entries below 12k and luxury outliers above 150k)
* **Area Range:** 30 m² – 250 m² (drops tiny micro-units and oversized commercial-style flats)
* **Total Rooms:** ≤ 6 (removes rare 7+1 and 8+ configurations that act as extreme leverage points in regression)
* **Neighbourhood names:** Parenthesised aliases (e.g. `celaliye(kamiloba)`) and slash-separated names (e.g. `barbaros/yesilbag`) were cleaned to their primary form.

#### **Geospatial Integration (P2 v2 — Neighbourhood Level)**
In P2 v2 we moved beyond district-level aggregation and geocoded **447 unique (district, neighbourhood) pairs** to map coordinates using Nominatim with a three-strategy validation pipeline (tight → medium → fallback). From each neighbourhood centroid we computed:

* **Transit access:** Haversine distance to the closest metro/Marmaray station and weighted station counts within 1 km radius, drawing on **220 Istanbul rail stations** sourced from OpenStreetMap.
* **POI density:** Counts of cafes, restaurants, university campuses, and parks within 1–2 km buffers via OSMnx.
* **Data-quality flags:** `is_periphery` (Silivri/Şile/Çatalca, where OSM coverage is sparse) and `is_district_center` (listings whose neighbourhood could only be resolved to district-level coordinates).

---

## **The Project Trilogy: Connecting the Dots**

| Phase | Focus | Key Deliverable |
|:---|:---|:---|
| **Phase 1: Problem & EDA** | **Data Cleaning & Engineering** | Problem formulation, outlier handling, walkability score, student suitability index, and visual EDA across 39 districts. |
| **Phase 2: Regression** | **Linear & Polynomial Models (two iterations)** | v1: district-level features, linear/polynomial/Ridge/Lasso, R² ~0.46. v2: neighbourhood-level geo engineering, same models, R² ~0.58. |
| **Phase 3: Beyond Regression** | **Model Selection & Reporting** | Tree-based models (Random Forest / Gradient Boosting), hyperparameter tuning, feature importance (SHAP), and final comprehensive report. |

## **Key Questions**

- How do structural features (size, rooms) vs. locational features (walkability, metro distance) affect rental prices?
- To what extent does urban accessibility influence the "price premium" in central districts?
- Which features are the strongest predictors of rental price for a machine learning model?
- Where are the **"Student Sweet Spots"** — districts with high walkability but affordable per-room rents?
- How can we mathematically balance urban accessibility with budget constraints to find the most "student-friendly" neighborhoods?

---

## **Methods**

### **1. Domain-Based Threshold Filtering**
Instead of purely statistical outlier removal, we applied real-world market limits to preserve high-value but legitimate listings (see Dataset section for exact bounds).

### **2. Feature Engineering (Walkability Index)**
A weighted composite score calculated based on proximity to essential amenities:

$$
Score = (Transport \times 0.5) + (University \times 0.3) + (Social\_Infrastructure \times 0.2)
$$

Computed for all 39 districts. Used in both P1 EDA and P2 v1/v2 regression.

### **3. Feature Engineering (Student Suitability Index)**
A composite index balancing accessibility with **per-room affordability**:

$$
SSI = (Walkability\_Score \times 0.5) + (Affordability\_Score \times 0.5)
$$

Where Affordability Score is derived from `price_per_room = price / total_rooms`, then converted to a 0-100 scale via percentile rank inversion. This per-room formulation rewards larger shared apartments where cost distributes across tenants.

### **4. Neighbourhood-Level Geographic Feature Engineering (P2 v2)**
To address the within-district heterogeneity identified in P2 v1 residuals (e.g. Bebek vs. Dikilitaş in Beşiktaş sharing the same district score), we built a full offline pipeline:

1. **Geocoding** — 447 unique (district, neighbourhood) pairs geocoded with Nominatim using a three-strategy validation (tight → medium → district-center fallback). 370 resolved at neighbourhood level, 49 at district level, 19 peripheral locations handled manually.
2. **Metro distance** — Haversine distance to 220 OpenStreetMap rail stations (metro, Marmaray, tram, funicular), each weighted by service type.
3. **POI counts** — OSMnx queries within 1–2 km buffers for cafes, restaurants, universities, and parks.
4. **Data-quality flags** — periphery and district-center fallback indicators.

### **5. Correlation and Residual Analysis**
Pearson Correlation, Binned Trend Analysis, and residual diagnostics (residuals vs. fitted, Q-Q plot, histogram) to identify model limitations and guide iterative improvement.

---

## **P1 Results**

- **The Power of Size:** Square footage (m²) is the strongest single predictor of price (r ≈ 0.50).
- **The Accessibility Premium:** Walkability shows a moderate positive correlation with price (r ≈ 0.32), with significant price spikes in highly walkable districts like **Beşiktaş**, **Kadıköy**, and **Şişli**.
- **The Old Center Paradox:** The walkability-vs-price relationship is non-monotonic. Prices climb with walkability up to the 70-80 range (~52k TL median), then drop sharply at the 80-100 range (~30k TL) where historical centers like Fatih dominate with older, smaller stock.
- **Student Score Trade-off:** A strong negative correlation between student score and price (r ≈ -0.54) confirms the mathematical consistency of the per-room methodology.
- **Top Student-Friendly Districts:** Under per-room affordability, **Fatih** leads decisively (85.97), followed by peripheral districts like **Avcılar (69.20), Bağcılar (67.32), Küçükçekmece (61.17)** that benefit from larger, affordable apartments.
- **District Prestige Premium:** **Kadıköy** holds the highest price-per-m² (~720 TL/m²) — Beşiktaş ranks only 13th.

---

## **P2 Results — Regression Modeling**

P2 was completed in two iterations. v1 used the original P1 feature set. v2 enriched the dataset with neighbourhood-level geographic features and re-ran the full pipeline.

### **P2 v1 — District-Level Features**

Four engineered features: log target, area × walkability interaction, district median price (target encoding), room count one-hot encoding.

| Model | Train R² | Val R² | Test R² | Test RMSE | Test MAE |
|:---|:---:|:---:|:---:|:---:|:---:|
| Baseline (area_m2 only) | 0.215 | 0.221 | 0.233 | 22,585 TL | 15,972 TL |
| Multiple LR | 0.470 | 0.493 | 0.462 | 18,924 TL | 13,050 TL |
| **Polynomial (degree 3)** | **0.510** | **0.510** | **0.464** | **18,880 TL** | **12,674 TL** |
| Ridge (α = 10) | 0.470 | 0.492 | 0.462 | 18,927 TL | 13,050 TL |
| Lasso (α = 0.001) | 0.470 | 0.492 | 0.462 | 18,913 TL | 13,041 TL |

**v1 best model:** Polynomial degree 3. **v1 ceiling: test R² ≈ 0.46.** Residual analysis revealed within-district heterogeneity as the main bottleneck — one district label cannot distinguish, for example, Bebek from Dikilitaş in Beşiktaş.

### **P2 v2 — Neighbourhood-Level Geographic Features**

Ten additional features added: `nearest_metro_km`, `metro_500m`, `metro_1km`, `weighted_1km`, `cafe_1km`, `restaurant_1km`, `university_2km`, `park_1km`, `is_periphery`, `is_district_center`.

| Model | Train R² | Val R² | Test R² | Test RMSE | Test MAE |
|:---|:---:|:---:|:---:|:---:|:---:|
| Baseline (area_m2 only) | 0.215 | 0.221 | 0.233 | 22,585 TL | 15,972 TL |
| Multiple LR | 0.470 | 0.493 | 0.476 | 18,935 TL | 13,056 TL |
| **Polynomial (degree 2)** | **0.573** | **0.591** | **0.575** | **16,943 TL** | **11,842 TL** |
| Ridge (α = 1) | 0.470 | 0.493 | 0.476 | 18,937 TL | 13,056 TL |
| Lasso (α = 0.001) | 0.470 | 0.493 | 0.476 | 18,922 TL | 13,046 TL |

**v2 best model:** Polynomial degree 2 (plain LR). Polynomial degree 3 causes numerical explosion due to multi-collinearity among correlated metro-density features — Ridge at degree 3 stabilises the model but does not outperform plain degree 2.

### **Key v2 Findings**

- **Geographic granularity matters more than model complexity.** Multiple LR improved by only +0.014 with the new features, but polynomial degree 2 improved by **+0.111** — the interaction terms between geographic features capture non-linear urban pricing patterns that no linear combination can reach.
- **Multi-collinearity is visible but manageable.** `metro_1km` and `weighted_1km` measure overlapping concepts and show opposite coefficient signs — a known multi-collinearity artefact. Ridge regularisation handles this correctly; test R² confirms the model performs well despite the coefficient paradox.
- **Polynomial degree 3 explodes without regularisation.** At 831 features, OLS matrix inversion fails numerically. This is the clearest signal that linear-family models have hit their architectural ceiling on this dataset.
- **Predictions improved but remain approximate.** Test RMSE dropped from ~18,900 TL (v1) to ~16,900 TL (v2). A ~11-12k TL average absolute error against a 36k TL median rent is useful for budget planning, not for exact pricing.
- **`student_score` and `price_per_room` excluded** — both are derived from the target variable and would cause target leakage.

### **Implications for P3**
The ~0.58 v2 ceiling confirms that the remaining variance requires non-linear models. A preliminary Random Forest test on the v2 feature set produced test R² **0.665** — a further **+0.09** gain with no additional feature engineering. P3 will formalise this with hyperparameter tuning, cross-validation, and feature importance analysis (SHAP).

---

## **Project Structure**
```text
istanbul-rent-walkability-analysis/
├── data/
│   ├── istanbul_emlak_data.csv               # Raw scraped listings
│   ├── istanbul_emlak_final.csv              # P1 cleaned dataset
│   ├── istanbul_emlak_with_geo.csv           # P2 v2 geo-enriched dataset
│   ├── neighborhood_coordinates.csv          # 447 neighbourhood centroids
│   ├── neighborhood_features.csv             # OSMnx POI + metro features
│   └── istanbul_rail_stations.csv            # 220 rail stations (OSMnx)
├── p1/
│   ├── p1_eda_24018020.ipynb                 # P1: EDA notebook
│   └── p1_plots/                             # P1 visualizations
├── p2/
│   ├── p2_regression_24018020.ipynb          # P2: v1 + v2 combined notebook
│   └── p2_plots/                             # P2 visualizations (v1: original, v2: NEW_ prefix)
├── scripts/
│   ├── data_scraper.py                       # Sahibinden.com scraper
│   ├── 01_diagnose.py                        # Neighbourhood anomaly detection
│   ├── 02_clean_neighborhoods.py             # Parenthesis/slash cleanup
│   ├── 03_geocode_test.py                    # Geocoding v1 test (baseline)
│   ├── 03b_geocode_test_v2.py               # Geocoding v2 (bbox + type filter)
│   ├── 03c_geocode_test_v3.py               # Geocoding v3 (addressdetails validation)
│   ├── 04_geocode_full.py                    # Full 447-neighbourhood geocoding run
│   ├── 04b_analyze_fails.py                  # FAIL analysis (Silivri/Şile/Çatalca)
│   ├── 04c_fix_fails.py                      # Manual district-center fallback
│   ├── 05_build_metro_csv.py                 # OSMnx rail station extraction
│   ├── 06_pilot_features.py                  # 5-neighbourhood pipeline test
│   ├── 07_compute_all_features.py            # Full OSMnx + Haversine feature run
│   ├── 08_merge_and_validate.py              # Join geo features to listing CSV
│   ├── 08b_quick_rf_test.py                  # Random Forest preview (R² 0.665)
│   ├── 09_p2_extension_test.py               # v2 model benchmarks
│   ├── 10_diagnose_poly3.py                  # Polynomial deg 3 explosion diagnosis
├── .gitignore
└── README.md
```
## **Reproducing the Geographic Features**
The geo-enriched dataset (`istanbul_emlak_with_geo.csv`) is not tracked in the repository. 
To reproduce it, run the scripts in order: `04_geocode_full.py` → `05_build_metro_csv.py` → 
`07_compute_all_features.py` → `08_merge_and_validate.py`. Total runtime: ~100 minutes.

## **References & Acknowledgements**

* **Geospatial Data:** Urban amenities and street network features were extracted via OpenStreetMap using the [OSMnx](https://github.com/gboeing/osmnx) library:
  > Boeing, G. (2025). Modeling and Analyzing Urban Networks and Amenities with OSMnx. *Geographical Analysis*, 57(4), 567-577.

* **Transit Data:** Istanbul rail station coordinates (220 stations across metro, Marmaray, tram, funicular, and commuter lines) were sourced from [OpenStreetMap](https://www.openstreetmap.org) contributors via the OSMnx `features_from_polygon` API with `railway` tags.

* **Geocoding:** Neighborhood centroid coordinates were resolved using [Nominatim](https://nominatim.org), OpenStreetMap's open geocoding service, via the [GeoPy](https://geopy.readthedocs.io) library with a three-strategy validation pipeline (tight → medium → district-center fallback).

* **Distance Computation:** Haversine great-circle distances between neighbourhood centroids and rail stations were computed using the [math](https://docs.python.org/3/library/math.html) standard library.

* **Data Source:** Rental listings were scraped from [Sahibinden.com](https://www.sahibinden.com), Turkey's largest real estate classifieds platform, using [Selenium](https://www.selenium.dev) with [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver).

* **Machine Learning:** Regression models (Linear, Ridge, Lasso, Polynomial) were implemented using [scikit-learn](https://scikit-learn.org):
  > Pedregosa et al. (2011). Scikit-learn: Machine Learning in Python. *JMLR*, 12, 2825-2830.

* **Data Processing:** [pandas](https://pandas.pydata.org), [NumPy](https://numpy.org), [Matplotlib](https://matplotlib.org), [Seaborn](https://seaborn.pydata.org)
```