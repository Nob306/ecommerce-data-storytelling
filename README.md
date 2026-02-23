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

**Phase:** Core Analytics Engine  
**Progress:** Anomaly Detection Complete  
**Next Up:** Root cause analysis

### Completed:
- **Phase 1 - Foundation:** Project architecture and KPI specifications
- **Phase 2 - Data Pipeline:** Data ingestion and validation pipeline
  - Successfully loaded 541,909 transactions
  - Implemented 14 automated quality checks
  - Achieved 71.4% data quality score (10/14 checks passed)
  - Identified and documented 4 data anomalies
- **Phase 3 - KPI Engine:** KPI computation engine
  - Built config-driven formula parser that reads metric definitions from YAML
  - Implemented support for simple aggregations, cross-KPI dependencies, conditional filtering, and complex multi-step calculations
  - All 16 KPIs calculating correctly across Finance, Operations, Growth, Product, and International categories
  - Results saved with timestamps to `data/processed/kpi_results.csv`
- **Phase 4 - Anomaly Detection:** Statistical anomaly detection
  - Built detection engine running Z-score, IQR, and Mann-Kendall tests across all 14 KPIs
  - Implemented confidence scoring that boosts when multiple methods agree on the same anomaly
  - Added baseline windowing to exclude Christmas 2010 from baseline calculations - without this, the seasonal spike inflates "normal" and makes regular months look like drops
  - Detected 47 anomalies across 13 KPIs on the weekly time series
  - Notable finding: product_revenue_concentration spiked 142% above expected in June 2011 - revenue unusually concentrated in top 20 products that week
  - Results saved to data/insights/anomalies.csv for root cause analysis

### Currently Building:
- Root cause analysis

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
- Completeness: CustomerID 24.9% missing (acceptable - represents guest checkouts)
- Completeness: Description 0.3% missing (well within threshold)
- Cancellations properly marked with negative quantities

**Known Issues (Documented, Not Fixed):**
- 2 transactions with negative unit prices (0.0004% of data)
- 2 transactions exceeding £100K threshold (0.0004% of data)

**Decision:** Proceeding with these anomalies documented rather than cleaned. In a real-world scenario, these would be flagged for business review - they could be legitimate bulk orders or data entry errors requiring domain expertise to resolve. This demonstrates that the validation system works as intended: it catches edge cases for human review rather than silently accepting everything.

---

## How It Works

The system has 5 layers that work together:

```
Data Layer 
  ↓ Loads and validates CSV data
  
KPI Layer 
  ↓ Calculates metrics from config files
  
Detection Layer 
  ↓ Finds anomalies and trends statistically
  
Analysis Layer 
  ↓ Figures out why metrics changed
  
Output Layer 
  ↓ Presents findings to users
```

**Design decision:** Metrics are defined in YAML config files rather than hardcoded in Python. This means business logic (thresholds, formulas, owners) can be changed without touching the codebase - which is how real analytics platforms like dbt structure metric definitions.

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
│   │   ├── models.py
│   │   ├── methods.py
│   │   └── detector.py
│   ├── narratives/                
│   └── platform/                  
├── data/
│   ├── raw/
│   │   └── UK retail data.csv    541,909 rows
│   ├── processed/
│   │   └── kpi_results.csv       
│   └── insights/
│       └── anomalies.csv         47 anomalies detected
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

# 4. Run anomaly detection
python -m src.insights.detector
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

**Anomaly Detector:**
```
Total Anomalies Detected: 47
  CRITICAL: 1
  HIGH: 14
  MEDIUM: 13
  LOW: 19
Results saved to: data/insights/anomalies.csv
```

---

## Dataset

Using real UK retail transaction data with:
- **541,909 transactions** over 13 months (Dec 2010 - Dec 2011)
- **4,070 unique products** sold across **38 countries**
- **4,372 unique customers** with purchase history

**Columns:** InvoiceNo, InvoiceDate, CustomerID, StockCode, Description, Quantity, UnitPrice, Country

I picked this dataset because it's real business data with actual messiness - missing CustomerIDs, negative quantities for returns, outliers - rather than a clean synthetic dataset. This makes it better for demonstrating data quality practices.

Source: UCI ML Repository (Online Retail Dataset)

---

## Metrics Tracked

16 KPIs across 5 business areas:

**Finance:** total revenue, revenue per order, revenue per customer

**Operations:** order count, items per order, units sold, product return rate, weekend revenue share, peak hour concentration

**Growth:** active customers, repeat customer rate, new customers

**Product:** product revenue concentration, avg unit price

**International:** revenue by country, international revenue share

Each metric has an owner (Finance, Operations, etc.), a cadence (daily or weekly), and anomaly detection thresholds.

---

## Development Plan

### Phase 1: Foundation 
Set up project structure, defined all 16 metrics in config files, documented data validation rules, planned architecture.

### Phase 2: Data Pipeline 
Built data loader with proper encoding (latin-1 for special characters), implemented 14 automated quality checks, achieved 71.4% data quality score with 4 documented anomalies.

### Phase 3: KPI Computation Engine 
Built a config-driven formula parser that executes metric definitions from YAML dynamically. The trickiest parts were handling cross-KPI dependencies (where one metric references another), conditional filtering (e.g. revenue from non-UK customers only), and complex aggregations like top-N product revenue that can't be expressed as simple formulas.

