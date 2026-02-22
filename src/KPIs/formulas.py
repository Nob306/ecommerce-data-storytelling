"""
Formula parsing and execution for KPI calculations.

This module safely parses and executes formula strings from kpis.yaml.
Supports basic operations: sum, count, avg, min, max, arithmetic,
and conditional filtering with where/with clauses.
"""

import pandas as pd
import re
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


class FormulaParser:
    """Parses and executes formula strings safely."""
    
    ALLOWED_FUNCTIONS = {
        'sum', 'count', 'avg', 'mean', 'min', 'max',
        'distinct', 'nunique'
    }
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialise parser with a DataFrame.
        """
        self.df = df
    
    # =========================================================================
    # DERIVED COLUMNS
    # =========================================================================

    def _add_derived_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add derived columns needed for conditional filtering.

        Creates a working copy of the DataFrame with:
          - TransactionValue: Quantity * UnitPrice (alias for 'revenue' in formulas)
          - DayOfWeek: Day name derived from InvoiceDate (e.g. 'Saturday')

        We work on a copy so the original DataFrame is never mutated.
        """
        df = df.copy()

        # TransactionValue is the per-row revenue figure.
        # Formulas reference 'revenue' which maps to this column.
        if 'TransactionValue' not in df.columns:
            df['TransactionValue'] = df['Quantity'] * df['UnitPrice']

        # DayOfWeek is needed for weekend_revenue_share.
        # InvoiceDate is already parsed as datetime by ingestion.py.
        if 'DayOfWeek' not in df.columns:
            df['DayOfWeek'] = df['InvoiceDate'].dt.day_name()

        return df

    # =========================================================================
    # TOP-LEVEL DISPATCH
    # =========================================================================

    def parse_and_execute(self, formula: str, calculated_kpis: dict = None) -> float:
        """
        Parse and execute a formula string.

        Ratio check runs BEFORE aggregate check because some formulas like
        'sum(Quantity) / order_count' contain both a '/' and start with 'sum('.
        Checking ratio first ensures the division is not swallowed by the
        aggregate parser.
        """
        formula = formula.strip()
        logger.debug(f"Parsing formula: {formula}")

        if self._is_ratio_formula(formula):
            return self._execute_ratio(formula, calculated_kpis)
        elif self._is_aggregate_function(formula):
            return self._execute_aggregate(formula)
        else:
            raise ValueError(f"Unsupported formula pattern: {formula}")

    # =========================================================================
    # PATTERN DETECTION
    # =========================================================================

    def _is_aggregate_function(self, formula: str) -> bool:
        """Check if formula starts with a known aggregate function."""
        pattern = r'^(sum|count|avg|mean|min|max|nunique)\('
        return bool(re.match(pattern, formula, re.IGNORECASE))

    def _is_ratio_formula(self, formula: str) -> bool:
        """Check if formula is a ratio like metric1 / metric2."""
        return '/' in formula

    def _has_condition(self, args: str) -> bool:
        """Check if aggregate args contain a where/with filter clause."""
        return bool(re.search(r'\b(where|with)\b', args, re.IGNORECASE))

    # =========================================================================
    # AGGREGATE EXECUTION
    # =========================================================================

    def _execute_aggregate(self, formula: str) -> float:
        """
        Execute an aggregate function, with or without a condition.

        Examples:
            sum(Quantity * UnitPrice)
            count(distinct InvoiceNo)
            sum(revenue where Country != 'United Kingdom')
            count(InvoiceNo with Quantity < 0)
        """
        match = re.match(r'(\w+)\((.*)\)$', formula, re.IGNORECASE | re.DOTALL)
        if not match:
            raise ValueError(f"Invalid aggregate formula: {formula}")

        func_name = match.group(1).lower()
        args = match.group(2).strip()

        if func_name not in self.ALLOWED_FUNCTIONS:
            raise ValueError(f"Function '{func_name}' not allowed.")

        # Route to conditional or standard execution
        if self._has_condition(args):
            return self._execute_conditional_aggregate(func_name, args)

        if 'distinct' in args.lower():
            return self._execute_distinct_count(args)
        if func_name == 'sum':
            return self._execute_sum(args)
        elif func_name in ['count', 'nunique']:
            return self._execute_count(args)
        elif func_name in ['avg', 'mean']:
            return self._execute_avg(args)
        elif func_name == 'min':
            return self._execute_min(args)
        elif func_name == 'max':
            return self._execute_max(args)
        else:
            raise ValueError(f"Unsupported function: {func_name}")

    # =========================================================================
    # CONDITIONAL AGGREGATION
    # =========================================================================

    def _execute_conditional_aggregate(self, func_name: str, args: str) -> float:
        """
        Execute an aggregate with a where/with filter condition.

        Handles three formula shapes:
          1. sum(revenue where Country != 'United Kingdom')
               → filter rows, then sum TransactionValue
          2. sum(revenue where DayOfWeek in ['Saturday', 'Sunday'])
               → filter rows, then sum TransactionValue
          3. count(InvoiceNo with Quantity < 0)
               → filter rows by condition on one column, count another

        The keyword 'where' is used when the condition column differs from
        what is being aggregated. 'with' is used similarly in our yaml.
        Both are treated identically here.
        """
        # Split on 'where' or 'with' (case-insensitive)
        split = re.split(r'\b(where|with)\b', args, maxsplit=1, flags=re.IGNORECASE)
        if len(split) < 3:
            raise ValueError(f"Could not parse conditional args: {args}")

        target = split[0].strip()    # What to aggregate, e.g. 'revenue' or 'InvoiceNo'
        condition = split[2].strip() # The filter, e.g. "Country != 'United Kingdom'"

        # Add derived columns (DayOfWeek, TransactionValue) to a working copy
        enriched_df = self._add_derived_columns(self.df)

        # Apply the filter condition to get a subset of rows
        filtered_df = self._apply_condition(enriched_df, condition)

        # Resolve 'revenue' alias → TransactionValue
        if target.lower() == 'revenue':
            target = 'TransactionValue'

        # Execute the aggregate on the filtered subset
        if func_name == 'sum':
            if target not in filtered_df.columns:
                raise ValueError(f"Column not found after filtering: {target}")
            return float(filtered_df[target].sum())

        elif func_name in ['count', 'nunique']:
            if target not in filtered_df.columns:
                raise ValueError(f"Column not found after filtering: {target}")
            return float(filtered_df[target].nunique())

        elif func_name in ['avg', 'mean']:
            if target not in filtered_df.columns:
                raise ValueError(f"Column not found after filtering: {target}")
            return float(filtered_df[target].mean())

        else:
            raise ValueError(f"Unsupported function in conditional aggregate: {func_name}")

    def _apply_condition(self, df: pd.DataFrame, condition: str) -> pd.DataFrame:
        """
        Apply a filter condition string to a DataFrame and return filtered rows.

        Supported condition shapes:
          - Column != 'value'          →  inequality string match
          - Column < 0                 →  numeric comparison
          - Column in ['A', 'B']       →  membership test
          - Column > N (numeric)       →  used for orders > 1 (handled separately)

        The 'orders > 1' case for repeat_customer_rate is NOT handled here —
        that KPI requires a groupby and is caught before reaching this method.
        """
        condition = condition.strip()

        # Case 1: 'in [...]' membership test
        # e.g. DayOfWeek in ['Saturday', 'Sunday']
        in_match = re.match(r"(\w+)\s+in\s+\[(.+)\]", condition, re.IGNORECASE)
        if in_match:
            col = in_match.group(1).strip()
            values_raw = in_match.group(2)
            # Parse the list values, stripping quotes and whitespace
            values = [v.strip().strip("'\"") for v in values_raw.split(',')]
            if col not in df.columns:
                raise ValueError(f"Column not found for filter: {col}")
            return df[df[col].isin(values)]

        # Case 2: '!=' inequality
        # e.g. Country != 'United Kingdom'
        neq_match = re.match(r"(\w+)\s*!=\s*'?([^']+)'?", condition, re.IGNORECASE)
        if neq_match:
            col = neq_match.group(1).strip()
            val = neq_match.group(2).strip().strip("'\"")
            if col not in df.columns:
                raise ValueError(f"Column not found for filter: {col}")
            return df[df[col] != val]

        # Case 3: numeric comparison '<', '>', '<=', '>='
        # e.g. Quantity < 0
        num_match = re.match(r"(\w+)\s*(<=|>=|<|>)\s*(-?\d+\.?\d*)", condition, re.IGNORECASE)
        if num_match:
            col = num_match.group(1).strip()
            op = num_match.group(2).strip()
            val = float(num_match.group(3))
            if col not in df.columns:
                raise ValueError(f"Column not found for filter: {col}")
            if op == '<':
                return df[df[col] < val]
            elif op == '>':
                return df[df[col] > val]
            elif op == '<=':
                return df[df[col] <= val]
            elif op == '>=':
                return df[df[col] >= val]

        raise ValueError(f"Could not parse condition: {condition}")

    # =========================================================================
    # STANDARD AGGREGATES (no conditions)
    # =========================================================================

    def _execute_sum(self, expression: str) -> float:
        """Execute sum calculation."""
        if '*' in expression:
            parts = [p.strip() for p in expression.split('*')]
            if len(parts) != 2:
                raise ValueError(f"Complex expressions not supported: {expression}")
            col1, col2 = parts
            if col1 not in self.df.columns or col2 not in self.df.columns:
                raise ValueError(f"Column not found: {col1} or {col2}")
            return float((self.df[col1] * self.df[col2]).sum())
        else:
            col = expression.strip()
            if col not in self.df.columns:
                raise ValueError(f"Column not found: {col}")
            return float(self.df[col].sum())

    def _execute_count(self, expression: str) -> float:
        """Execute count calculation."""
        if 'distinct' in expression.lower():
            return self._execute_distinct_count(expression)
        col = expression.strip()
        if col not in self.df.columns:
            raise ValueError(f"Column not found: {col}")
        return float(self.df[col].count())

    def _execute_distinct_count(self, expression: str) -> float:
        """Execute distinct count calculation."""
        col = re.sub(r'distinct\s+', '', expression, flags=re.IGNORECASE).strip()
        if col not in self.df.columns:
            raise ValueError(f"Column not found: {col}")
        return float(self.df[col].nunique())

    def _execute_avg(self, expression: str) -> float:
        """Execute average calculation."""
        if '*' in expression:
            parts = [p.strip() for p in expression.split('*')]
            col1, col2 = parts
            if col1 not in self.df.columns or col2 not in self.df.columns:
                raise ValueError(f"Column not found: {col1} or {col2}")
            return float((self.df[col1] * self.df[col2]).mean())
        else:
            col = expression.strip()
            if col not in self.df.columns:
                raise ValueError(f"Column not found: {col}")
            return float(self.df[col].mean())

    def _execute_min(self, expression: str) -> float:
        """Execute minimum calculation."""
        col = expression.strip()
        if col not in self.df.columns:
            raise ValueError(f"Column not found: {col}")
        return float(self.df[col].min())

    def _execute_max(self, expression: str) -> float:
        """Execute maximum calculation."""
        col = expression.strip()
        if col not in self.df.columns:
            raise ValueError(f"Column not found: {col}")
        return float(self.df[col].max())

    # =========================================================================
    # RATIO EXECUTION
    # =========================================================================

    def _execute_ratio(self, formula: str, calculated_kpis: dict = None) -> float:
        """
        Execute ratio calculation (metric1 / metric2).

        Splits on '/' and evaluates each side independently.
        Each side can be a previously calculated KPI name, an aggregate
        function, a column name, or a plain number.
        """
        parts = formula.split('/')
        if len(parts) != 2:
            raise ValueError(f"Invalid ratio formula: {formula}")

        numerator = parts[0].strip()
        denominator = parts[1].strip()

        num_value = self._evaluate_simple_expression(numerator, calculated_kpis)
        den_value = self._evaluate_simple_expression(denominator, calculated_kpis)

        if den_value == 0:
            logger.warning(f"Division by zero in formula: {formula}")
            return 0.0

        return float(num_value / den_value)

    def _evaluate_simple_expression(self, expr: str, calculated_kpis: dict = None) -> float:
        """
        Evaluate one side of a ratio.

        Resolution order:
          1. Previously calculated KPI (e.g. 'total_revenue')
          2. Aggregate function (e.g. 'sum(Quantity)')
          3. Column name (falls back to sum of that column)
          4. Plain number
        """
        expr = expr.strip()

        if calculated_kpis and expr in calculated_kpis:
            return float(calculated_kpis[expr])

        if self._is_aggregate_function(expr):
            return self._execute_aggregate(expr)

        if expr in self.df.columns:
            return float(self.df[expr].sum())

        try:
            return float(expr)
        except ValueError:
            raise ValueError(f"Cannot evaluate expression: {expr}")


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def calculate_kpi_value(df: pd.DataFrame, formula: str) -> float:
    """Convenience function to calculate a single KPI value."""
    parser = FormulaParser(df)
    return parser.parse_and_execute(formula)


