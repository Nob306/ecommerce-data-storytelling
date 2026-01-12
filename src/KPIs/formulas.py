"""
Formula parsing and execution for KPI calculations.

This module safely parses and executes formula strings from kpis.yaml.
Supports basic operations: sum, count, avg, min, max, and arithmetic.
"""

import pandas as pd
import re
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


class FormulaParser:
    """Parses and executes formula strings safely."""
    
    ALLOWED_FUNCTIONS = {
        'sum', 'count', 'avg', 'mean', 'min', 'max',  #defines the allowed forumulas 
        'distinct', 'nunique'
    }
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialise parser with a DataFrame.

        """
        self.df = df
    
    def parse_and_execute(self, formula: str) -> float:
        """
        Parse and execute a formula string.
        
        """
        formula = formula.strip()
        logger.debug(f"Parsing formula: {formula}")
        
        if self._is_aggregate_function(formula):
            return self._execute_aggregate(formula)
        elif self._is_ratio_formula(formula):
            return self._execute_ratio(formula)
        else:
            raise ValueError(f"Unsupported formula pattern: {formula}")
    
    def _is_aggregate_function(self, formula: str) -> bool:
        """Check if formula is a simple aggregate like sum(...) or count(...)"""
        pattern = r'^(sum|count|avg|mean|min|max|nunique)\('
        return bool(re.match(pattern, formula, re.IGNORECASE))
    
    def _is_ratio_formula(self, formula: str) -> bool:
        """Check if formula is a ratio like metric1 / metric2"""
        return '/' in formula
    
    def _execute_aggregate(self, formula: str) -> float:
        """
        Execute an aggregate function.
        
        Examples:
            sum(Quantity * UnitPrice)
            count(distinct InvoiceNo)
            avg(UnitPrice)
        """
        match = re.match(r'(\w+)\((.*)\)', formula, re.IGNORECASE)
        if not match:
            raise ValueError(f"Invalid aggregate formula: {formula}")
        
        func_name = match.group(1).lower()
        args = match.group(2).strip()
        
        if func_name not in self.ALLOWED_FUNCTIONS:
            raise ValueError(f"Function '{func_name}' not allowed. Use one of: {self.ALLOWED_FUNCTIONS}")
        
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
    
    def _execute_sum(self, expression: str) -> float:
        """
        Execute sum calculation.
        
        Examples:
            "Quantity * UnitPrice" -> sum of all transaction values
            "Quantity" -> sum of all quantities
        """
        if '*' in expression:
            parts = [p.strip() for p in expression.split('*')]
            if len(parts) != 2:
                raise ValueError(f"Complex expressions not supported: {expression}")
            
            col1, col2 = parts
            if col1 not in self.df.columns or col2 not in self.df.columns:
                raise ValueError(f"Column not found: {col1} or {col2}")
            
            result = (self.df[col1] * self.df[col2]).sum()
        else:
            # Simple sum: "Quantity"
            col = expression.strip()
            if col not in self.df.columns:
                raise ValueError(f"Column not found: {col}")
            
            result = self.df[col].sum()
        
        return float(result)
    
    def _execute_count(self, expression: str) -> float:
        """
        Execute count calculation.
        
        Examples:
            "InvoiceNo" -> count of all rows
            "distinct InvoiceNo" -> count of unique invoices
        """
        if 'distinct' in expression.lower():
            return self._execute_distinct_count(expression)
        
        col = expression.strip()
        if col not in self.df.columns:
            raise ValueError(f"Column not found: {col}")
        
        return float(self.df[col].count())
    
    def _execute_distinct_count(self, expression: str) -> float:

        col = re.sub(r'distinct\s+', '', expression, flags=re.IGNORECASE).strip()
    
        if col not in self.df.columns:
            raise ValueError(f"Column not found: {col}")
    
        return float(self.df[col].nunique())
    
    def _execute_avg(self, expression: str) -> float:
        """
        Execute average calculation.
        
        """
        if '*' in expression:
            parts = [p.strip() for p in expression.split('*')]
            if len(parts) != 2:
                raise ValueError(f"Complex expressions not supported: {expression}")
            
            col1, col2 = parts
            if col1 not in self.df.columns or col2 not in self.df.columns:
                raise ValueError(f"Column not found: {col1} or {col2}")
            
            result = (self.df[col1] * self.df[col2]).mean()
        else:
            col = expression.strip()
            if col not in self.df.columns:
                raise ValueError(f"Column not found: {col}")
            
            result = self.df[col].mean()
        
        return float(result)
    
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
    
    def _execute_ratio(self, formula: str) -> float:
        """
        Execute ratio calculation (metric1 / metric2).
        
        This is used for derived metrics like:
            "total_revenue / order_count" (revenue per order)
        
        Note: For now, this requires the numerator and denominator
        to be other formulas or column names.
        """
        parts = formula.split('/')
        if len(parts) != 2:
            raise ValueError(f"Invalid ratio formula: {formula}")
        
        numerator = parts[0].strip()
        denominator = parts[1].strip()
        
        # this is simplified - Week 4 will handle cross-KPI dependencies
        num_value = self._evaluate_simple_expression(numerator)
        den_value = self._evaluate_simple_expression(denominator)
        
        if den_value == 0:
            logger.warning(f"Division by zero in formula: {formula}")
            return 0.0
        
        return float(num_value / den_value)
    
    def _evaluate_simple_expression(self, expr: str) -> float:
        """
        Evaluate a simple expression (column name or aggregate).
        
        Used for ratio calculations.
        """
        if self._is_aggregate_function(expr):
            return self._execute_aggregate(expr)
        elif expr in self.df.columns:
            return float(self.df[expr].sum())
        else:
            # try to parse as a number
            try:
                return float(expr)
            except ValueError:
                raise ValueError(f"Cannot evaluate expression: {expr}")


def calculate_kpi_value(df: pd.DataFrame, formula: str) -> float:
    """
    Convenience function to calculate a KPI value.
    
    """
    parser = FormulaParser(df)
    return parser.parse_and_execute(formula)

#for testing

if __name__ == "__main__":
    # Sameple data
    sample_data = {
        'InvoiceNo': ['001', '001', '002', '003'],
        'Quantity': [2, 3, 1, 5],
        'UnitPrice': [10.0, 15.0, 20.0, 5.0],
        'CustomerID': ['A', 'A', 'B', 'C']
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