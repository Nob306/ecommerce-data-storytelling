"""
LLM Narrative Generator - turns root cause results into plain English summaries.

Uses Groq's free API (Llama 3 model) to generate analyst-style briefings
from structured RootCauseResult data.

Results are cached to data/insights/narratives.json so API calls only happen
once per anomaly. Re-running the narrator skips already-generated narratives.

Usage:
    python -m src.narratives.narrator

Requires:
    GROQ_API_KEY in .env file (get free key at console.groq.com)
"""

import json
import os
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
logger = logging.getLogger(__name__)

NARRATIVES_PATH = Path('data/insights/narratives.json')
CACHE_DIR = Path('data/cache')

# KPI display names for cleaner narrative output
KPI_DISPLAY_NAMES = {
    'total_revenue': 'Total Revenue',
    'order_count': 'Order Count',
    'units_sold': 'Units Sold',
    'active_customers': 'Active Customers',
    'revenue_per_order': 'Revenue per Order',
    'revenue_per_customer': 'Revenue per Customer',
    'items_per_order': 'Items per Order',
    'avg_unit_price': 'Average Unit Price',
    'repeat_customer_rate': 'Repeat Customer Rate',
    'product_revenue_concentration': 'Product Revenue Concentration',
    'product_return_rate': 'Product Return Rate',
    'international_revenue_share': 'International Revenue Share',
    'weekend_revenue_share': 'Weekend Revenue Share',
    'peak_hour_concentration': 'Peak Hour Concentration',
}


def build_prompt(row: pd.Series) -> str:
    """
    Build a structured prompt from a root cause result row.

    Keeps the prompt tight and specific — the LLM doesn't need
    the full dataset context, just the anomaly details and top drivers.
    """
    kpi = KPI_DISPLAY_NAMES.get(row['kpi_name'], row['kpi_name'])
    date = pd.Timestamp(row['date']).strftime('%B %d, %Y')
    direction = 'above' if row['total_deviation'] > 0 else 'below'
    deviation_pct = abs(row['total_deviation_pct'])
    severity = row['anomaly_severity'].upper()

    # Build driver context from flattened columns
    drivers = []
    for i in range(1, 4):
        dim_col = f'driver_{i}_dimension'
        seg_col = f'driver_{i}_segment'
        pct_col = f'driver_{i}_contribution_pct'
        if dim_col in row and pd.notna(row.get(dim_col)):
            drivers.append(
                f"{row[dim_col]}={row[seg_col]} "
                f"({row[pct_col]:.1f}% of deviation)"
            )

    drivers_text = ', '.join(drivers) if drivers else 'no specific segment identified'

    prompt = f"""You are a senior data analyst writing a concise briefing for a non-technical business executive.

Anomaly detected in a UK e-commerce retail dataset (Dec 2010 - Dec 2011):
- Metric: {kpi}
- Date: {date}
- Severity: {severity}
- The metric was {deviation_pct:.1f}% {direction} expected
- Top dimensional drivers: {drivers_text}

Write a 2-3 sentence business summary explaining what happened and what it likely means. 
Be specific about the drivers. Do not use jargon. Do not mention statistical methods or percentages from the drivers list - translate them into plain language.
Do not start with "I" or refer to yourself. Write in third person past tense."""

    return prompt


def generate_narrative(client: Groq, prompt: str) -> str:
    """Call Groq API and return the generated narrative."""
    response = client.chat.completions.create(
        model='llama-3.1-8b-instant',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=200,
        temperature=0.3,  # low temperature for consistent, factual output
    )
    return response.choices[0].message.content.strip()


def run_narrator(force_regenerate: bool = False):
    """
    Generate narratives for all successfully explained anomalies.

    Loads root causes from cache, skips any that already have a narrative
    unless force_regenerate=True, saves results to narratives.json.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s:%(name)s:%(message)s'
    )

    # Check API key
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print('ERROR: GROQ_API_KEY not found in .env file.')
        print('Get a free key at console.groq.com and add it to .env:')
        print('  GROQ_API_KEY=your_key_here')
        return

    client = Groq(api_key=api_key)

    # Load root causes
    rc_path = CACHE_DIR / 'root_causes.parquet'
    if not rc_path.exists():
        rc_path = Path('data/insights/root_causes.csv')
        if not rc_path.exists():
            print('ERROR: root_causes not found. Run Phase 5 first.')
            return
        rc_df = pd.read_csv(rc_path)
    else:
        rc_df = pd.read_parquet(rc_path)

    # Only generate for successfully explained anomalies
    explained = rc_df[rc_df['status'] == 'analysed'].copy()
    logger.info(f'Found {len(explained)} explained anomalies to narrate')

    # Load existing narratives
    existing = {}
    if NARRATIVES_PATH.exists() and not force_regenerate:
        with open(NARRATIVES_PATH) as f:
            existing = json.load(f)
        logger.info(f'Loaded {len(existing)} existing narratives from cache')

    narratives = dict(existing)
    generated_count = 0
    skipped_count = 0

    for _, row in explained.iterrows():
        # Create a stable key for this anomaly
        key = f"{row['kpi_name']}_{pd.Timestamp(row['date']).strftime('%Y-%m-%d')}"

        if key in narratives and not force_regenerate:
            skipped_count += 1
            continue

        try:
            prompt = build_prompt(row)
            narrative = generate_narrative(client, prompt)
            narratives[key] = {
                'kpi_name': row['kpi_name'],
                'date': str(row['date']),
                'severity': row['anomaly_severity'],
                'narrative': narrative,
                'generated_at': datetime.now().isoformat()
            }
            generated_count += 1
            logger.info(f'Generated narrative for {key}')

        except Exception as e:
            logger.error(f'Failed to generate narrative for {key}: {e}')
            narratives[key] = {
                'kpi_name': row['kpi_name'],
                'date': str(row['date']),
                'severity': row['anomaly_severity'],
                'narrative': f'Narrative generation failed: {e}',
                'generated_at': datetime.now().isoformat()
            }

    # Save
    NARRATIVES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(NARRATIVES_PATH, 'w') as f:
        json.dump(narratives, f, indent=2)

    print(f'\nNarrative generation complete:')
    print(f'  Generated: {generated_count}')
    print(f'  Skipped (cached): {skipped_count}')
    print(f'  Total: {len(narratives)}')
    print(f'  Saved to: {NARRATIVES_PATH}')


def load_narratives() -> dict:
    """Load cached narratives. Returns empty dict if not yet generated."""
    if not NARRATIVES_PATH.exists():
        return {}
    with open(NARRATIVES_PATH) as f:
        return json.load(f)


if __name__ == '__main__':
    run_narrator()