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

**Phase:** Phase 6 Complete  
**Progress:** Full pipeline from raw data to AI-generated narratives, live dashboard, and LLM observability  
**Next Up:** Phase 7 PostgreSQL + dbt + Power BI + CI/CD

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
  - Notable finding: product_revenue_concentration spiked above expected in June 2011 - revenue was more concentrated in top 20 products than usual that week
  - Results saved to data/insights/anomalies.csv for root cause analysis
- **Phase 5 - Root Cause Analysis:** Automated dimensional slicing to explain anomalies
  - For each anomaly, filters raw transaction data to the anomaly week and slices by Country, StockCode, and HourOfDay
  - Calculates each segment's contribution to the total deviation, scaled against the baseline period
  - 19 anomalies successfully explained, 20 flagged for manual review (ratio KPIs cannot be directly segmented)
  - Ratio KPIs are flagged rather than producing misleading results - you cannot slice repeat_customer_rate by Country without recalculating numerator and denominator separately per segment, and doing it naively gives nonsense numbers
  - Results saved to data/insights/root_causes.csv
  - Notable finding: the November 2011 spike in active_customers, order_count, total_revenue, and units_sold all trace back to the same cause - UK customers buying two specific products (StockCode 23084 and 22086) at unusually high volumes during afternoon hours. That is not four separate anomalies, it is one pre-Christmas wholesale buying event showing up across four metrics.
- **Phase 6 - Dashboard, Narratives, and AI Layer:** Streamlit dashboard, LLM narrative generation, RAG pipeline, and AI observability
  - Built Streamlit dashboard with 5 pages: Overview, Time Series, Anomalies, Insights, AI Lab
  - Precompute layer saves all pipeline outputs to parquet cache for fast dashboard loading
  - LLM narratives generated via Groq (Llama 3.1-8b-instant) for all 19 explained anomalies
  - Prompt versioning system in `config/prompts.yaml` — v1 to v2 reduced quality violations from 42% to 0%
  - Monitoring layer logs every LLM call to JSONL with latency, token usage, cost, and quality flags
  - RAG pipeline built with LangChain LCEL + ChromaDB + sentence-transformers — retrieves 3 similar historical anomalies before generating each narrative
  - AI Lab dashboard page surfaces monitoring stats, narrative comparison (standard vs RAG), and full prompt version history
  - TenantConfig path resolution layer single-tenant now, multi-tenant ready

### Currently Building:
- Phase 7: PostgreSQL + dbt + Power BI + CI/CD

### Future Ideas (might add later):
- AWS deployment
- Multi-tenant support for multiple business datasets
- Churn prediction model on the same dataset

Note: I'm prioritising getting each layer working well before moving to the next. Better to have 5 solid features than 8 half-baked ones.

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
| Repeat Customer Rate | ~70% |
| New Customers | 4,372 |
| Product Revenue Concentration | ~14% from top 20 products |
| Avg Unit Price | £1.88 |
| Product Return Rate | ~20% |
| International Revenue Share | ~16% |
| Weekend Revenue Share | ~8% |
| Peak Hour Concentration | ~40% |

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

The system has 6 layers that work together:

```
Data Layer 
  ↓ Loads and validates CSV data
  
KPI Layer 
  ↓ Calculates metrics from config files
  
Detection Layer 
  ↓ Finds anomalies and trends statistically
  
Analysis Layer 
  ↓ Figures out why metrics changed
  
AI Layer 
  ↓ Generates plain-English narratives with RAG context, logs every call
  
Output Layer 
  ↓ Presents findings through Streamlit dashboard
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
│   ├── kpis.yaml                    # 16 metric definitions (formula, owner, thresholds)
│   ├── data_contracts.yaml          # Data validation rules and schema
│   └── prompts.yaml                 # Versioned LLM prompt templates (v1, v2)
├── src/
│   ├── config/
│   │   └── tenant_config.py         # Path resolution — single-tenant now, multi-tenant ready
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
│   │   ├── detector.py
│   │   ├── results.py
│   │   └── analyser.py
│   ├── narratives/
│   │   ├── monitor.py               # LLM call logging (latency, cost, quality flags)
│   │   ├── narrator.py              # Standard narrative generation via Groq
│   │   ├── retriever.py             # ChromaDB vector store + similarity search
│   │   └── rag_narrator.py          # LangChain RAG pipeline with retrieved context
│   └── platforms/
│       ├── precompute.py            # Runs pipeline, saves parquet cache for dashboard
│       ├── dashboard.py             # Streamlit app (5 pages)
│       └── ai_lab.py                # AI Lab page — monitoring, comparison, prompt history
├── data/
│   ├── raw/
│   │   └── UK retail data.csv       # 541,909 rows
│   ├── processed/
│   │   └── kpi_results.csv       
│   ├── insights/
│   │   ├── anomalies.csv            # 47 anomalies detected
│   │   ├── root_causes.csv          # 39 root cause results
│   │   ├── narratives.json          # Standard LLM narratives (v2 prompt)
│   │   └── rag_narratives.json      # RAG-enhanced narratives (v2-rag)
│   ├── monitoring/
│   │   └── llm_calls.jsonl          # Every LLM call logged (latency, tokens, cost, flags)
│   └── cache/                       # Precomputed parquet files (gitignored)
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

### Environment Variables

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_key_here
```

