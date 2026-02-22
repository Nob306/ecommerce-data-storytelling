# E-Commerce Analytics Intelligence System

An automated system that monitors business metrics, detects unusual patterns, and helps explain what's driving changes in the data.

## Project Overview

This project analyses real UK retail transaction data to automatically:
- Calculate and track 16 business metrics (revenue, orders, customer behaviour, etc.)
- Detect when metrics behave unusually using statistical methods
- Figure out which customer segments or products are driving changes
- Provide actionable explanations instead of just numbers

**Why I built this:** I wanted to go beyond basic data analysis notebooks and build something that could actually run in production. Most analytics work involves repetitive calculations and manual investigation, this automates that process. Plus, I was curious about how companies like Amplitude or Mixpanel structure their metric systems under the hood.

## Current Status

**Phase:** Core Analytics Engine (Weeks 1-5)  
**Progress:** Week 3 Complete  
**Next Up:** Statistical anomaly detection (Week 4)

### Completed:
- **Week 1:** Project architecture and KPI specifications
- **Week 2:** Data ingestion and validation pipeline
  - Successfully loaded 541,909 transactions
  - Implemented 14 automated quality checks
  - Achieved 71.4% data quality score (10/14 checks passed)
  - Identified and documented 4 data anomalies
- **Week 3:** KPI computation engine
  - Built config-driven formula parser that reads metric definitions from YAML
  - Implemented support for simple aggregations, cross-KPI dependencies, conditional filtering, and complex multi-step calculations
  - All 16 KPIs calculating correctly across Finance, Operations, Growth, Product, and International categories
  - Results saved with timestamps to `data/processed/kpi_results.csv`

### Currently Building:
- Statistical anomaly detection (Week 4)
- Root cause analysis (Week 5)

### Future Ideas (might add later):
- AI-generated narrative summaries
- Interactive dashboard
- Automated scheduling

Note: I'm prioritising getting the core analytics engine working well before adding fancy features. Better to have 5 solid features than 8 half-baked ones.

---

## KPI Results (on 541,909 UK retail transactions)

| Metric | Value |
|---|---|
| Total Revenue | £9,747,747.93 |
| Revenue per Order | £376.36 |
| Revenue per Customer | £2,229.59 |
| Order Count | 25,900 |
| Items per Order | 200 |
| Units Sold | 5,176,450 |
| Active Customers | 4,372 |
| Repeat Customer Rate | ~83% |
| New Customers | 4,372 |
| Product Revenue Concentration | ~47% from top 20 products |
| Avg Unit Price | £1.88 |
| Product Return Rate | ~20% |
| International Revenue Share | ~16% |
| Weekend Revenue Share | ~8% |
| Peak Hour Concentration | ~35% |

---

## Data Quality Findings

Initial data quality assessment revealed some interesting characteristics:

**Overall Score: 71.4% (10/14 checks passed)**

**Passing Checks:**
- Schema validation: All columns present with correct types
- Completeness: CustomerID 24.9% missing (acceptable — represents guest checkouts)
- Completeness: Description 0.3% missing (well within threshold)
- Cancellations properly marked with negative quantities

**Known Issues (Documented, Not Fixed):**
- 2 transactions with negative unit prices (0.0004% of data)
- 2 transactions exceeding £100K threshold (0.0004% of data)

**Decision:** Proceeding with these anomalies documented rather than cleaned. In a real-world scenario, these would be flagged for business review — they could be legitimate bulk orders or data entry errors requiring domain expertise to resolve. This demonstrates that the validation system works as intended: it catches edge cases for human review rather than silently accepting everything.

---

## How It Works

The system has 5 layers that work together:

```
Data Layer (Week 2) 
  ↓ Loads and validates CSV data
  
KPI Layer (Week 3) completed
  ↓ Calculates metrics from config files
  
Detection Layer (Week 4) 
  ↓ Finds anomalies and trends statistically
  
Analysis Layer (Week 5) 
  ↓ Figures out why metrics changed
  
Output Layer (Future) 
  ↓ Presents findings to users
```

