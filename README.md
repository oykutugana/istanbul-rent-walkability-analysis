# **Istanbul Rental Market & Walkability Analysis**

> **Project Link:** **[github.com/oykutugana/istanbul-rent-walkability-analysis](https://github.com/oykutugana/istanbul-rent-walkability-analysis)**

This project analyses rental prices in Istanbul by combining traditional housing features with a custom-engineered Walkability Score and a Student Suitability Index. The goal is to identify market sweet spots — neighborhoods that optimize the trade-off between urban accessibility and rental affordability for students. Phase 1 establishes the cleaned dataset and exploratory findings. Phase 2 builds regression models on a feature set enriched with neighborhood-level geographic data. Phase 3 reframes the price-prediction problem as a binary classification task (Premium vs Affordable) and compares six base classifiers plus a Stacking meta-ensemble.

---

## **Overview**

Istanbul's rental market is highly dynamic and influenced by diverse factors. Size and room count are standard predictors, but **urban accessibility** is often undervalued in data models. This project introduces a **Walkability Score** to quantify how proximity to transport, universities, and social hubs affects market value. It serves as a comprehensive guide for students and young professionals seeking optimal living conditions.

---

## **Dataset**

The analysis is built upon a refined dataset of rental listings across Istanbul's 38 districts.

**Primary Data Source:** The raw data consists of real estate listings web-scraped from **Sahibinden.com**, Turkey's leading classifieds platform. After domain-based outlier removal, the P1 cleaned dataset contains **15,272 listings** across **38 districts and 727 unique (district, neighborhood) pairs**. After dropping the 293 listings whose neighborhoods could not be geocoded reliably (Silivri, Şile, Çatalca — peripheral districts where Nominatim returns ambiguous results), the P2 and P3 modelling dataset contains **14,979 listings** across **36 districts and 698 unique (district, neighborhood) pairs**.

#### **Data Composition**

| Feature | Description                                                                                |
| :--- |:-------------------------------------------------------------------------------------------|
| **Price (TL)** | Monthly rental fee (regression target / source of P3 classification target)                |
| **Area (m²)** | Gross square meters of the property                                                        |
| **Room Count** | Number of rooms and living areas (e.g., 2+1, 3+1, Stüdyo)                                  |
| **Location** | District (38), sub-district (semt), and neighborhood (mahalle) granularity                 |
| **Walkability Score** | Custom engineered feature (0–100), district-level (P1)                                     |
| **Student Score** | Weighted index (50% Walkability, 50% Per-Room Affordability) for optimal housing selection |
| **`affordable` (P3)** | Binary label: 1 if price ≤ median (39,999 TL), 0 otherwise                                 |

#### **Data Cleaning & Refinement**

Domain-based outlier filtering was applied rather than purely statistical IQR rules:

* **Price range:** 10,000 TL – 150,000 TL (URL-filtered at scrape time; removes typo entries and luxury outliers)
* **Area range:** 30 m² – 250 m² (drops scraping artefacts and oversized commercial-style units)
* **Total rooms:** ≤ 6 (removes rare 7+1 and 8+ configurations that act as extreme leverage points in regression)
* **Text normalisation:** ASCII normalisation applied to district, sub-district, and neighborhood names (`ğ→g`, `ı→i`, `ş→s`, etc.)

#### **Geospatial Integration (P2)**

P2 replaces the district-level walkability proxy with neighborhood-level features. An offline four-script pipeline geocodes each unique `(district, sub_district, neighborhood)` triple and computes radius-based feature counts:

* **Geocoding** — Nominatim with a three-tier fallback strategy (mahalle → semt → ilçe). Bounding-box validation rejects results outside Istanbul.
* **Transit access** — Haversine distance to the closest metro/Marmaray station, plus weighted station counts within 1 km using OpenStreetMap data fetched via the Overpass API.
* **POI density** — Counts of cafés, restaurants, university campuses, and parks within 1–2 km buffers.
* **Data-quality flags** — `is_periphery` (15+ km from city centre) and `is_district_center` (listings whose neighborhood resolved only to district-level coordinates, ~4% of listings).

---

## **The Project Trilogy: Connecting the Dots**

| Phase | Focus | Key Deliverable                                                                                                                                                                                                                                                                                                                                      |
|:---|:---|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Phase 1: Problem & EDA** | **Data Cleaning & Engineering** | Problem formulation, outlier handling, walkability score, student suitability index, visual EDA across 38 districts. Final dataset: 15,272 listings × 10 columns.                                                                                                                                                                                    |
| **Phase 2: Regression** | **Linear & Polynomial Models** | Neighborhood-level geographic feature engineering (Nominatim + Overpass), Auto-VIF filtering, baseline / multiple LR / polynomial / Ridge / Lasso. **Best model: Polynomial degree 3 plain LR with Test R² 0.635.**                                                                                                                                  |
| **Phase 3: Classification & Beyond** | **Affordability Prediction** | Unsupervised analysis (PCA, K-Means, Agglomerative + geo-only refinement), seven supervised models (Naive Bayes, Logistic Regression, KNN, Decision Tree, Random Forest, Gradient Boosting, Stacking Classifier), 5-fold GridSearchCV tuning, error analysis. **Best model: Stacking Classifier with Val F1-macro 0.8214, Test F1-macro 0.8010, and Test AUC-ROC 0.8891.** |
---

## **Key Questions**

* How do structural features (size, rooms) and locational features (walkability, metro distance) combine to determine rental prices?
* To what extent does urban accessibility drive the price premium in central districts?
* Which features are the strongest predictors of rental price for a regression model?
* Where are the **Student Sweet Spots** — districts with high walkability and affordable per-room rents?
* How can urban accessibility and budget constraints be balanced mathematically to identify the most student-friendly neighborhoods?
* Can a classifier reliably separate Affordable from Premium listings, and where do its errors concentrate?

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

### **4. Neighborhood-Level Geographic Feature Engineering (P2)**

To address the within-district heterogeneity identified in P1 (e.g. Bebek vs. Dikilitaş in Beşiktaş sharing the same district score), a four-step offline pipeline replaces district-level signal with neighborhood-level features:

1. **`01_extract_unique_locations.py`** — Extracts unique `(district, sub_district, neighborhood)` triples from the P1 dataset.
2. **`02_geocode_locations.py`** — Geocodes each location via Nominatim with a three-tier fallback (mahalle → semt → ilçe). Failed lookups outside Istanbul's bounding box are rejected. Includes resumable JSON cache for rate-limit interruptions.
3. **`03_fetch_pois.py`** — Fetches all Istanbul POIs (transit stations, restaurants, cafés, universities, parks) from the Overpass API as a one-time city-wide snapshot. Caches raw JSON for reproducibility.
4. **`04_compute_features.py`** — Computes radius-based counts and haversine distances around each centroid, then merges features with the P1 listings.

### **5. Auto-VIF Feature Filtering (P2)**

The geographic candidate pool contains overlapping signals (e.g., `metro_500m`, `metro_1km`, `weighted_1km` all measure transit-station density). Rather than hardcoding which features to drop, the model uses an iterative **Variance Inflation Factor (VIF)** filter that removes the highest-VIF feature until all remaining VIFs are below 10. In the current run, only `metro_1km` (VIF 46.7) was dropped; the remaining 9 geographic features form a well-conditioned design matrix.

### **6. Unsupervised Analysis & Cluster Refinement (P3)**

P3 applies PCA and two clustering algorithms (K-Means and Agglomerative with Ward linkage) on the 28-feature training matrix. An iterative refinement step found that the 16 room-dummy columns dominated the L2 distance metric, so the clustering was rerun on the **9 geographic features only**. The geo-only clustering tripled the silhouette score (from 0.121 to 0.375) and halved the Davies-Bouldin index. The resulting cluster label was added to the feature set and tested across LR, RF, and GB — no model gained more than 0.001 F1-macro, so the label was not retained in the final feature set.

### **7. Stacking Meta-Ensemble (P3)**

A Stacking Classifier combines three tuned base learners (Random Forest, Gradient Boosting, K-Nearest Neighbors) through a Logistic Regression meta-learner with 5-fold out-of-fold predictions. The meta-learner reads only the base learners' predicted probabilities (`passthrough=False`) rather than the raw 28 features.

### **8. Correlation, Residual, and Error Analysis**

Pearson correlation, binned trend analysis, regression residual diagnostics (residuals vs. fitted, Q-Q plot, histogram), and classification error analysis (proximity to threshold, per-class confusion, feature importance) are used throughout the three phases to identify model limitations and guide iterative improvement.

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

**Best model:** Polynomial degree 3 (plain Linear Regression). Test R² **0.635**, RMSE **15,618 TL**, MAE **10,802 TL** on a median rent of **39,999 TL**.

### **Key Findings**

* **Polynomial expansion delivers genuine signal.** Multiple LR (degree 1) reaches Test R² 0.535. Polynomial degree 3 reaches **0.635** — a +0.10 absolute gain (+19% relative) from the same algorithm with quadratic and cubic interaction terms.
* **Auto-VIF cleanup keeps degree 3 from overfitting.** The Auto-VIF filter removed redundant base features upstream, the log transform on the target homogenises variance, and the 8,987-row training set provides ~19 observations per feature.
* **Regularisation is not needed on this dataset.** Ridge and Lasso land within 0.001 of plain MLR; Ridge is *worse* than plain OLS at polynomial degree 3 (Test R² 0.611 vs 0.635). Lasso zeroes no features at its cross-validated `alpha = 0.0001`.
* **Predictions remain approximate.** A ~10,800 TL average absolute error against a 39,999 TL median rent is useful for budget planning, but not for exact pricing. Listing-level attributes the dataset cannot see (building age, floor, view, balcony, furnished status) likely account for most of the remaining unexplained variance.
* **`student_score` and `price_per_room` excluded.** Both are derived from the target variable and would cause leakage.

### **Implications for P3**

The Test R² 0.635 ceiling and a ~10,800 TL average error suggest the linear family has nearly exhausted its capacity on the available features. P3 reframes the task as **binary classification** at the median price, which (i) shifts the evaluation onto a discrete, calibrated metric (F1-macro), (ii) allows ensemble methods to be compared on AUC-ROC, and (iii) produces an output (Premium vs Affordable) that directly answers the project's affordability question for students.

---

## **P3 Results — Classification**

P3 reframes the price-prediction task as binary classification. The continuous rental price is binarised at the median (39,999 TL):

* **Class 1 (Affordable):** `price ≤ 39,999 TL` — 7,491 listings (50.01%)
* **Class 0 (Premium):** `price > 39,999 TL` — 7,488 listings (49.99%)

The same 14,979 listings, same 28 features, and same 60/20/20 train/val/test split from P2 are reused without re-splitting.

### **Test-set comparison across all seven models**

| Model                       | Val F1-macro | Test Accuracy | Test F1-macro | Test AUC-ROC |
|:----------------------------|:---:|:---:|:---:|:---:|
| Naive Bayes (Gaussian)      | 0.6258 | 0.6615 | 0.6315 | 0.8086 |
| Logistic Regression (tuned) | 0.7690 | 0.7647 | 0.7642 | 0.8533 |
| K-Nearest Neighbors (tuned) | 0.7974 | 0.7787 | 0.7786 | 0.8627 |
| Decision Tree (tuned)       | 0.7914 | 0.7737 | 0.7737 | 0.8606 |
| Random Forest (tuned)       | 0.8208 | 0.8024 | 0.8024 | 0.8875 |
| Gradient Boosting (tuned)   | 0.8110 | 0.8004 | 0.8003 | 0.8869 |
| **Stacking Classifier**     | **0.8214** | **0.8011** | **0.8010** | **0.8891** |

**Best model:** **Stacking Classifier** with Random Forest + Gradient Boosting + K-Nearest Neighbors as base learners and Logistic Regression as the meta-learner. Val F1-macro **0.8214** (highest), Test Accuracy **0.8011**, Test F1-macro **0.8010**, Test AUC-ROC **0.8891** (highest). Random Forest finished within 0.0014 of Stacking on Test F1-macro (within sampling noise); Stacking was selected on the strength of its Val F1-macro and Test AUC-ROC leads.

### **Key Findings**

* **Top three models are statistically tied on the test set.** Random Forest, Stacking, and Gradient Boosting reached Test F1-macro of 0.8024, 0.8010, and 0.8003 respectively — a spread of 0.0021, well within sampling noise on a 2,996-row test set. All three lost a small amount from validation to test (−0.018 to −0.020 F1), indicating a slightly easier validation split rather than overfitting to test. Stacking was selected as the final model because it leads on Validation F1-macro (0.8214, the GridSearchCV scoring metric) and on Test AUC-ROC (0.8891, the threshold-independent ranking metric).

* **Same top features as P1 and P2.** The Random Forest base learner inside the Stacking Classifier ranks three features at the top: `area_m2` (31.8% importance), `dist_med_price` (17.3%), `walkability_score` (10.0%). These three explain ~59% of the model's behaviour. The ranking is identical to the regression coefficient ranking from P2 — the dataset's predictive structure does not depend on the choice of model family or learning objective.

* **Errors concentrate near the decision threshold.** Listings within 5,000 TL of the median produce a **42.3%** error rate. Listings 40,000 TL+ away from the median produce a **0.0%** error rate (every one of the 326 such listings classified correctly). The 596 total errors (308 false Affordable, 288 false Premium) cluster sharply in the grey zone where features sit near their global averages and cannot push borderline listings confidently to either side.

* **Cluster-as-feature did not help.** PCA and clustering (K-Means + Agglomerative with Ward linkage) revealed structure, but the cluster label did not improve any of LR, RF, or GB by more than 0.001 F1 in either direction. A geo-only refinement of the clustering tripled the silhouette score (0.121 → 0.375), but the information was already present in the raw features the classifier sees.

* **Meta-learner draws on genuine base-learner diversity.** The Stacking Classifier's Logistic Regression meta-learner weights Random Forest at **53%**, Gradient Boosting at **34%**, and K-Nearest Neighbors at **13%**. KNN's non-parametric local-geometry view contributes a non-trivial fraction of the final signal, which is what gives Stacking its Test AUC-ROC lead over the tree-only ensembles.

* **Naive Bayes is a clear "weakest tool" baseline.** GaussianNB reaches only 0.6315 Test F1-macro because the independence assumption is severely violated by the correlated geographic features and the redundant room dummies. The 13-percentage-point gap from the next model confirms that feature independence is the wrong assumption for this dataset.

### **Implications**

The F1 ≈ 0.80 ceiling reached by all tree-based and meta-ensemble methods reflects an irreducible-error floor in the current feature set, not a limitation of the model family. The error analysis localises this floor to the immediate vicinity of the price threshold, where 42% of borderline listings are misclassified — the features needed to break this tie (building age, floor, view, balcony, furnished status) are not present in the dataset. The near-tie on Test F1-macro between Stacking and Random Forest (Δ = 0.0014) illustrates the importance of evaluating models on multiple criteria: a single-metric comparison would have produced an arbitrary winner, while the Validation F1 + Test AUC-ROC combination provides a more stable basis for the final selection.

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
│   └── istanbul_emlak_with_geo.csv           # P2/P3 modelling dataset 
├── p1/
│   ├── p1_eda_24018020.ipynb                 # P1: EDA notebook
│   └── p1_plots/                             # P1 visualisations
├── p2/
│   ├── p2_regression_24018020.ipynb          # P2: regression notebook
│   └── p2_plots/                             # P2 visualisations
├── p3/
│   ├── p3_classification_24018020.ipynb      # P3: classification notebook
│   └── p3_plots/                             # P3 visualisations
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

## **Reproducing the Project**

### Geographic Features (P2 / P3 input)

The geo-enriched dataset (`istanbul_emlak_with_geo.csv`) is not tracked in the repository. To reproduce it, run the scripts in `geocoding/` in order:

```bash
cd geocoding/
python 01_extract_unique_locations.py    # < 1 sec
python 02_geocode_locations.py           # ~10–15 min (Nominatim 1 req/sec)
python 03_fetch_pois.py                  # ~2–5 min (5 city-wide Overpass queries)
python 04_compute_features.py            # ~1–2 min (local computation)
```

Both `02` and `03` cache results — interrupted runs resume from where they left off without re-querying.

### Running the Notebooks

The three notebooks must be run in order (P1 → P2 → P3) because each consumes the previous phase's output:

```bash
jupyter notebook p1/p1_eda_24018020.ipynb              # produces istanbul_emlak_final.csv
# then run the geocoding pipeline above
jupyter notebook p2/p2_regression_24018020.ipynb       # reads istanbul_emlak_with_geo.csv
jupyter notebook p3/p3_classification_24018020.ipynb   # reads istanbul_emlak_with_geo.csv
```

P3 reuses the P2 train/val/test split via `np.random.seed(42)` and a deterministic shuffle of row indices.

---

## **References & Acknowledgements**

* **Geospatial Data:** Urban amenities and transit data extracted from **OpenStreetMap** via the [Overpass API](https://overpass-api.de/).

* **Geocoding:** Neighborhood centroid coordinates resolved using [Nominatim](https://nominatim.org), OpenStreetMap's open geocoding service, with a custom three-tier fallback validation pipeline.

* **Distance Computation:** Haversine great-circle distances between neighborhood centroids and POIs computed via vectorised NumPy.

* **Data Source:** Rental listings scraped from [Sahibinden.com](https://www.sahibinden.com), Turkey's largest real estate classifieds platform, using [Selenium](https://www.selenium.dev) with [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver).

* **Machine Learning:** Regression and classification models (Linear, Ridge, Lasso, Polynomial, Logistic Regression, KNN, Decision Tree, Random Forest, Gradient Boosting, Stacking Classifier, GaussianNB) implemented using [scikit-learn](https://scikit-learn.org):
  > Pedregosa et al. (2011). Scikit-learn: Machine Learning in Python. *JMLR*, 12, 2825–2830.

* **VIF Computation:** [statsmodels](https://www.statsmodels.org) `variance_inflation_factor` for the Auto-VIF feature filter.

* **Data Processing:** [pandas](https://pandas.pydata.org), [NumPy](https://numpy.org), [Matplotlib](https://matplotlib.org), [Seaborn](https://seaborn.pydata.org), [SciPy](https://scipy.org) (for Q-Q plots and statistical functions).
