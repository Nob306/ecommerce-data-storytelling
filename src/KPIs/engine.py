"""
KPI Computation Engine - calculates all KPIs dynamically from config

This is the main engine that orchestrates KPI calculation.
It reads the config, applies formulas, and stores results.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

from src.kpis.registry import KPIRegistry
from src.kpis.formulas import FormulaParser
from src.data.ingestion import DataLoader

logger = logging.getLogger(__name__)


class KPIEngine:
    """Main engine for KPI calculation."""
    
    def __init__(self, config_path: str = "config/kpis.yaml"):
        """
        Initialize KPI engine.
        
        """
        self.registry = KPIRegistry(config_path)
        self.results = {}
    
    def calculate_kpi(self, kpi_name: str, df: pd.DataFrame, calculated_kpis: dict = None) -> Optional[float]:
        """ Calulation of KPIs """

        formula = self.registry.get_formula(kpi_name)
        
        if not formula:
            logger.error(f"No formula found for KPI: {kpi_name}")
            return None
        
        try:
            parser = FormulaParser(df)
            value = parser.parse_and_execute(formula, calculated_kpis=calculated_kpis)  # ← Pass calculated_kpis
            logger.debug(f"Calculated {kpi_name}: {value}")
            return value
        except Exception as e:
            logger.error(f"Error calculating {kpi_name}: {e}")
            return None
    
    def calculate_all(self, df: pd.DataFrame, cadence: Optional[str] = None) -> Dict[str, float]:
        """
        
        Calculate all KPIs
        
        
        """

        results = {}
        
        # Get KPIs to calculate
        if cadence:
            kpi_names = self.registry.list_kpis_by_cadence(cadence)
        else:
            kpi_names = self.registry.list_kpis()
        
        logger.info(f"Calculating {len(kpi_names)} KPIs...")
        
        for kpi_name in kpi_names:
            value = self.calculate_kpi(kpi_name, df, calculated_kpis=results)  
            if value is not None:
                results[kpi_name] = value
        
        self.results = results
        logger.info(f"Successfully calculated {len(results)}/{len(kpi_names)} KPIs")
        
        return results
    
    def calculate_by_time_window(
        self, 
        df: pd.DataFrame, 
        date_column: str = 'InvoiceDate',
        window: str = 'D'
    ) -> pd.DataFrame:
        """
        Calculate KPIs for each time window.
        
        Args:
            df: DataFrame with transaction data
            date_column: Name of date column
            window: Pandas offset string ('D' for daily, 'W' for weekly)
            
        Returns:
            DataFrame with KPIs calculated per time window
        """
        if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
            df[date_column] = pd.to_datetime(df[date_column])
        
        df_grouped = df.groupby(pd.Grouper(key=date_column, freq=window))
        
        results_list = []
        
        for date, group_df in df_grouped:
            if len(group_df) == 0:
                continue
            
            # Calculate all KPIs for this time window
            kpi_values = self.calculate_all(group_df)
            
            # Add date and KPI values
            row = {'date': date}
            row.update(kpi_values)
            results_list.append(row)
        
        results_df = pd.DataFrame(results_list)
        logger.info(f"Calculated KPIs for {len(results_df)} time periods")
        
        return results_df
    
    def save_results(
        self, 
        results: Dict[str, float],
        output_path: str = "data/processed/kpi_results.csv",
        append: bool = True
    ):
        """
        Save KPI results to CSV.
        
        Args:
            results: Dictionary of KPI results
            output_path: Where to save results
            append: If True, append to existing file; if False, overwrite
        """
        # Create results DataFrame
        results_data = {
            'timestamp': [datetime.now()],
            'calculation_date': [datetime.now().date()]
        }
        results_data.update({k: [v] for k, v in results.items()})
        
        df = pd.DataFrame(results_data)
        
        # Create output directory if needed
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save or append
        if append and output_file.exists():
            # Load existing and append
            existing_df = pd.read_csv(output_file)
            df = pd.concat([existing_df, df], ignore_index=True)
        
        df.to_csv(output_file, index=False)
        logger.info(f"Saved KPI results to {output_file}")
    
    def print_results(self, results: Optional[Dict[str, float]] = None):
        """
        Print KPI results in a readable format.
        
        Args:
            results: Optional dict of results (uses self.results if None)
        """
        if results is None:
            results = self.results
        
        if not results:
            print("No results to display")
            return
        
        print("\n" + "="*70)
        print("KPI CALCULATION RESULTS")
        print("="*70)
        print(f"Calculation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total KPIs Calculated: {len(results)}")
        print("="*70)
        
        # Group by owner
        kpi_by_owner = {}
        for kpi_name in results.keys():
            owner = self.registry.get_owner(kpi_name) or "Unknown"
            if owner not in kpi_by_owner:
                kpi_by_owner[owner] = []
            kpi_by_owner[owner].append(kpi_name)
        
        # Print by owner
        for owner in sorted(kpi_by_owner.keys()):
            print(f"\n{owner} Metrics:")
            print("-" * 70)
            
            for kpi_name in sorted(kpi_by_owner[owner]):
                value = results[kpi_name]
                kpi_def = self.registry.get_kpi(kpi_name)
                description = kpi_def.get('description', '') if kpi_def else ''
                
                # Format value based on KPI type
                if 'revenue' in kpi_name.lower() or 'price' in kpi_name.lower():
                    formatted_value = f"£{value:,.2f}"
                elif 'rate' in kpi_name.lower() or 'share' in kpi_name.lower():
                    formatted_value = f"{value:.2%}"
                else:
                    formatted_value = f"{value:,.0f}"
                
                print(f"  {kpi_name:.<45} {formatted_value}")
                if description:
                    print(f"    └─ {description}")
        
        print("\n" + "="*70)


def main():
    """Main execution function."""
    # Load data
    logger.info("Loading transaction data...")
    loader = DataLoader()
    df = loader.load_retail_data()
    
    # Initialize engine
    logger.info("Initializing KPI engine...")
    engine = KPIEngine()
    
    # Calculate all KPIs
    logger.info("Calculating KPIs...")
    results = engine.calculate_all(df)
    
    # Print results
    engine.print_results(results)
    
    # Save results
    engine.save_results(results)
    
    print("\n" + "="*70)
    print("KPI CALCULATION COMPLETE")
    print("="*70)
    print(f"Results saved to: data/processed/kpi_results.csv")
    print(f"Total KPIs calculated: {len(results)}")
    print("="*70)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()