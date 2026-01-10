# E-Commerce Analytics Intelligence System

An automated system that monitors business metrics, detects unusual patterns, and helps explain what's driving changes in the data.

## Project Overview

This project analyses real UK retail transaction data to automatically:
- Calculate and track 15 business metrics (revenue, orders, customer behavior, etc.)
- Detect when metrics behave unusually using statistical methods
- Figure out which customer segments or products are driving changes
- Provide actionable explanations instead of just numbers

**Why I built this:** I wanted to go beyond basic data analysis notebooks and build something that could actually run in production. Most analytics work involves repetitive calculations and manual investigation—this automates that process. Plus, I was curious about how companies like Amplitude or Mixpanel structure their metric systems under the hood.

## Current Status

**Phase:** Core Analytics Engine (Weeks 1-5)  
**Progress:** Week 2 Complete  
**Next Up:** KPI computation engine

### Completed:
- Week 1: Project architecture and KPI specifications
- Week 2: Data ingestion and validation pipeline
  - Successfully loaded 541,909 transactions
  - Implemented 14 automated quality checks
  - Achieved 71.4% data quality score (10/14 checks passed)
  - Identified and documented 4 data anomalies

### Currently Building:
-  KPI calculation engine (Week 3)
-  Statistical anomaly detection (Week 4)
-  Root cause analysis (Week 5)

### Future Ideas (might add later):
- AI-generated narrative summaries
- Interactive dashboard
- Automated scheduling

Note: I'm prioritising getting the core analytics engine working well before adding fancy features. Better to have 5 solid features than 8 half-baked ones.

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

**Decision:** Proceeding with these anomalies documented rather than cleaned. In a real-world scenario, these would be flagged for business review (could be legitimate bulk orders or data entry errors requiring domain expertise to resolve). This demonstrates that the validation system works as intended—it catches edge cases for human review rather than silently accepting everything.

---

## How It Works

The system has 5 layers that work together:

```
Data Layer (Week 2) 
  ↓ Loads and validates CSV data
  
KPI Layer (Week 3) 
  ↓ Calculates metrics from config files
  
Detection Layer (Week 4-5) 
  ↓ Finds anomalies and trends statistically
  
Analysis Layer (Week 5) 
  ↓ Figures out why metrics changed
  
Output Layer (Future) 
  ↓ Presents findings to users
```

**Design decision:** I'm using YAML config files to define metrics instead of hardcoding them. Initially I just had Python functions, but I kept having to modify code whenever I wanted to change a threshold or add a metric. This approach means I can tweak business logic without touching the codebase—which is how real analytics platforms work (learned this from reading about how dbt structures metric definitions).

## Project Structure

```
ecommerce-data-storytelling/
├── config/
│   ├── kpis.yaml                  # Metric definitions
│   └── data_contracts.yaml        # Data validation rules
├── src/
│   ├── data/
│   │   ├── ingestion.py          # CSV loading
│   │   └── validation.py         # Quality checks
│   ├── kpis/                      # Metric calculations
│   ├── insights/                  # Anomaly detection
│   ├── narratives/                # Text generation
│   └── platform/                  # Dashboard
├── tests/                         # Unit tests
├── data/
│   ├── raw/                       # Original CSV data
│   ├── processed/                 # Cleaned data
│   └── insights/                  # Generated analysis
├── notebooks/                     # Exploration
└── docs/                         # Documentation
```

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

### Running Data Pipeline

```bash
# Load and summarise data
python -m src.data.ingestion

# Validate data quality
python -m src.data.validation
```

**Note:** Do not run scripts directly (e.g., `python src/data/ingestion.py`) as this can cause import and path resolution errors. Always use the module syntax with `-m` flag.

### Expected Output

**Ingestion:**
```
INFO: Loaded 541,909 rows and 8 columns
Date range: 2010-12-01 to 2011-12-09
Unique customers: 4,372
Unique products: 4,070
```

**Validation:**
```
Overall Quality Score: 71.43%
Checks: 10/14 passed
Recommendation: Review 4 anomalies for business context
```

## Dataset

Using real UK retail transaction data with:
- **541,909 transactions** over 13 months (Dec 2010 - Dec 2011)
- **4,070 unique products** sold across **38 countries**
- **4,372 unique customers** with purchase history

