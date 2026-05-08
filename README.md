# **Istanbul Rental Market & Walkability Analysis**

> **Project Link:** **[github.com/oykutugana/istanbul-rent-walkability-analysis](https://github.com/oykutugana/istanbul-rent-walkability-analysis)**

This project analyses rental prices in Istanbul by combining traditional housing features with a custom-engineered Walkability Score and a Student Suitability Index. The goal is to identify market sweet spots — neighbourhoods that optimise the trade-off between urban accessibility and rental affordability for students. Phase 2 builds regression models on the P1 dataset enriched with neighbourhood-level geographic features engineered from real-world map data.

---

## **Overview**

Istanbul's rental market is highly dynamic and influenced by diverse factors. Size and room count are standard predictors, but **urban accessibility** is often undervalued in data models. This project introduces a **Walkability Score** to quantify how proximity to transport, universities, and social hubs affects market value. It serves as a comprehensive guide for students and young professionals seeking optimal living conditions.

---

## **Dataset**

The analysis is built upon a refined dataset of rental listings across Istanbul's 38 districts.

**Primary Data Source:** The raw data consists of real estate listings web-scraped from **Sahibinden.com**, Turkey's leading classifieds platform. After domain-based outlier removal, the P1 cleaned dataset contains **15,272 listings**. After dropping the 293 listings whose neighbourhoods could not be geocoded reliably (Silivri, Şile, Çatalca — peripheral districts where Nominatim returns ambiguous results), the P2 modelling dataset contains **14,979 listings** across 36 districts and 698 unique neighbourhoods.

#### **Data Composition**

| Feature | Description |
| :--- | :--- |
| **Price (TL)** | Monthly rental fee (target variable) |
| **Area (m²)** | Gross square meters of the property |
| **Room Count** | Number of rooms and living areas (e.g., 2+1, 3+1, Stüdyo) |
| **Location** | District (38), sub-district (semt), and neighbourhood (mahalle) granularity |
| **Walkability Score** | Custom engineered feature (0–100), district-level (P1) |
| **Student Score** | Weighted index (50% Walkability, 50% Per-Room Affordability) for optimal housing selection |

#### **Data Cleaning & Refinement**

Domain-based outlier filtering was applied rather than purely statistical IQR rules:

* **Price range:** 10,000 TL – 150,000 TL (URL-filtered at scrape time; removes typo entries and luxury outliers)
* **Area range:** 30 m² – 250 m² (drops scraping artefacts and oversized commercial-style units)
* **Total rooms:** ≤ 6 (removes rare 7+1 and 8+ configurations that act as extreme leverage points in regression)
* **Text normalisation:** ASCII normalisation applied to district, sub-district, and neighborhood names (`ğ→g`, `ı→i`, `ş→s`, etc.)

#### **Geospatial Integration (P2)**

P2 replaces the district-level walkability proxy with neighbourhood-level features. An offline four-script pipeline geocodes each unique `(district, sub_district, neighborhood)` triple and computes radius-based feature counts:

* **Geocoding** — Nominatim with a three-tier fallback strategy (mahalle → semt → ilçe). Bounding-box validation rejects results outside Istanbul.
* **Transit access** — Haversine distance to the closest metro/Marmaray station, plus weighted station counts within 1 km using OpenStreetMap data fetched via the Overpass API.
* **POI density** — Counts of cafés, restaurants, university campuses, and parks within 1–2 km buffers.
* **Data-quality flags** — `is_periphery` (15+ km from city centre) and `is_district_center` (listings whose neighbourhood resolved only to district-level coordinates, ~4% of listings).

---

## **The Project Trilogy: Connecting the Dots**

| Phase | Focus | Key Deliverable |
|:---|:---|:---|
| **Phase 1: Problem & EDA** | **Data Cleaning & Engineering** | Problem formulation, outlier handling, walkability score, student suitability index, visual EDA across 38 districts. Final dataset: 15,272 listings × 10 columns. |
| **Phase 2: Regression** | **Linear & Polynomial Models** | Neighbourhood-level geographic feature engineering (Nominatim + Overpass), Auto-VIF filtering, baseline / multiple LR / polynomial / Ridge / Lasso. **Best model: Polynomial degree 3 plain LR with Test R² 0.635.** |
| **Phase 3: Beyond Regression** | **Model Selection & Reporting** | Tree-based models (Random Forest, Gradient Boosting), hyperparameter tuning, feature importance (SHAP), final comprehensive report. |

---

## **Key Questions**

* How do structural features (size, rooms) and locational features (walkability, metro distance) combine to determine rental prices?
* To what extent does urban accessibility drive the price premium in central districts?
* Which features are the strongest predictors of rental price for a regression model?
* Where are the **Student Sweet Spots** — districts with high walkability and affordable per-room rents?
* How can urban accessibility and budget constraints be balanced mathematically to identify the most student-friendly neighbourhoods?

---

## **Methods**

### **1. Domain-Based Threshold Filtering**

Domain-informed bounds preserve high-value but legitimate listings while removing structural noise (see Dataset section for exact thresholds).

### **2. Walkability Score (P1)**

A weighted composite score computed at the district level from publicly available aggregate counts:

$$\text{Walkability Score} = (\text{Transport} \times 0.5) + (\text{University} \times 0.3) + (\text{Social Infrastructure} \times 0.2)$$

The score is rescaled to 0–100 and applied uniformly to every listing within a district.

### **3. Student Suitability Index (P1)**

A composite index balancing accessibility with **per-room affordability**:

$$\text{Student Score} = (\text{Walkability} \times 0.5) + (\text{Affordability} \times 0.5)$$

Where `affordability = (1 − rank_pct(price_per_room)) × 100` and `price_per_room = price / effective_rooms`. The studio fix sets `effective_rooms = 1.5` for `Stüdyo (1+0)` listings to reflect realistic single-tenant economics — without this fix, studios would be unfairly penalised by `total_rooms = 1`.

### **4. Neighbourhood-Level Geographic Feature Engineering (P2)**

To address the within-district heterogeneity identified in P1 (e.g. Bebek vs. Dikilitaş in Beşiktaş sharing the same district score), a four-step offline pipeline replaces district-level signal with neighbourhood-level features:

1. **`01_extract_unique_locations.py`** — Extracts unique `(district, sub_district, neighborhood)` triples from the P1 dataset.
2. **`02_geocode_locations.py`** — Geocodes each location via Nominatim with a three-tier fallback (mahalle → semt → ilçe). Failed lookups outside Istanbul's bounding box are rejected. Includes resumable JSON cache for rate-limit interruptions.
3. **`03_fetch_pois.py`** — Fetches all Istanbul POIs (transit stations, restaurants, cafés, universities, parks) from the Overpass API as a one-time city-wide snapshot. Caches raw JSON for reproducibility.
4. **`04_compute_features.py`** — Computes radius-based counts and haversine distances around each centroid, then merges features with the P1 listings.

### **5. Auto-VIF Feature Filtering (P2)**

The geographic candidate pool contains overlapping signals (e.g., `metro_500m`, `metro_1km`, `weighted_1km` all measure transit-station density). Rather than hardcoding which features to drop, the model uses an iterative **Variance Inflation Factor (VIF)** filter that removes the highest-VIF feature until all remaining VIFs are below 10. In the current run, only `metro_1km` (VIF 46.7) was dropped; the remaining 9 geographic features form a well-conditioned design matrix.

### **6. Correlation and Residual Analysis**

Pearson correlation, binned trend analysis, and residual diagnostics (residuals vs. fitted, Q-Q plot, histogram) used throughout to identify model limitations and guide iterative improvement.

---

## **P1 Results — Exploratory Data Analysis**

* **Physical scale dominates as a single predictor.** `area_m2` correlates with `price` at **+0.565** — the strongest single linear predictor. `total_rooms` adds a secondary contribution (+0.428) but correlates with `area_m2` at +0.82, indicating multicollinearity that P2 addresses.
* **Walkability premium is real but moderate.** `walkability_score` correlates with `price` at **+0.330**. Rents climb steadily with walkability up to the 70–80 band (~60k TL median), then drop sharply at 80–100 (~36k TL) — Fatih's older, smaller housing stock pulls medians below the city-wide level despite top accessibility.
* **Student Score trade-off is by design.** The composite student_score correlates with price at **−0.513**, confirming that the percentile-rank affordability term successfully separates expensive-walkable districts from affordable-walkable ones.
* **Top student-friendly districts.** **Fatih leads decisively (76.48)** — a 17-point gap to second place. The remaining top 10 splits between premium-central districts (Şişli 59.05, Beyoğlu 51.55, Beşiktaş 49.08) where high walkability dominates and affordable peripheral districts (Pendik 54.95, Tuzla 51.25, Esenler 50.29, Esenyurt 47.46) where rent dominates.
* **District prestige premium.** **Zeytinburnu** holds the highest median price-per-m² (~695 TL/m²), narrowly ahead of Kadıköy (~680) and Bakırköy (~675). Beşiktaş — despite top-tier walkability — sits mid-pack on per-m² because its premium is unit-size driven rather than land-scarcity driven.

---

## **P2 Results — Regression Modeling**

P2 fits five models on the geo-enriched dataset (14,979 listings × 28 features) and compares them on a held-out test set. Feature set: 3 P1 numeric + 9 geographic (Auto-VIF filtered) + 16 room dummies.

| Model | Train R² | Val R² | Test R² | Test RMSE | Test MAE |
|:---|:---:|:---:|:---:|---:|---:|
| Baseline (area_m2 only) | 0.290 | 0.314 | 0.305 | 21,568 TL | 15,109 TL |
| Multiple LR | 0.522 | 0.550 | 0.535 | 17,637 TL | 12,142 TL |
| **Polynomial (degree 3, plain LR)** | **0.651** | **0.654** | **0.635** | **15,618 TL** | **10,802 TL** |
| Ridge (α = 10) | 0.522 | 0.549 | 0.535 | 17,635 TL | 12,141 TL |
| Lasso (α = 0.0001) | 0.522 | 0.549 | 0.535 | 17,633 TL | 12,141 TL |

**Best model:** Polynomial degree 3 (plain Linear Regression). Test R² **0.635**, RMSE **15,618 TL**, MAE **10,802 TL** on a median rent of 39,000 TL.

### **Key Findings**

* **Polynomial expansion delivers genuine signal.** Multiple LR (degree 1) reaches Test R² 0.535. Polynomial degree 3 reaches **0.635** — a +0.10 absolute gain (+19% relative) from the same algorithm with quadratic and cubic interaction terms. The improvement reflects real interactions like "metro proximity matters more in dense restaurant areas" that a linear sum of features cannot represent.

* **Auto-VIF cleanup keeps degree 3 from overfitting.** With 470 features at degree 3, overfitting is the natural concern. Three things prevent it: the Auto-VIF filter removed redundant base features upstream, the log transform on the target homogenises variance across price levels, and the 8,987-row training set provides ~19 observations per feature — comfortably above the rule-of-thumb minimum.

* **Regularisation is not needed on this dataset.** Ridge and Lasso land within 0.001 of plain MLR on test R² in the linear setting, and Ridge is *worse* than plain OLS at polynomial degree 3 (Test R² 0.611 vs 0.635). The Auto-VIF filter and explicit `total_rooms` removal eliminated the multicollinearity issues that L1/L2 penalties typically address.

* **Lasso zeroes no features.** With cross-validated `alpha = 0.0001`, Lasso retains all 28 features — the design matrix is well-conditioned enough that no L1 penalty is beneficial.

* **Predictions remain approximate.** A ~10,800 TL average absolute error against a 39,000 TL median rent is useful for budget planning and ranking neighbourhoods, but not for exact pricing. Listing-level attributes the dataset cannot see (building age, floor, view, balcony, furnished status) likely account for most of the remaining unexplained variance.

* **`student_score` and `price_per_room` excluded.** Both are derived from the target variable; including them would inflate validation R² toward 1.0 by leaking the target.

### **Implications for P3**

The Test R² 0.635 ceiling suggests the linear family has not fully exhausted its capacity, but each additional polynomial degree triples the feature count, making further gains in this family expensive. P3 will move to tree-based models (Random Forest, then Gradient Boosted Trees) which capture non-linear and high-order interactions natively without polynomial expansion or regularisation tuning. The realistic target for P3 is **Test R² in the 0.70–0.75 range**.

---

## **Project Structure**

```text
istanbul-rent-walkability-analysis/
├── data/
│   ├── istanbul_emlak_data.csv               # Raw scraped listings
│   ├── istanbul_emlak_final.csv              # P1 cleaned dataset (15,272 rows)
│   ├── unique_locations.csv                  # Unique (district, sub_district, neighborhood)
│   ├── geocoded_locations.csv                # Nominatim geocoded centroids
│   ├── geocode_cache.json                    # Resumable Nominatim cache
│   ├── poi_raw/                              # Raw Overpass API JSON snapshots
│   │   ├── raw_transit.json
│   │   ├── raw_restaurants.json
│   │   ├── raw_cafes.json
│   │   ├── raw_universities.json
│   │   └── raw_parks.json
│   └── istanbul_emlak_with_geo.csv           # P2 modelling dataset (15,272 × 22)
├── p1/
│   ├── p1_eda_24018020.ipynb                 # P1: EDA notebook
│   └── p1_plots/                             # P1 visualisations
├── p2/
│   ├── p2_regression_24018020.ipynb          # P2: regression notebook
│   └── p2_plots/                             # P2 visualisations
├── geocoding/
│   ├── 01_extract_unique_locations.py
│   ├── 02_geocode_locations.py
│   ├── 03_fetch_pois.py
│   ├── 04_compute_features.py
│   └── geocoding_pipeline.md                 # Pipeline run instructions
├── scripts/
│   └── data_scraper.py                       # Sahibinden.com scraper
├── .gitignore
└── README.md
```

---

## **Reproducing the Geographic Features**

The geo-enriched dataset (`istanbul_emlak_with_geo.csv`) is not tracked in the repository. To reproduce it, run the scripts in `geocoding/` in order:

```bash
cd geocoding/
python 01_extract_unique_locations.py    # < 1 sec
python 02_geocode_locations.py           # ~10–15 min (Nominatim 1 req/sec)
python 03_fetch_pois.py                  # ~2–5 min (5 city-wide Overpass queries)
python 04_compute_features.py            # ~1–2 min (local computation)
```

Both `02` and `03` cache results — interrupted runs resume from where they left off without re-querying.

---

## **References & Acknowledgements**

* **Geospatial Data:** Urban amenities and transit data extracted from **OpenStreetMap** via the [Overpass API](https://overpass-api.de/).

* **Geocoding:** Neighbourhood centroid coordinates resolved using [Nominatim](https://nominatim.org), OpenStreetMap's open geocoding service, with a custom three-tier fallback validation pipeline.

* **Distance Computation:** Haversine great-circle distances between neighbourhood centroids and POIs computed via vectorised NumPy.

* **Data Source:** Rental listings scraped from [Sahibinden.com](https://www.sahibinden.com), Turkey's largest real estate classifieds platform, using [Selenium](https://www.selenium.dev) with [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver).

* **Machine Learning:** Regression models (Linear, Ridge, Lasso, Polynomial) implemented using [scikit-learn](https://scikit-learn.org):
  > Pedregosa et al. (2011). Scikit-learn: Machine Learning in Python. *JMLR*, 12, 2825–2830.

* **VIF Computation:** [statsmodels](https://www.statsmodels.org) `variance_inflation_factor` for the Auto-VIF feature filter.

* **Data Processing:** [pandas](https://pandas.pydata.org), [NumPy](https://numpy.org), [Matplotlib](https://matplotlib.org), [Seaborn](https://seaborn.pydata.org), [SciPy](https://scipy.org) (for Q-Q plots and statistical functions).