# =============================================================================
# TESTS
# =============================================================================

if __name__ == "__main__":
    sample_data = {
        'InvoiceNo': ['001', '001', '002', '003', 'C004'],
        'InvoiceDate': pd.to_datetime([
            '2011-01-01 10:00', '2011-01-01 10:00',
            '2011-01-07 14:00', '2011-01-08 09:00', '2011-01-08 11:00'
        ]),
        'Quantity': [2, 3, 1, 5, -1],
        'UnitPrice': [10.0, 15.0, 20.0, 5.0, 10.0],
        'CustomerID': ['A', 'A', 'B', 'C', 'A'],
        'Country': ['United Kingdom', 'United Kingdom', 'Germany', 'United Kingdom', 'United Kingdom']
    }
    df = pd.DataFrame(sample_data)

    print("Sample Data:")
    print(df)
    print("\n" + "="*50)

    test_formulas = [
        ("sum(Quantity * UnitPrice)", "Total Revenue"),
        ("count(distinct InvoiceNo)", "Unique Orders"),
        ("avg(UnitPrice)", "Average Price"),
        ("sum(Quantity)", "Total Units"),
        ("sum(Quantity * UnitPrice) / count(distinct InvoiceNo)", "Revenue Per Order"),
        ("count(InvoiceNo with Quantity < 0) / count(distinct InvoiceNo)", "Return Rate"),
        ("sum(revenue where Country != 'United Kingdom') / sum(Quantity * UnitPrice)", "International Share"),
        ("sum(revenue where DayOfWeek in ['Saturday', 'Sunday']) / sum(Quantity * UnitPrice)", "Weekend Share"),
    ]

    parser = FormulaParser(df)

    for formula, description in test_formulas:
        try:
            result = parser.parse_and_execute(formula)
            print(f"{description}:")
            print(f"  Formula: {formula}")
            print(f"  Result: {result}")
            print()
        except Exception as e:
            print(f"{description}: ERROR - {e}\n")