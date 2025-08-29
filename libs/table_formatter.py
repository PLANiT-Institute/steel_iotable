import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from .io_data_loader import IODataLoader

class IOTableFormatter:
    """
    Formats analysis results in Input-Output table format.
    Creates matrices showing impacts across sectors in traditional IO table style.
    """
    
    def __init__(self, io_loader: IODataLoader):
        """
        Initialize the IO Table Formatter.
        
        Args:
            io_loader: IODataLoader instance for sector information
        """
        self.io_loader = io_loader
        self.sector_codes = io_loader.get_sector_codes()
        self.sector_names = io_loader.get_sector_names()
    
    def create_impact_matrix(
        self,
        impact_results: Dict[str, float],
        matrix_title: str = "Impact Matrix",
        target_sector: str = None,
        show_top_n: int = 20
    ) -> pd.DataFrame:
        """
        Create an impact matrix in IO table format.
        
        Args:
            impact_results: Dictionary of {sector: impact_value}
            matrix_title: Title for the matrix
            target_sector: Target sector causing the impacts
            show_top_n: Number of top sectors to show
            
        Returns:
            DataFrame formatted as IO table
        """
        # Extract sector codes from impact results
        sector_impacts = {}
        
        for sector_label, impact in impact_results.items():
            # Extract sector code (before the colon)
            if ':' in sector_label:
                sector_code = sector_label.split(':')[0].strip()
                sector_name = sector_label.split(':', 1)[1].strip()
            else:
                sector_code = sector_label
                sector_name = self.io_loader.get_sector_name(sector_code)
            
            sector_impacts[sector_code] = {
                'name': sector_name,
                'impact': impact,
                'full_label': sector_label
            }
        
        # Sort by absolute impact
        sorted_sectors = sorted(
            sector_impacts.items(), 
            key=lambda x: abs(x[1]['impact']), 
            reverse=True
        )
        
        # Create matrix data
        matrix_data = []
        
        for i, (sector_code, data) in enumerate(sorted_sectors[:show_top_n]):
            row = {
                'Sector_Code': sector_code,
                'Sector_Name': data['name'][:30],  # Truncate long names
                'Impact_Value': data['impact'],
                'Impact_Abs': abs(data['impact']),
                'Rank': i + 1
            }
            matrix_data.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(matrix_data)
        
        # Set index to sector code for IO table style
        if not df.empty:
            df = df.set_index('Sector_Code')
        
        return df
    
    def create_supply_chain_matrix(
        self,
        supply_chain_results: Dict,
        show_top_n: int = 20
    ) -> Dict[str, pd.DataFrame]:
        """
        Create supply chain impact matrices.
        
        Args:
            supply_chain_results: Results from supply chain analysis
            show_top_n: Number of top sectors to show
            
        Returns:
            Dictionary of matrices for different impact types
        """
        matrices = {}
        
        # Direct impacts matrix
        direct_impacts = supply_chain_results.get('direct_impacts', {})
        if direct_impacts:
            matrices['Direct_Impacts'] = self.create_impact_matrix(
                direct_impacts, 
                "Direct Supply Chain Impacts",
                show_top_n=show_top_n
            )
        
        # Indirect impacts matrix
        indirect_impacts = supply_chain_results.get('indirect_impacts', {})
        if indirect_impacts:
            matrices['Indirect_Impacts'] = self.create_impact_matrix(
                indirect_impacts,
                "Indirect Supply Chain Impacts", 
                show_top_n=show_top_n
            )
        
        # Total impacts matrix
        total_impacts = supply_chain_results.get('total_impacts', {})
        if total_impacts:
            matrices['Total_Impacts'] = self.create_impact_matrix(
                total_impacts,
                "Total Supply Chain Impacts",
                show_top_n=show_top_n
            )
        
        return matrices
    
    def create_import_domestic_matrix(
        self,
        import_domestic_results: Dict,
        show_top_n: int = 15
    ) -> Dict[str, pd.DataFrame]:
        """
        Create import vs domestic impact matrices.
        
        Args:
            import_domestic_results: Results from import/domestic analysis
            show_top_n: Number of top sectors to show
            
        Returns:
            Dictionary with import and domestic impact matrices
        """
        matrices = {}
        
        # Import impacts matrix
        import_impacts = import_domestic_results.get('import_impacts', {})
        if import_impacts:
            matrices['Import_Impacts'] = self.create_impact_matrix(
                import_impacts,
                "Import Impacts",
                show_top_n=show_top_n
            )
        
        # Domestic impacts matrix
        domestic_impacts = import_domestic_results.get('domestic_impacts', {})
        if domestic_impacts:
            matrices['Domestic_Impacts'] = self.create_impact_matrix(
                domestic_impacts,
                "Domestic Impacts",
                show_top_n=show_top_n
            )
        
        # Combined comparison matrix
        if import_impacts and domestic_impacts:
            comparison_data = []
            
            # Get all sectors from both impacts
            all_sectors = set()
            for sector in import_impacts.keys():
                if ':' in sector:
                    all_sectors.add(sector.split(':')[0].strip())
            for sector in domestic_impacts.keys():
                if ':' in sector:
                    all_sectors.add(sector.split(':')[0].strip())
            
            for sector_code in all_sectors:
                # Find matching entries
                import_value = 0
                domestic_value = 0
                sector_name = self.io_loader.get_sector_name(sector_code)
                
                for sector_label, value in import_impacts.items():
                    if sector_label.startswith(sector_code + ':'):
                        import_value = value
                        break
                
                for sector_label, value in domestic_impacts.items():
                    if sector_label.startswith(sector_code + ':'):
                        domestic_value = value
                        break
                
                total_impact = abs(import_value) + abs(domestic_value)
                if total_impact > 0.01:  # Threshold for inclusion
                    comparison_data.append({
                        'Sector_Code': sector_code,
                        'Sector_Name': sector_name[:25],
                        'Import_Impact': import_value,
                        'Domestic_Impact': domestic_value,
                        'Total_Impact': import_value + domestic_value,
                        'Import_Share': abs(import_value) / total_impact if total_impact > 0 else 0,
                        'Domestic_Share': abs(domestic_value) / total_impact if total_impact > 0 else 0
                    })
            
            # Sort by total impact
            comparison_data.sort(key=lambda x: abs(x['Total_Impact']), reverse=True)
            
            if comparison_data:
                comparison_df = pd.DataFrame(comparison_data[:show_top_n])
                matrices['Import_Domestic_Comparison'] = comparison_df.set_index('Sector_Code')
        
        return matrices
    
    def create_comprehensive_summary_matrix(
        self,
        comprehensive_results: Dict
    ) -> pd.DataFrame:
        """
        Create a comprehensive summary matrix showing all impact types.
        
        Args:
            comprehensive_results: Results from comprehensive analysis
            
        Returns:
            Summary matrix DataFrame
        """
        summary_data = []
        
        # Get different impact types
        value_added = comprehensive_results.get('value_added_analysis', {}).get('sectoral_value_added', {})
        production = comprehensive_results.get('production_analysis', {}).get('sectoral_production', {})
        employment = comprehensive_results.get('employment_analysis', {}).get('sectoral_employment', {})
        environmental = comprehensive_results.get('environmental_analysis', {}).get('sectoral_co2_impact', {})
        
        # Get all sectors
        all_sectors = set()
        for impact_dict in [value_added, production, employment, environmental]:
            for sector_label in impact_dict.keys():
                if ':' in sector_label:
                    all_sectors.add(sector_label.split(':')[0].strip())
                else:
                    all_sectors.add(sector_label)
        
        # Create summary for each sector
        for sector_code in list(all_sectors)[:20]:  # Top 20 sectors
            sector_name = self.io_loader.get_sector_name(sector_code)
            
            # Find values for this sector
            va_impact = 0
            prod_impact = 0
            emp_impact = 0
            co2_impact = 0
            
            # Search in each impact type
            for sector_label, value in value_added.items():
                if sector_label.startswith(sector_code + ':') or sector_label == sector_code:
                    va_impact = value
                    break
            
            for sector_label, value in production.items():
                if sector_label.startswith(sector_code + ':') or sector_label == sector_code:
                    prod_impact = value
                    break
            
            for sector_label, value in employment.items():
                if sector_label.startswith(sector_code + ':') or sector_label == sector_code:
                    emp_impact = value
                    break
            
            for sector_label, value in environmental.items():
                if sector_label.startswith(sector_code + ':') or sector_label == sector_code:
                    co2_impact = value
                    break
            
            # Only include sectors with significant impacts
            total_significance = abs(va_impact) + abs(prod_impact) + abs(emp_impact) + abs(co2_impact)
            
            if total_significance > 0.1:
                summary_data.append({
                    'Sector_Code': sector_code,
                    'Sector_Name': sector_name[:25],
                    'Value_Added_Impact': va_impact,
                    'Production_Impact': prod_impact,
                    'Employment_Impact': emp_impact,
                    'CO2_Impact_1000tons': co2_impact,
                    'Total_Significance': total_significance
                })
        
        # Sort by total significance
        summary_data.sort(key=lambda x: x['Total_Significance'], reverse=True)
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            return summary_df.set_index('Sector_Code')
        else:
            return pd.DataFrame()
    
    def create_employment_matrix(
        self,
        employment_results: Dict,
        show_top_n: int = 15
    ) -> pd.DataFrame:
        """
        Create employment impact matrix.
        
        Args:
            employment_results: Employment analysis results
            show_top_n: Number of sectors to show
            
        Returns:
            Employment impact matrix
        """
        employment_impacts = employment_results.get('sectoral_employment', {})
        
        if not employment_impacts:
            return pd.DataFrame()
        
        employment_data = []
        
        for sector, jobs in employment_impacts.items():
            # Extract sector info
            if ':' in sector:
                sector_parts = sector.split(':', 1)
                sector_code = sector_parts[0].strip()
                sector_name = sector_parts[1].strip()[:30]
            else:
                sector_code = sector
                sector_name = sector[:30]
            
            employment_data.append({
                'Sector_Code': sector_code,
                'Sector_Name': sector_name,
                'Employment_Change': jobs,
                'Employment_Abs': abs(jobs)
            })
        
        # Sort by absolute employment change
        employment_data.sort(key=lambda x: x['Employment_Abs'], reverse=True)
        
        # Create DataFrame
        if employment_data:
            emp_df = pd.DataFrame(employment_data[:show_top_n])
            return emp_df.set_index('Sector_Code')
        else:
            return pd.DataFrame()
    
    def display_matrix_table(
        self,
        matrix: pd.DataFrame,
        title: str,
        max_rows: int = 20,
        number_format: str = '{:,.1f}'
    ):
        """
        Display a matrix in formatted table style.
        
        Args:
            matrix: DataFrame to display
            title: Title for the table
            max_rows: Maximum rows to display
            number_format: Format string for numbers
        """
        if matrix.empty:
            print(f"\n{title}: No data available")
            return
        
        print(f"\n{'='*80}")
        print(f"{title.upper()}")
        print(f"{'='*80}")
        
        # Limit rows
        display_matrix = matrix.head(max_rows)
        
        # Format numeric columns
        formatted_matrix = display_matrix.copy()
        for col in formatted_matrix.columns:
            if formatted_matrix[col].dtype in ['float64', 'float32', 'int64', 'int32']:
                formatted_matrix[col] = formatted_matrix[col].apply(
                    lambda x: number_format.format(x) if pd.notna(x) else 'N/A'
                )
        
        # Display with proper alignment
        print(formatted_matrix.to_string(
            max_rows=max_rows,
            max_cols=10,
            col_space=15,
            justify='right'
        ))
        
        if len(matrix) > max_rows:
            print(f"\n... showing top {max_rows} of {len(matrix)} sectors")
        
        print(f"{'='*80}")
    
    def export_matrices_to_excel(
        self,
        matrices: Dict[str, pd.DataFrame],
        filename: str,
        target_sector: str = None,
        demand_change: float = None
    ):
        """
        Export matrices to Excel file in IO table format.
        
        Args:
            matrices: Dictionary of matrices to export
            filename: Output Excel filename
            target_sector: Target sector for metadata
            demand_change: Demand change amount for metadata
        """
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                
                # Write summary sheet
                summary_data = {
                    'Analysis_Type': list(matrices.keys()),
                    'Sectors_Analyzed': [len(df) for df in matrices.values()],
                    'Max_Impact': [df.iloc[:, -1].max() if not df.empty else 0 for df in matrices.values()],
                    'Min_Impact': [df.iloc[:, -1].min() if not df.empty else 0 for df in matrices.values()]
                }
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Write each matrix to separate sheet
                for sheet_name, matrix in matrices.items():
                    if not matrix.empty:
                        # Clean sheet name for Excel compatibility
                        clean_sheet_name = sheet_name.replace('/', '_')[:31]
                        matrix.to_excel(writer, sheet_name=clean_sheet_name)
                
                # Add metadata sheet
                if target_sector or demand_change:
                    metadata = pd.DataFrame({
                        'Parameter': ['Target_Sector', 'Demand_Change', 'Analysis_Date'],
                        'Value': [
                            target_sector or 'N/A',
                            f"{demand_change:,.0f} billion won" if demand_change else 'N/A',
                            pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                        ]
                    })
                    metadata.to_excel(writer, sheet_name='Metadata', index=False)
            
            print(f"\nMatrices exported to: {filename}")
            
        except Exception as e:
            print(f"Error exporting to Excel: {str(e)}")
    
    def create_full_analysis_tables(
        self,
        comprehensive_results: Dict,
        show_top_n: int = 20
    ) -> Dict[str, pd.DataFrame]:
        """
        Create complete set of analysis tables from comprehensive results.
        
        Args:
            comprehensive_results: Complete analysis results
            show_top_n: Number of top sectors to show in each table
            
        Returns:
            Dictionary of all analysis tables
        """
        all_matrices = {}
        
        # Supply chain matrices
        supply_chain = comprehensive_results.get('supply_chain_analysis', {})
        if supply_chain:
            supply_matrices = self.create_supply_chain_matrix(supply_chain, show_top_n)
            all_matrices.update(supply_matrices)
        
        # Import/domestic matrices
        import_domestic = comprehensive_results.get('import_domestic_analysis', {})
        if import_domestic:
            import_matrices = self.create_import_domestic_matrix(import_domestic, show_top_n)
            all_matrices.update(import_matrices)
        
        # Employment matrix
        employment = comprehensive_results.get('employment_analysis', {})
        if employment:
            emp_matrix = self.create_employment_matrix(employment, show_top_n)
            if not emp_matrix.empty:
                all_matrices['Employment_Impacts'] = emp_matrix
        
        # Comprehensive summary matrix
        comprehensive_analysis = comprehensive_results.get('comprehensive_analysis', {})
        if comprehensive_analysis:
            summary_matrix = self.create_comprehensive_summary_matrix(comprehensive_analysis)
            if not summary_matrix.empty:
                all_matrices['Comprehensive_Summary'] = summary_matrix
        
        return all_matrices