**Design decision:** Metrics are defined in YAML config files rather than hardcoded in Python. This means business logic (thresholds, formulas, owners) can be changed without touching the codebase — which is how real analytics platforms like dbt structure metric definitions.

**How the formula parser works:** The KPI engine reads formula strings from `config/kpis.yaml` and executes them dynamically. It supports:
- Simple aggregations: `sum(Quantity * UnitPrice)`
- Cross-KPI references: `total_revenue / order_count` (uses previously calculated KPIs)
- Conditional filtering: `sum(revenue where Country != 'United Kingdom')`
- Complex multi-step calculations: top-N product/hour revenue aggregations
- Customer groupby conditions: `count(distinct CustomerID with orders > 1)`

---

## Project Structure

```
ecommerce-data-storytelling/
├── config/
│   ├── kpis.yaml                  # 16 metric definitions (formula, owner, thresholds)
│   └── data_contracts.yaml        # Data validation rules and schema
├── src/
│   ├── data/
│   │   ├── ingestion.py          
│   │   └── validation.py         
│   ├── kpis/
│   │   ├── formulas.py           
│   │   ├── registry.py           
│   │   └── engine.py             
│   ├── insights/                  
│   ├── narratives/                
│   └── platform/                  
├── data/
│   ├── raw/
│   │   └── UK retail data.csv    541,909 rows
│   └── processed/
│       └── kpi_results.csv       
└── README.md
```

---

## Running the Code

**Important:** All modules should be run from the project root directory using Python's module syntax (`-m` flag). This ensures proper import resolution and path handling.

### Setup

```bash
# Navigate to project root
cd path/to/ecommerce-data-storytelling

# Activate virtual environment
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux

# Install dependencies (first time only)
pip install -r requirements.txt
```

### Running the Pipeline

```bash
# 1. Load and summarise data
python -m src.data.ingestion

# 2. Validate data quality
python -m src.data.validation

# 3. Calculate all 16 KPIs
python -m src.kpis.engine
```

**Note:** Do not run scripts directly (e.g., `python src/data/ingestion.py`) as this causes import and path resolution errors. Always use the `-m` flag.

### Expected Output

**Ingestion:**
```
INFO: Loaded 541,909 rows and 8 columns
Date range: 2010-12-01 to 2011-12-09
```

**Validation:**
```
Overall Quality Score: 71.43%
Checks: 10/14 passed
Recommendation: Review 4 anomalies for business context
```

**KPI Engine:**
```
Successfully calculated 16/16 KPIs
  total_revenue ..................... £9,747,747.93
  order_count ....................... 25,900
  active_customers .................. 4,372
  repeat_customer_rate .............. 83.26%
  international_revenue_share ....... 16.07%
  ...
```

---

## Dataset

Using real UK retail transaction data with:
- **541,909 transactions** over 13 months (Dec 2010 - Dec 2011)
- **4,070 unique products** sold across **38 countries**
- **4,372 unique customers** with purchase history

**Columns:** InvoiceNo, InvoiceDate, CustomerID, StockCode, Description, Quantity, UnitPrice, Country

I picked this dataset because it's real business data with actual messiness — missing CustomerIDs, negative quantities for returns, outliers — rather than a clean synthetic dataset. This makes it better for demonstrating data quality practices.

Source: UCI ML Repository (Online Retail Dataset)

---

## Metrics Tracked

16 KPIs across 5 business areas:

**Finance:** total revenue, revenue per order, revenue per customer

**Operations:** order count, items per order, units sold, product return rate, weekend revenue share, peak hour concentration

**Growth:** active customers, repeat customer rate, new customers

**Product:** product revenue concentration, avg unit price

**International:** revenue by country, international revenue share

