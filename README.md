# **Istanbul Rental Market & Walkability Analysis** 

> **Project Link:** **[github.com/oykutugana/istanbul-rent-walkability-analysis](https://github.com/oykutugana/istanbul-rent-walkability-analysis)**

This project analyzes rental prices in Istanbul by combining traditional housing features with a custom-engineered Walkability Score and a Student Suitability Index. The goal is to identify the 'sweet spots' in the market—areas that optimize the trade-off between urban accessibility and rental affordability for students. Phase 2 builds on this clean dataset to predict rental prices using a series of regression models.

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
| **Location** | District (39) and Neighborhood (382) level granularity. |
| **Walkability Score** | Custom engineered feature (0-100). |
| **Student Score** | A weighted index (50% Walkability, 50% Per-Room Affordability) for optimal housing selection. |

#### **Data Cleaning & Refinement**
To ensure the model's reliability, we applied domain-based outlier filtering rather than purely statistical bounds:
* **Price Range:** 12,000 TL – 150,000 TL (removes typo entries below 12k and luxury outliers above 150k)
* **Area Range:** 30 m² – 250 m² (drops tiny micro-units and oversized commercial-style flats)
* **Total Rooms:** ≤ 6 (removes rare 7+1 and 8+ configurations that act as extreme leverage points in regression)

#### **Geospatial Integration**
We enriched the raw housing data by computing district-level urban accessibility indicators:
* **Transport:** Counts of Metro, Metrobüs, and Marmaray stations per district.
* **Education:** Number of major University Campuses per district.
* **Social Life:** Index of social amenities (cafes, libraries, parks) per district.

---

## **The Project Trilogy: Connecting the Dots**

| Phase | Focus | Key Deliverable |
|:---|:---|:---|
| **Phase 1: Problem & EDA** | **Data Cleaning & Engineering** | Problem formulation, outlier handling, walkability score, student suitability index, and visual EDA. |
| **Phase 2: Regression** | **Linear & Polynomial Models** | Feature engineering (log target, interaction terms, target encoding, one-hot), train/val/test split, Linear / Polynomial / Ridge / Lasso regression, and performance evaluation. |
| **Phase 3: Beyond Regression** | **Model Selection & Reporting** | Comparing advanced models (Random Forest / XGBoost), neighbourhood-level features, and final comprehensive report. |

## **Key Questions**

- How do structural features (size, rooms) vs. locational features (walkability) affect rental prices?
- To what extent does urban accessibility influence the "price premium" in central districts?
- Which features are the strongest predictors of rental price for a machine learning model?
- Where are the **"Student Sweet Spots"**—districts with high walkability but affordable per-room rents?
- How can we mathematically balance urban accessibility with budget constraints to find the most "student-friendly" neighborhoods?

---

## **Methods**

The analysis combines data cleaning, feature engineering, and statistical exploration to uncover key market dynamics.

### **1. Domain-Based Threshold Filtering**
Instead of purely statistical outlier removal, we applied real-world market limits to preserve high-value but legitimate listings (see Dataset section above for the exact bounds).

### **2. Feature Engineering (Walkability Index)**
A weighted composite score calculated based on proximity to essential amenities:

$$
Score = (Transport \times 0.5) + (University \times 0.3) + (Social\_Infrastructure \times 0.2)
$$

The walkability score is computed for all 39 districts in Istanbul.

### **3. Feature Engineering (Student Suitability Index)**
To support student housing decisions, we developed a composite index that balances accessibility with **per-room affordability**:

$$
SSI = (Walkability\_Score \times 0.5) + (Affordability\_Score \times 0.5)
$$

Where the Affordability Score is computed from `price_per_room = price / total_rooms`, then converted to a 0-100 scale via percentile rank inversion. This per-room formulation rewards larger shared apartments where the cost burden distributes across multiple tenants — a more realistic representation of student living conditions than absolute price.

### **4. Normalization**
All custom scores are scaled from **0 to 100** to ensure model consistency.

### **5. Correlation Analysis**
Utilizing Pearson Correlation and Binned Trend Analysis to identify relationships between accessibility and market value.

---

## **P1 Results**

- **The Power of Size:** Square footage (m²) is the strongest single predictor of price (r ≈ 0.50).
- **The Accessibility Premium:** Walkability shows a moderate positive correlation with price (r ≈ 0.32), with significant price spikes in highly walkable districts like **Beşiktaş**, **Kadıköy**, and **Şişli**.
- **The Old Center Paradox:** The walkability-vs-price relationship is non-monotonic. Prices climb with walkability up to the 70-80 range (~52k TL median), then drop sharply at the 80-100 range (~30k TL) where historical centers like Fatih dominate with older, smaller stock.
- **Student Score Trade-off:** A strong negative correlation between student score and price (r ≈ -0.54) confirms the mathematical consistency of the per-room methodology.
- **Top Student-Friendly Districts:** Under per-room affordability, **Fatih** leads decisively (85.97), followed by peripheral districts like **Avcılar (69.20), Bağcılar (67.32), Küçükçekmece (61.17)** that benefit from larger, affordable apartments.
- **District Prestige Premium:** **Kadıköy** holds the highest price-per-m² (~720 TL/m²) — Beşiktaş ranks only 13th. The "lifestyle premium" is tied to land value, not unit size.

---

## **P2 Results — Regression Modeling**

Building on the cleaned P1 dataset, we engineered four new features and evaluated five regression models:

#### **Feature Engineering**
1. **Log target transform** — reduced price skewness from 1.473 to 0.288
2. **Interaction term** — `area_m2 × walkability_score` to capture combined size-location effects
3. **Aggregation (target encoding)** — `district_median_price` computed only from the training set to avoid leakage
4. **One-hot encoding** — for `room_count` (1+1, 2+1, etc.)

#### **Model Comparison (60/20/20 train/val/test split)**

| Model | Train R² | Val R² | Test R² | Test RMSE | Test MAE |
|:---|:---:|:---:|:---:|:---:|:---:|
| Baseline (simple LR on area_m2) | 0.215 | 0.221 | 0.233 | 22,585 TL | 15,972 TL |
| Multiple LR | 0.470 | 0.493 | 0.462 | 18,924 TL | 13,050 TL |
| **Polynomial (degree 3)** | **0.510** | **0.510** | **0.464** | **18,880 TL** | **12,674 TL** |
| Ridge (α = 10) | 0.470 | 0.492 | 0.462 | 18,927 TL | 13,050 TL |
| Lasso (α = 0.001) | 0.470 | 0.492 | 0.462 | 18,913 TL | 13,041 TL |

#### **Key Findings**
- **Best model:** Polynomial regression of degree 3 (highest validation R²). However, degree 2 generalizes slightly better to the test set, suggesting mild overfitting at degree 3.
- **The model explains ~50% of price variance** using only physical, locational, and configuration features. The remaining variance comes from missing features (building age, floor, view, furnishing).
- **Lasso zeroed out 2 of 21 features** (`room_1.5+1`, `room_4+1`) — rare configurations with little independent signal.
- **Ridge and Lasso gave near-identical results to plain Multiple LR**, confirming that our features are not heavily collinear.
- **Predictions are useful for budget planning but not for exact pricing.** A typical absolute error of ~13k TL is large compared to the 36k TL median rent (~36%), so the model is informative rather than authoritative.
- **`student_score` and `price_per_room` were intentionally excluded** as features because both are derived from the target variable (`price`), which would cause severe target leakage.

#### **Implications for P3**
The ~0.50 R² ceiling reflects the limit of linear-style models on this feature set. Phase 3 will explore tree-based regressors (Random Forest, Gradient Boosting) which natively handle non-linear and non-monotonic patterns like the "Old Center Paradox", and incorporate finer-grained neighborhood-level features.

---

## **Project Structure**
```text
istanbul-rent-walkability-analysis/
├── data/                                   # Raw and processed CSV files
├── p1/                     
│   └── p1_eda_<24018020>.ipynb             # P1: EDA notebook
│   └── p1_plots/                           # P1 visualizations
├── p2/                     
│   └── p2_regression_<24018020>.ipynb      # P2: Regression notebook
│   └── p2_plots/                           # P1 visualizations
├── scripts/
│   └── data_scraper.py                     # Data scraping
├── .gitignore
└── README.md
```