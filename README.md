# Online Retail Analytics & RFM Customer Segmentation Dashboard

An end-to-end retail analytics project built using **Python, Pandas, and Streamlit** to analyze online retail transactions, identify sales trends, evaluate product performance, and understand customer purchasing behavior through RFM (Recency, Frequency, Monetary) segmentation.

The project combines exploratory data analysis, data cleaning, customer analytics, and an interactive business dashboard to translate transaction data into actionable business insights.

## Project Overview

The objective is to help retail businesses understand:

- How revenue and order performance change over time.
- Which products, categories, and markets contribute most to revenue.
- How customers differ in purchasing behavior and value.
- Which customer segments require retention, engagement, or reactivation strategies.

## Dashboard Features

### 1. Business Overview

- Key performance indicators: Revenue, Customers, Orders, Average Order Value (AOV), and Return Rate.
- Monthly revenue, order volume, and AOV trends.
- Geographic analysis and top international markets.
- Top-performing products and category performance.
- Interactive period and market filters.

### 2. Customer RFM Analytics

- Customer segment distribution and segment-specific playbooks.
- Customer lookup by ID, segment filters, and random customer selection.
- Individual customer RFM scores and segment classification.
- Personalized customer recommendations and suggested actions.
- Customer location, purchase history, and financial summary.
- Top products, categories, and monthly spending patterns.

## Data Preparation & Analysis

The project uses the Online Retail transaction dataset.

The data preparation workflow includes:

- Data loading and quality assessment.
- Missing-value and duplicate handling.
- Identification of cancelled invoices and credit notes.
- Transaction cleaning and transformation.
- Revenue calculation and product categorization.
- Customer-level aggregation and RFM scoring.

## Key Analytical Results

The data pipeline includes validation checks against the following expected results:

| Metric | Result |
|---|---:|
| Cleaned transactions | 392,732 |
| Unique invoices | 18,536 |
| Unique customers | 4,339 |
| RFM-scored customers | 4,318 |
| Cleaned sales revenue | £8,887,208.89 |

## Technology Stack

- **Python** – Core programming and data processing
- **Pandas** – Data cleaning, transformation, and analysis
- **NumPy** – Numerical operations
- **Streamlit** – Interactive dashboard development
- **Plotly** – Interactive data visualizations
- **Jupyter Notebook** – Exploratory data analysis
- **Parquet** – Efficient storage of processed datasets
- **Git & GitHub** – Version control and project hosting

## Project Structure

```text
online-retail-analytics-with-rfm/
│
├── .streamlit/
│   └── config.toml
│
├── data/
│   ├── raw/
│   │   └── Online Retail.xlsx
│   ├── credit_notes.parquet
│   ├── rfm.parquet
│   └── transactions.parquet
│
├── notebooks/
│   └── retail_data_analysis.ipynb
│
├── views/
│   ├── overview.py
│   └── customers.py
│
├── app.py
├── core.py
├── build_data.py
├── test_app.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Installation & Usage

### 1. Clone the repository

```bash
git clone https://github.com/Abhinayreddy43/online-retail-analytics-with-rfm.git
cd online-retail-analytics-with-rfm
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the dashboard

```bash
streamlit run app.py
```

The dashboard will be available at:

`http://localhost:8501`

### 5. Rebuild processed datasets (optional)

Place the original Excel dataset at:

`data/raw/Online Retail.xlsx`

Then execute:

```bash
python build_data.py
```

The dashboard also attempts to generate missing processed datasets automatically when the source file is available.

### 6. Run regression tests

```bash
python test_app.py
```

## Notes

- Processed Parquet datasets are used by the dashboard to avoid repeating data preparation during normal application startup.
- The original Excel dataset should only be redistributed if its source licence permits it.
- The geographic map outlines require an internet connection to load from Plotly's CDN.

## Project Status

**Completed:** Interactive retail business overview and customer RFM analytics dashboard.

**Author:** Abhinay Reddy

**GitHub:** https://github.com/Abhinayreddy43