**Columns:**
- InvoiceNo, InvoiceDate, CustomerID, StockCode
- Description, Quantity, UnitPrice, Country

I picked this dataset because:
- It's real business data (not synthetic), so it has actual messiness—missing CustomerIDs, negative quantities for returns, obvious outliers
- Multiple dimensions to slice by (time, geography, products, customers)
- Large enough to be interesting (500K+ rows) but runs fine on my laptop
- Publicly available via UCI ML Repository, so reproducible

The dataset has realistic quirks: 24.9% of transactions lack CustomerIDs (guest checkouts), returns are marked with negative quantities, and there are a handful of edge cases that would require business context to resolve. This makes it perfect for demonstrating data quality practices.

## Metrics I'm Tracking

I defined 15 KPIs across different business areas:

**Revenue:**
- Total revenue, revenue per order, revenue per customer

**Volume:**
- Order count, items per order, units sold

**Customers:**
- Active customers, repeat rate, new customers

**Products:**
- Product concentration, average price, return rate

**Geography:**
- Revenue by country, international vs domestic split

Each metric has:
- **Owner** (who would care about it—Finance, Operations, etc.)
- **Cadence** (daily or weekly)
- **Thresholds** for detecting unusual behavior

Originally I just had 5 metrics, but after doing some EDA I realised you need different views for different stakeholders. Finance cares about total revenue, Operations cares about order volume, Product team wants basket size metrics. This mimics how actual companies organise their dashboards.

## Development Plan

### Week 1: Foundation (Completed)
- Set up project structure
- Define all metrics in config files
- Document data validation rules
- Plan architecture

Took longer than expected because I kept refactoring the folder structure. Finally settled on organising by layer (data, kpis, insights) rather than by feature.

### Week 2: Data Pipeline (Completed)
- Load CSV data with pandas
- Validate against schema rules
- Check data quality (completeness, outliers)
- Handle missing values and errors

**Achievements:**
- Built reliable data loader with proper encoding (latin-1 for special characters)
- Implemented 14 automated quality checks across 4 dimensions
- Achieved 71.4% initial quality score with 4 documented anomalies
- Proper error handling and logging throughout

**Lessons learned:** The importance of validating early. Found 2 negative prices and 2 extreme values that would have corrupted downstream analysis if not caught. Also learned that 25% of customers being "guests" (no CustomerID) is normal for retail—initially thought this was a data quality issue.

### Week 3: Metric Calculation (Next)
- Parse YAML config files
- Calculate all 15 KPIs dynamically
- Support daily/weekly aggregations
- Make calculations reproducible

Challenge: Figuring out how to parse formulas like "sum(Quantity * UnitPrice)" from YAML and execute them safely. Might use eval() with heavy sanitisation or build a simple expression parser.

### Week 4: Anomaly Detection
- Implement Z-score method
- Add IQR (interquartile range) method
- Detect trend changes (Mann-Kendall test)
- Score confidence for each detection

I want multiple detection methods because different approaches catch different types of anomalies. Z-score is good for sudden spikes, IQR handles outliers better, Mann-Kendall catches gradual trends.

### Week 5: Root Cause Analysis
- Automatically segment by dimensions
- Calculate impact of each segment
- Rank what's driving the change
- Compare actual vs expected by segment

This is the most complex part—need to systematically check Country, Product, Customer segments, etc. to identify which combination explains the anomaly. Trying to avoid the "analyst manually slices data for 2 hours" problem.

### Future Enhancements (Phase 2)
If I have time after finishing the core system:
- Generate plain English summaries using templates (or experiment with LLMs if I can get API access)
- Build a Streamlit dashboard to view insights interactively
- Add ability to schedule daily runs with Prefect

Realistically, I'll probably get through Week 5 and call it done. These are nice-to-haves but not essential for demonstrating the core capability.

## Technical Approach

What makes this different from typical student projects:

**1. Config-Driven Design**
- Metrics defined in YAML, not hardcoded in Python
- Easy to modify without changing code
- Separates business logic from implementation
- Inspired by how tools like dbt handle metric definitions

**2. Statistical Methods**
- Using actual statistical tests (Z-score, IQR, Mann-Kendall)
- Not just arbitrary thresholds like "if revenue < 1000, alert"
- Confidence scoring so you know how certain the detection is
- Learned these methods from my stats class and SciPy docs

