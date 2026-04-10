# **Istanbul Rental Market & Walkability Analysis** 

**[github.com/oykutugana/istanbul-rent-walkability-analysis](https://github.com/oykutugana/istanbul-rent-walkability-analysis)**

**[Click here to view the Analysis Notebook (P1 EDA)](./notebooks/P1_EDA.ipynb)**

This project analyzes rental prices in Istanbul by combining traditional housing features with a custom-engineered Walkability Score and a Student Suitability Index. The goal is to identify the 'sweet spots' in the market—areas that optimize the trade-off between urban accessibility and rental affordability for students.

---

## **Overview**
Istanbul's rental market is highly dynamic and influenced by diverse factors. While size and room count are standard, **urban accessibility** is often undervalued in data models. This project introduces a **"Walkability Score"** to quantify how proximity to transport, universities, and social hubs affects market value. It serves as a comprehensive guide for students and young professionals seeking optimal living conditions.

---

## **Dataset**

The analysis is built upon a high-quality, refined dataset of rental listings across Istanbul's diverse districts.

**Primary Data Source:** The raw data consists of approximately **15,000 real estate listings** web-scraped from **Sahibinden.com**, Turkey’s premier classifieds platform. This ensures the study reflects real-time market dynamics.

#### **Data Composition**
| Feature | Description |
| :--- | :--- |
| **Price (TL)** | Monthly rental fee (Target Variable). |
| **Area (m²)** | Gross square meters of the property. |
| **Room Count** | Number of rooms and living areas (e.g., 2+1, 3+1). |
| **Location** | District and Neighborhood level granularity. |
| **Walkability Score** | Custom engineered feature (0-100). |
| Student Score | A weighted index (50% Walkability, 50% Affordability) for optimal housing selection. |

#### **Data Cleaning & Refinement**
To ensure the model's reliability, we focused on **realistic residential listings** by removing extreme outliers:  
* **Price Range:** 5,000 TL – 200,000 TL  
* **Area Range:** 30 m² – 500 m²  

#### **Geospatial Integration**
We enriched the raw housing data by calculating proximity to key urban interest points:
* **Transport:** Proximity to Metro, Metrobüs, and Marmaray stations.
* **Education:** Distance to major University Campuses.
* **Social Life:** Density of social amenities (cafes, libraries, parks).
---

## **The Project Trilogy: Connecting the Dots**

| Phase                     | Focus | Key Deliverable                                                                                          |
|:--------------------------| :--- |:---------------------------------------------------------------------------------------------------------|
| **Phase 1: Problem & EDA**          | **Data Cleaning & Engineering** | Problem formulation, handling outliers, and visualizing the Walkability Score trends.                    |
| **Phase 2: Regression**           | **Linear & Polynomial Models** | Implementing Linear and Polynomial Regression, feature engineering, and rigorous performance evaluation. |
| **Phase 3: Beyond Regression** | **Model Selection & Reporting** | Comparing advanced models (Random Forest/XGBoost), Model Selection, and final comprehensive report.      |

## **Key Questions**

- How do structural features (size, rooms) vs. locational features (walkability) affect rental prices?
- To what extent does urban accessibility influence the "price premium" in central districts?
- Which features are the strongest predictors of rental price for a machine learning model?
- Where are the **"Student Sweet Spots"**—districts with high walkability but affordable rents?
- How can we mathematically balance urban accessibility with budget constraints to find the most "student-friendly" neighborhoods?

---

## **Methods**

The analysis combines data cleaning, feature engineering, and statistical exploration to uncover key market dynamics.

### **1. Domain-Based Threshold Filtering**
Instead of purely statistical outlier removal, we applied real-world market limits to preserve high-value but legitimate listings.

### **2. Feature Engineering (Walkability Index)**
A weighted composite score calculated based on proximity to essential amenities:

$$
Score = (Transport \times 0.5) + (University \times 0.3) + (Social\_Infrastructure \times 0.2)
$$

### **3. Feature Engineering (Student Suitability Index)**
To support student housing decisions, we developed a composite index that balances accessibility with affordability:

$$
SSI=(Walkability_Score×0.5)+(Affordability_Score×0.5)
$$

Where Affordability Score is the inverse normalization of rental prices.

### **4. Normalization**
All custom scores are scaled from **0 to 100** to ensure model consistency.

### **5. Correlation Analysis**
Utilizing Pearson Correlation and Binned Trend Analysis to identify relationships between accessibility and market value.

---

## **Results**

- **The Power of Size:** Square footage ($m^2$) remains the strongest predictor of price ($r \approx 0.54$).  
- **The Accessibility Premium:** Walkability shows a moderate positive correlation ($r \approx 0.27$), with significant price spikes in highly walkable districts like **Beşiktaş** and **Kadıköy**.  
- **Market Segments:** Our "Sweet Spot" analysis identified **Üsküdar** and **Fatih** as high-value districts for students, offering superior walkability at lower-than-average costs.  
- **Data Integrity:** Successfully eliminated "Unknown" neighborhood noise and filled gaps in central district data (**Beyoğlu**, **Sarıyer**, **Ataşehir**).
- **Top Districts:** Beyond central prestige, districts like Esenyurt (for affordability) and Bayrampaşa/Zeytinburnu (for balance) emerged as the top recommendations in our suitability ranking.

---

## **Project Structure**
```text
istanbul-rent-analysis/
├── data/               # Raw and processed CSV files
├── notebooks/          # P1,P2,P3
├── plots/              # Visualizations, Heatmaps, and Trends
├── scripts/            # Data Scraping
├── .gitignore              
└── README.md