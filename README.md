**Istanbul Rental Market & Walkability Analysis** 

**[Click here to view the Analysis Notebook (P1 EDA)](./notebooks/P1_EDA.ipynb)**

This project analyzes rental prices in Istanbul by combining traditional housing features with a custom-engineered Walkability Score, capturing urban accessibility. The goal is to understand how location quality influences price and to support better housing decisions for students.

---

## **Overview**
Istanbul's rental market is highly dynamic and influenced by diverse factors. While size and room count are standard, **urban accessibility** is often undervalued in data models. This project introduces a **"Walkability Score"** to quantify how proximity to transport, universities, and social hubs affects market value. It serves as a comprehensive guide for students and young professionals seeking optimal living conditions.

---

## **Dataset**
The analysis is based on a refined dataset of rental listings in Istanbul.

- **Source:** Web-scraped real estate listings.  
- **Volume:** ~10,000 processed rows.  
- **Features:** Price (TL), Area ($m^2$), Room Count, District, Neighborhood, and the engineered **Walkability Score**.  
- **Refinement:** Focused on realistic residential listings:  
  - **Price Range:** 5,000 TL – 200,000 TL  
  - **Area Range:** 30 $m^2$ – 500 $m^2$

---

## **Key Questions**

- How do structural features (size, rooms) vs. locational features (walkability) affect rental prices?
- To what extent does urban accessibility influence the "price premium" in central districts?
- Which features are the strongest predictors of rental price for a machine learning model?
- Where are the **"Student Sweet Spots"**—districts with high walkability but affordable rents?

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

### **3. Normalization**
All custom scores are scaled from **0 to 100** to ensure model consistency.

### **4. Correlation Analysis**
Utilizing Pearson Correlation and Binned Trend Analysis to identify relationships between accessibility and market value.

---

## **Results**

- **The Power of Size:** Square footage ($m^2$) remains the strongest predictor of price ($r \approx 0.54$).  
- **The Accessibility Premium:** Walkability shows a moderate positive correlation ($r \approx 0.27$), with significant price spikes in highly walkable districts like **Beşiktaş** and **Kadıköy**.  
- **Market Segments:** Our "Sweet Spot" analysis identified **Üsküdar** and **Fatih** as high-value districts for students, offering superior walkability at lower-than-average costs.  
- **Data Integrity:** Successfully eliminated "Unknown" neighborhood noise and filled gaps in central district data (**Beyoğlu**, **Sarıyer**, **Ataşehir**).

---

## **Conclusion**

This project is structured into three phases:

### **P1: Exploratory Data Analysis (EDA) [CURRENT]**
- Focused on data cleaning, feature engineering, and market visualization.

### **P2: Machine Learning Model [UPCOMING]**
- Implementing Regression models (Linear, Random Forest, XGBoost) to predict prices based on the Walkability Index.

### **P3: Optimization & Deployment [FUTURE]**
- Model fine-tuning and developing a simple dashboard to help students find optimal housing based on their campus location.


---

## **Project Structure**
```text
istanbul-rent-analysis/
├── data/               # Raw and processed CSV files
├── notebooks/          # P1: EDA & P2: Machine Learning
├── plots/              # Visualizations, Heatmaps, and Trends
├── README.md           # Project documentation
└── .gitignore          # Files to be ignored by Git