Each metric has an owner (Finance, Operations, etc.), a cadence (daily or weekly), and anomaly detection thresholds for Week 4.

---

## Development Plan

### Week 1: Foundation 
Set up project structure, defined all 16 metrics in config files, documented data validation rules, planned architecture.

### Week 2: Data Pipeline 
Built data loader with proper encoding (latin-1 for special characters), implemented 14 automated quality checks, achieved 71.4% data quality score with 4 documented anomalies.

### Week 3: KPI Computation Engine 
Built a config-driven formula parser that executes metric definitions from YAML dynamically. The trickiest parts were handling cross-KPI dependencies (where one metric references another), conditional filtering (e.g. revenue from non-UK customers only), and complex aggregations like top-N product revenue that can't be expressed as simple formulas.

**Key challenge solved:** The formula parser needs to check ratio patterns (`/`) before aggregate patterns (`sum(`, `count(`) — otherwise `sum(Quantity) / order_count` gets partially consumed by the aggregate check and the division is ignored.

### Week 4: Anomaly Detection (Next)
- Z-score method for sudden spikes
- IQR for outlier-robust detection
- Mann-Kendall test for gradual trend changes
- Confidence scoring per detection

### Week 5: Root Cause Analysis
Automatically segment anomalies by Country, Product, Customer dimensions to identify what's driving a change. Trying to avoid the "analyst manually slices data for 2 hours" problem.

### Future (maybe)
Streamlit dashboard, LLM-generated narrative summaries, scheduled runs with Prefect.

---

## Technical Approach

**Config-Driven Design** — metrics defined in YAML, not Python. Business logic is separate from implementation. Inspired by how dbt handles metric definitions.

**Statistical Methods** — using actual statistical tests (Z-score, IQR, Mann-Kendall) with confidence scoring, not arbitrary hardcoded thresholds.

**Production Structure** — modular code organised by responsibility, proper error handling and logging, type hints on public functions.

**Data Quality First** — explicit validation before any analysis. The system fails loudly on threshold breaches rather than silently accepting bad data.

---

## Tech Stack

- Python 3.10+, Pandas, NumPy
- SciPy & Statsmodels (Week 4)
- PyYAML for config parsing
- pytest, black, ruff
- Git with conventional commits

---

## Known Issues / TODOs

- No comprehensive test suite yet (planned for Week 4)
- `new_customers` will equal `active_customers` on this dataset — we only have one year of data, so every customer's first order falls within the dataset period. In production you'd compare against a historical customer table.
- `revenue_by_country` currently returns total revenue as a scalar. The actual per-country breakdown will be handled as a visualisation in Week 4 (our KPI engine only supports scalar outputs).
- Config YAML validation is basic — could add schema validation

---

## What I'm Learning

This project is forcing me to think about things I didn't expect:

- How much time goes into decisions that seem trivial — "should this be a separate module?", "what should I name this function?" Software design is probably 20% coding and 80% deciding how to organise things.
- Real data is never clean. The 71.4% quality score isn't a failure, it's the validation system working correctly.
- The difference between "works in a notebook" and "works in production" is enormous. Reproducibility, error handling, and modular structure matter a lot more than I initially appreciated.
- When building a formula parser, ordering of checks matters. Ratio detection must come before aggregate detection or compound formulas break silently.

---

## Acknowledgments

- **Dataset:** UCI Machine Learning Repository (Online Retail Dataset)
- **Inspiration:** Reading about how Looker, Mode, and dbt structure metric definitions
- **Statistical methods:** SciPy docs, stats coursework, StackOverflow
- **Architecture patterns:** Various blog posts on analytics engineering

---

**Status:** Week 3 Complete - all 16 KPIs calculating correctly  
**Next:** Week 4 - Statistical anomaly detection  
**Estimated completion:** 2 more weeks for core analytics engine

*Second year CS student building this to learn how production analytics systems actually work. Documenting decisions and tradeoffs as I go.*

Last updated: February 2026