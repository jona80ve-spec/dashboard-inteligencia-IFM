# Insurance Intelligence Dashboard (IFM) 🚀

A production-ready data science web application built with Python and Streamlit. This project solves a core insurance challenge by transforming raw historical data into interactive predictive models and automated risk reports.

Live Demo: https://streamlit.app

---

## 📌 Business Case & Impact
* **Problem:** [Briefly describe the insurance issue, e.g., manual risk assessment or slow customer churn detection].
* **Solution:** Automated the statistical ingestion pipeline to predict [e.g., loss ratios / pricing / claim probabilities] in real-time.
* **Business Value:** Reduces decision-making time from days to seconds, allowing underwriters to explore simulated risk scenarios instantly.

---

## ⚙️ Data Engineering & Pipeline
1. **Data Ingestion:** Processed large-scale datasets containing [mention features like: demographic data, policy details, claims history].
2. **Data Cleaning:** Handled missing values, treated outliers via [e.g., IQR/Z-score], and fixed type mismatches.
3. **Feature Engineering:** 
   * Encoded categorical variables using [e.g., One-Hot Encoding / Target Encoding].
   * Normalized numerical features using [e.g., StandardScaler].
   * Created interaction terms for risk assessment scoring.

---

## 🤖 Modeling & Artificial Intelligence
* **Algorithm:** Powered by a customized Regression Model (e.g., [Multiple Linear / Logistic / Generalized Linear Model - GLM]) to capture the underlying risk factors mathematically.
* **Validation:** Evaluated using a K-Fold Cross-Validation approach to ensure stability and robust performance on unseen data.
* **Performance Metrics:** 
  * R-squared ($R^2$): `0.XX` (explaining XX% of the variance).
  * Mean Absolute Error (MAE): `X.XX`
  * Root Mean Squared Error (RMSE): `X.XX`
* **Interpretability:** Leveraged statistical coefficients and p-values to provide full transparency, allowing underwriters to see exactly how each feature impacts the final target prediction.
"Validated all classical statistical assumptions (homoscedasticity, normality of residuals, and VIF for multicollinearity) to guarantee model reliability."
---

## 🛠️ Tech Stack & Architecture
* **Language:** Python 3.10+
* **Data Processing:** Pandas, NumPy
* **Machine Learning:** Scikit-Learn, [XGBoost / LightGBM]
* **Frontend Dashboard:** Streamlit
* **Deployment & MLOps:** Streamlit Cloud (Continuous Deployment tied to GitHub main branch)

---

## 🚀 How to Run Locally

1. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd dashboard-inteligencia-IFM
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the Streamlit app:**
   ```bash
   streamlit run app.py
   ```