**3. Production Structure**
- Modular code organised by responsibility, not just notebooks
- Unit tests for reliability (aiming for 80%+ coverage)
- Proper error handling and logging
- Type hints where it matters

**4. Data Quality Focus**
- Explicit validation rules before any analysis
- Data quality checks that fail loudly if thresholds aren't met
- Handles missing CustomerIDs (guest checkouts) and returns (negative quantities)

Initially I just loaded the CSV and started analysing, but hit issues with:
- Some product descriptions being null
- Quantities being negative (returns)
- A few unit prices being 0
So I added explicit contracts to catch these upfront. The validation caught 4 edge cases immediately, which validated the approach.

## Tech Stack

**Core:**
- Python 3.10+
- Pandas & NumPy for data wrangling
- SciPy & Statsmodels for statistical tests
- scikit-learn for some preprocessing
- PyYAML for config parsing

**Development:**
- pytest for testing
- black & ruff for formatting (finally gave in to auto-formatting after too many style debates with myself)
- Git for version control with conventional commits

**Maybe Later:**
- Streamlit for dashboarding (tried it before, pretty straightforward)
- OpenAI API for narrative generation (need to figure out cost first)
- Plotly for interactive visualisations

## What I'm Learning

This project is forcing me to develop:

**Analytics Engineering**
- Building systems that run repeatedly, not one-off analyses
- Thinking about reproducibility and maintainability
- Understanding the difference between "works in a notebook" and "works in production"

**Software Design**
- Modular architecture (each layer has one job)
- Separation of concerns (config vs code vs data)
- When to use classes vs functions (still figuring this out tbh)

**Statistical Thinking**
- Moving beyond descriptive stats (mean, median) to inferential methods
- Understanding false positive rates in anomaly detection
- Quantifying uncertainty with confidence scores

**Production Practices**
- Writing tests that actually catch bugs (not just for coverage numbers)
- Documentation that explains "why" not just "what"
- Git commits that tell a story of what changed and why

Biggest surprise so far: How much time goes into decisions that seem trivial, like "should this be a separate module?" or "what should I name this function?" Turns out software design is 20% coding and 80% deciding how to organise things.

Also learned that real data is never clean. The 71.4% quality score isn't a failure—it's validation that the system works. In production, you'd investigate those 4 anomalies with business stakeholders, not blindly delete them.

## Known Issues / TODOs

Things I'm aware of but haven't addressed yet:
- Scripts must be run as modules (`python -m`) not direct paths
- No comprehensive test suite yet (Week 3 goal)
- Config validation is basic (could add schema validation for YAML files)
- No CI/CD setup yet (maybe GitHub Actions later?)
- Documentation could use more code examples

Data Quality Items (Documented, Not Fixed):
- 2 negative unit prices flagged for review
- 2 transactions exceeding £100K threshold
- Decision to proceed with these documented rather than cleaned

Also considering:
- Should I use poetry instead of requirements.txt for dependency management?
- Type hints everywhere or just on public functions?
- How much unit testing is enough before it becomes overkill?

## Acknowledgments

- **Dataset:** UCI Machine Learning Repository (Online Retail Dataset)
- **Inspiration:** Reading about how Looker, Mode, and dbt structure metric definitions got me thinking about config-driven approaches
- **Statistical methods:** Learned from SciPy documentation, stats coursework, and a bunch of StackOverflow deep dives
- **Architecture patterns:** Various blog posts on analytics engineering and data platform design

Shoutout to everyone on the data engineering subreddit who unknowingly helped me through lurking.

## Notes

This is a learning project I'm building during my second year of Computer Science. My goals are:
- Build something complete rather than abandoning it halfway (guilty of this before)
- Write code that I could actually hand off to someone else
- Understand the "why" behind design decisions, not just implement features
- Practice building systems, not just writing scripts

I'm documenting decisions and tradeoffs as I go because (1) future me will forget why I did things, and (2) it helps clarify my own thinking.

If you're reading this and have suggestions or spot issues, feel free to open an issue or reach out. Always happy to learn from people with more experience.

---

**Status:** Week 2 Complete | Week 3 Starting Soon  
**Estimated Timeline:** 3 more weeks for core analytics engine

Last updated: January 2026