**Key challenge solved:** The formula parser needs to check ratio patterns (`/`) before aggregate patterns (`sum(`, `count(`) - otherwise `sum(Quantity) / order_count` gets partially consumed by the aggregate check and the division is ignored.

### Phase 4: Anomaly Detection 
Three detection methods running in parallel across all KPIs:

Z-score catches sudden spikes by measuring how many standard deviations a value is from the mean. IQR is more robust - it uses the middle 50% of the data so extreme values don't distort what counts as normal. Mann-Kendall detects gradual trends rather than point anomalies - it's what flagged that revenue, orders, and active customers were all on a statistically significant upward trajectory through 2011.

The trickiest part was the baseline problem: with only 13 months of data, the Christmas 2010 spike is part of the same dataset you're detecting anomalies in. Adding a configurable baseline_window parameter to exclude that period was the fix - you can tell the detector "calculate what's normal using Jan-Nov 2011 only."

When multiple methods flag the same KPI on the same date, confidence gets boosted. A point that Z-score and IQR both flag independently is stronger evidence than either alone.

### Phase 5: Root Cause Analysis 
Automatically segment anomalies by Country, Product, Customer dimensions to identify what's driving a change. Trying to avoid the "analyst manually slices data for 2 hours" problem.

### Future (maybe)
Streamlit dashboard, LLM-generated narrative summaries, scheduled runs with Prefect.

---

## Technical Approach

**Config-Driven Design** - metrics defined in YAML, not Python. Business logic is separate from implementation. Inspired by how dbt handles metric definitions.

**Statistical Methods** - three methods were chosen deliberately, each catching a different type of problem:

Z-score is the most interpretable - it tells you exactly how many standard deviations a value is from the mean, which is easy to explain to a non-technical stakeholder. The tradeoff is it assumes the data is roughly normally distributed, which retail revenue isn't (it's right-skewed because of occasional large orders). So Z-score alone would miss some real anomalies and generate false positives on others.

IQR fixes that problem. Instead of using the mean and standard deviation (which get pulled by extreme values), it uses the middle 50% of the data to set its boundaries. That makes it robust to the kind of skewed distributions you get with revenue data. The downside is it's less interpretable - "this value is 2.3 IQR fence widths outside the upper fence" doesn't mean much to most people.

Mann-Kendall is different from both - it doesn't look at individual points at all. It's a non-parametric rank-based test that asks whether there's a statistically significant monotonic trend across the whole series. It's what caught that revenue, orders, and active customers were all gradually increasing through 2011, even in weeks where no single data point looked unusual. Non-parametric means it makes no assumptions about the distribution of the data, which matters here.

Running all three in parallel means sudden spikes, distributional outliers, and gradual drift are all covered. When multiple methods flag the same point, confidence gets boosted - that's the key design decision that keeps false positive rates manageable.

**Production Structure** - modular code organised by responsibility, proper error handling and logging, type hints on public functions.

**Data Quality First** - explicit validation before any analysis. The system fails loudly on threshold breaches rather than silently accepting bad data.

---

## Tech Stack

- Python 3.10+, Pandas, NumPy
- SciPy & Statsmodels
- PyYAML for config parsing
- pytest, black, ruff
- Git with conventional commits

---

## Known Issues / TODOs

- No comprehensive test suite yet
- `new_customers` will equal `active_customers` on this dataset - we only have one year of data, so every customer's first order falls within the dataset period. In production you'd compare against a historical customer table.
- `revenue_by_country` currently returns total revenue as a scalar. The actual per-country breakdown will be handled as a visualisation later (our KPI engine only supports scalar outputs).
- Config YAML validation is basic - could add schema validation

---

## What I'm Learning

This project is forcing me to think about things I didn't expect:

- How much time goes into decisions that seem trivial - "should this be a separate module?", "what should I name this function?" Software design is probably 20% coding and 80% deciding how to organise things.
- Real data is never clean. The 71.4% quality score isn't a failure, it's the validation system working correctly.
- The difference between "works in a notebook" and "works in production" is enormous. Reproducibility, error handling, and modular structure matter a lot more than I initially appreciated.
- When building a formula parser, ordering of checks matters. Ratio detection must come before aggregate detection or compound formulas break silently.
- Baseline selection matters more than algorithm choice. The same Z-score threshold produces completely different results depending on whether you include a known seasonal spike in your baseline. Getting this wrong generates noise, not signal.
- Multiple detection methods catching the same anomaly is much more meaningful than any single method - the confidence boosting logic ended up being one of the more useful design decisions.

---

## Acknowledgments

- **Dataset:** UCI Machine Learning Repository (Online Retail Dataset)
- **Inspiration:** Reading about how Looker, Mode, and dbt structure metric definitions
- **Statistical methods:** SciPy docs, stats coursework, StackOverflow
- **Architecture patterns:** Various blog posts on analytics engineering

---

**Status:** Phase 4 Complete - 47 anomalies detected across 13 KPIs  
**Next:** Phase 5 - Root cause analysis  
**Estimated completion:** 1 more phase for core analytics engine

*Second year CS student building this to understand how production analytics systems actually work. Building in phases rather than a fixed schedule - shipping each layer properly before moving to the next.*

Last updated: February 2026