Get a free key at [console.groq.com](https://console.groq.com).

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

# 5. Run root cause analysis
python -m src.insights.analyser

# 6. Precompute dashboard cache
python -m src.platforms.precompute

# 7. Generate narratives
python -m src.narratives.narrator         
python -m src.narratives.rag_narrator     

# 8. Launch dashboard
streamlit run src/platforms/dashboard.py
```

**Note:** Do not run scripts directly (e.g., `python src/data/ingestion.py`) as this causes import and path resolution errors. Always use the `-m` flag.

### Expected Output

**Ingestion:**

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
  repeat_customer_rate .............. 70.00%
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

**Root Cause Analyser:**
```
Total Anomalies Analysed: 39
  Successfully explained: 19
  Manual review required: 20
  Insufficient data: 0
Results saved to: data/insights/root_causes.csv
```

**Narrator:**
```
Generated: 19
Skipped (cached): 0
Prompt version: v2
Total cost: $0.000324 USD
Avg latency: 217ms
% violations: 0/19
```

---

## Dashboard Pages

**Overview** — 16 KPI cards with trend arrows and anomaly indicators. Red dot = anomaly detected for that metric.

**Time Series** — Weekly KPI line chart with coloured dashed vertical lines marking anomaly dates by severity (green=low, orange=high, red=critical).

**Anomalies** — Filterable anomaly table. Click any row to see the root cause bar chart and LLM narrative for that anomaly.

**Insights** — The November 2011 event visualised as a normalised 4-KPI chart, with AI narrative summaries for each anomaly in the cluster.

**AI Lab** — LLM observability and evaluation:
- *Monitoring* — live stats for every API call (total calls, success rate, cost, latency, quality flags by prompt version)
- *Narrative Comparison* — pick any anomaly and compare standard vs RAG narrative side by side with retrieved context documents shown
- *Prompt Versions* — full template history from `config/prompts.yaml` with call counts, violation rates, and latency per version

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

### Phase 1: Foundation ✅
Set up project structure, defined all 16 metrics in config files, documented data validation rules, planned architecture.

### Phase 2: Data Pipeline ✅
Built data loader with proper encoding (latin-1 for special characters), implemented 14 automated quality checks, achieved 71.4% data quality score with 4 documented anomalies.

### Phase 3: KPI Computation Engine ✅
Built a config-driven formula parser that executes metric definitions from YAML dynamically. The trickiest parts were handling cross-KPI dependencies (where one metric references another), conditional filtering (e.g. revenue from non-UK customers only), and complex aggregations like top-N product revenue that can't be expressed as simple formulas.

**Key challenge solved:** The formula parser needs to check ratio patterns (`/`) before aggregate patterns (`sum(`, `count(`) - otherwise `sum(Quantity) / order_count` gets partially consumed by the aggregate check and the division is ignored.

### Phase 4: Anomaly Detection ✅
Three detection methods running in parallel across all KPIs:

Z-score catches sudden spikes by measuring how many standard deviations a value is from the mean. IQR is more robust - it uses the middle 50% of the data so extreme values don't distort what counts as normal. Mann-Kendall detects gradual trends rather than point anomalies - it's what flagged that revenue, orders, and active customers were all on a statistically significant upward trajectory through 2011.

The trickiest part was the baseline problem: with only 13 months of data, the Christmas 2010 spike is part of the same dataset you're detecting anomalies in. Adding a configurable baseline_window parameter to exclude that period was the fix - you can tell the detector "calculate what's normal using Jan-Nov 2011 only."

When multiple methods flag the same KPI on the same date, confidence gets boosted. A point that Z-score and IQR both flag independently is stronger evidence than either alone.

### Phase 5: Root Cause Analysis ✅
For each detected anomaly, the analyser filters raw transaction data to the anomaly week and slices by Country, StockCode, and HourOfDay. It calculates how much each segment contributed to the total deviation relative to what was expected from the baseline, then ranks them by impact.

The key design decision was to flag ratio KPIs for manual review rather than analyse them naively. Slicing repeat_customer_rate by Country would require recalculating the numerator and denominator separately for each country - just filtering the data and recalculating the ratio produces numbers that look plausible but are wrong. Better to be honest about the limitation than to surface misleading results.

Contribution percentages can exceed 100% for the primary driver - this is not a bug. It happens when the dominant segment (usually UK, which accounts for the majority of transactions) overcompensates while other segments were simultaneously below their baseline. The maths is correct; it just looks odd without context.

The most interesting finding was that four separate anomalies in November 2011 (active_customers, order_count, total_revenue, units_sold) all point to the same root cause - two specific products bought by UK customers at high volumes during afternoon hours across three consecutive weeks. The root cause analyser caught that automatically, which is exactly what it was built to do.

### Phase 6: Dashboard, Narratives, and AI Layer ✅
Streamlit dashboard with 5 pages and Plotly visualisations. Precompute layer saves all pipeline outputs to parquet cache so the dashboard loads instantly without re-running the full pipeline.

LLM narratives generated via Groq (free tier, Llama 3.1-8b-instant). Every call logged through a monitoring layer to JSONL — latency, token usage, estimated cost, and output quality flags per call. Prompt templates versioned in `config/prompts.yaml` rather than hardcoded in Python, so changes are trackable in git. The v1 to v2 prompt change reduced quality violations from 8/19 (42%) to 0/19 (0%) — caught and confirmed through the monitoring layer.

RAG pipeline built with LangChain LCEL + ChromaDB + sentence-transformers. Each narrative generation first retrieves the 3 most similar historical anomalies from the vector store, injects them as context, then calls the LLM. A cross-KPI retrieval bug caused hallucinations in the first run — the LLM cited a revenue spike that didn't exist because it was given irrelevant product concentration anomalies as context. Fixed by adding same-KPI metadata filtering to the retrieval step.

AI Lab dashboard page gives visibility into all of this — monitoring stats, standard vs RAG narrative comparison side by side, and the full prompt version history with quality metrics.

### Phase 7: PostgreSQL + dbt + Power BI + CI/CD 🔜
Migrate from CSV/parquet to a proper database layer. Replace the KPI engine's CSV outputs with dbt models. Add Power BI connection for stakeholder-facing reporting. Set up CI/CD pipeline with automated testing on push.

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
- Streamlit, Plotly
- Groq (Llama 3.1-8b-instant), LangChain, ChromaDB, sentence-transformers
- Parquet (cache), JSONL (monitoring log)
- pytest, black, ruff
- Git with conventional commits

---

## Known Issues / TODOs

- No comprehensive test suite yet
- `new_customers` will equal `active_customers` on this dataset - we only have one year of data, so every customer's first order falls within the dataset period. In production you'd compare against a historical customer table.
- `revenue_by_country` currently returns total revenue as a scalar. The actual per-country breakdown will be handled as a visualisation later (our KPI engine only supports scalar outputs).
- Config YAML validation is basic - could add schema validation
- Root cause contribution percentages can exceed 100% for the primary driver. This is not a calculation error - it happens when the dominant segment (usually UK, which drives the majority of transactions) overperforms while other segments are simultaneously below their baseline, meaning the primary segment has to "overcompensate" to produce the observed total deviation. The number is mathematically correct but looks odd without that explanation.
- RAG token counts are not captured for v2-rag calls LangChain LCEL's pipe syntax doesn't return a usage object directly. Latency is captured correctly.

---

## What I'm Learning

This project is forcing me to think about things I didn't expect:

- How much time goes into decisions that seem trivial - "should this be a separate module?", "what should I name this function?" Software design is probably 20% coding and 80% deciding how to organise things.
- Real data is never clean. The 71.4% quality score isn't a failure, it's the validation system working correctly.
- The difference between "works in a notebook" and "works in production" is enormous. Reproducibility, error handling, and modular structure matter a lot more than I initially appreciated.
- When building a formula parser, ordering of checks matters. Ratio detection must come before aggregate detection or compound formulas break silently.
- Baseline selection matters more than algorithm choice. The same Z-score threshold produces completely different results depending on whether you include a known seasonal spike in your baseline. Getting this wrong generates noise, not signal.
- Multiple detection methods catching the same anomaly is much more meaningful than any single method - the confidence boosting logic ended up being one of the more useful design decisions.
- Root cause analysis taught me that the same event can show up as multiple separate anomalies. The November 2011 spike looked like four distinct problems until the dimensional slicing showed they all pointed to the same two products and the same customer segment. Automated analysis caught something that would have taken an analyst a while to piece together manually.
- Prompts are code. They need versioning, testing, and measurement. Changing a prompt without tracking what changed and whether it helped is the same mistake as changing production code without version control.
- Observability first. You cannot evaluate an AI system you cannot observe. The monitoring layer needed to exist before the RAG layer, not after.

---

## Acknowledgments

- **Dataset:** UCI Machine Learning Repository (Online Retail Dataset)
- **Inspiration:** Reading about how Looker, Mode, and dbt structure metric definitions
- **Statistical methods:** SciPy docs, stats coursework, StackOverflow
- **Architecture patterns:** Various blog posts on analytics engineering

---

## How I Built This With AI Assistance

This project was built using Claude as a pair programming tool throughout. I'm documenting this deliberately rather than omitting it, transparency about AI-assisted development is more useful than pretending it didn't happen, and the way I used it is worth explaining.

### The workflow

I directed the architecture and made every significant design decision. Claude generated implementation. I reviewed, tested, caught bugs, and directed fixes. The split in practice: I specified what to build and why, Claude wrote the first version, I ran it and evaluated whether it worked correctly, and we iterated from there.

This is not meaningfully different from how senior engineers use AI tools now. The skill is in knowing what to build, recognising when the output is wrong, and understanding the system well enough to debug it. Generating code is the easy part.

### What the AI got wrong — and how I caught it

These are real bugs that appeared during the build and required actual diagnosis to fix:

**KPI calculation errors in the README** — The README documented `repeat_customer_rate` as ~83% and `product_revenue_concentration` as ~47%. Both were wrong, carried over from an earlier phase when the engine had formula bugs. I caught them by running a manual verification audit against the raw data and comparing every value in the README against the engine output. The engine was correct; the README had never been updated. Corrected to 70% and 14% respectively.

**Date axis showing year 2035** — The time series chart was displaying years starting from 2035 instead of 2011. The root cause was that the KPI engine returns a `date` column in the DataFrame rather than setting it as the index, so the dashboard was receiving a plain integer RangeIndex (0, 1, 2...) which Plotly interpreted as epoch offsets. Fixed by explicitly calling `set_index('date')` in `precompute.py` before saving to parquet. The fix required understanding the full data flow from engine output to parquet to dashboard render — not just changing one line.

**RAG hallucination from cross-KPI retrieval** — The first RAG run retrieved `product_revenue_concentration` anomalies when generating a narrative for a `total_revenue` anomaly, because the vector similarity search matched document structure rather than business meaning. The LLM then fabricated a reference to a revenue spike in January 2011 that didn't exist, citing the retrieved context as if it were relevant. I caught it by comparing the retrieved context IDs against the anomaly being narrated and recognising the mismatch. Fixed by adding a `same_kpi_only=True` metadata filter to ChromaDB retrieval. The monitoring layer confirmed zero hallucinations after the fix.

**Prompt violations caught by monitoring** — 8 out of 19 v1 narratives contained percentages, violating the explicit prompt instruction not to use them. I wouldn't have caught this by reading outputs manually — 8/19 is easy to miss when you're skimming. The monitoring layer flagged it automatically. The fix was tightening the v2 prompt wording, and the monitoring log confirmed the violation rate dropped from 42% to 0%.

### What this taught me about working with AI tools

**Prompts are code.** They need versioning, testing, and measurement. The prompt versioning system in `config/prompts.yaml` exists because I learned mid-project that changing a prompt without tracking what changed and whether it helped is the same mistake as changing production code without version control.

**Observability first.** The monitoring layer was built before the RAG layer specifically because you cannot evaluate an AI system you cannot observe. This is the same principle as adding logging and metrics before scaling a service you need to be able to see what's happening before you can improve it.

**AI accelerates implementation, not understanding.** The design decisions in this project baseline windowing, ratio KPI flagging, JSONL for monitoring logs, TenantConfig for path resolution all came from thinking through the problem before writing code. AI generated the implementation quickly once the design was clear. Where I skipped the thinking step and let AI drive the design, the results needed more rework.

**Verification is the job.** The KPI audit, the date axis debugging, the RAG hallucination diagnosis none of these were caught by AI. They were caught by running the system, looking at the output, and asking whether it was correct. That's the work that remains irreducibly human regardless of how good the code generation gets.

### What I can explain without AI assistance

Every layer of this system. The statistical methods and why three were chosen. The formula parser and why check ordering matters. The baseline windowing decision and what happens if you get it wrong. The dimensional slicing approach and why ratio KPIs can't be segmented naively. The RAG architecture and the specific failure mode that caused the hallucination. The JSONL monitoring format and why it was chosen over a database.

If an interviewer wants to walk through any part of this codebase, I can explain the design decisions, the tradeoffs, and what I would do differently.

---

**Status:** Phase 6 Complete  
**Next:** Phase 7 PostgreSQL + dbt + Power BI + CI/CD

*Second year CS student building this to understand how production analytics systems actually work. Building in phases rather than a fixed schedule - shipping each layer properly before moving to the next.*

Last updated: March 2026