import pandas as pd
from typing import Dict

class IOTableAnalyzer:
    def __init__(self, data_file: str = 'data/iotable_2020.xlsx'):
        """Initialize the I-O Table Analyzer with clean data structure."""
        self.data_file = data_file
        self.mapping = None
        self.coefficients = {}  # Will store A, Am, Ad
        self.load_data()
    
    def load_data(self):
        """Load mapping and all three coefficient matrices from Excel file."""
        print("Loading I-O Table data...")
        
        # Load mapping sheet
        self.mapping = pd.read_excel(self.data_file, sheet_name='basicmap')
        print(f"Loaded {len(self.mapping)} sectors from basicmap sheet")
        
        # Load direct input coefficients (A)
        df_A = pd.read_excel(self.data_file, sheet_name='directinputcoeff_A')
        self.coefficients['A'] = df_A.set_index('code')
        print(f"Loaded A (direct) coefficient matrix: {self.coefficients['A'].shape}")
        
        # Load import input coefficients (Am)
        df_Am = pd.read_excel(self.data_file, sheet_name='importinputcoeff_Am')
        self.coefficients['Am'] = df_Am.set_index('code')
        print(f"Loaded Am (import) coefficient matrix: {self.coefficients['Am'].shape}")
        
        # Load domestic coefficients (Ad)
        df_Ad = pd.read_excel(self.data_file, sheet_name='domesticinputcoeff_Ad')
        # Clean the column name if needed
        if 'code' not in df_Ad.columns:
            df_Ad = df_Ad.rename(columns={df_Ad.columns[0]: 'code'})
        self.coefficients['Ad'] = df_Ad.set_index('code')
        print(f"Loaded Ad (domestic) coefficient matrix: {self.coefficients['Ad'].shape}")
        
        # Load indirect production coefficients (I-Ad)^-1
        df_indirect_prod = pd.read_excel(self.data_file, sheet_name='indirectprodcoeff')
        self.coefficients['indirect_prod'] = df_indirect_prod.set_index('code')
        print(f"Loaded indirect production coefficient matrix: {self.coefficients['indirect_prod'].shape}")
        
        # Load indirect import coefficients
        df_indirect_import = pd.read_excel(self.data_file, sheet_name='indirectimportcoeff')
        self.coefficients['indirect_import'] = df_indirect_import.set_index('code')
        print(f"Loaded indirect import coefficient matrix: {self.coefficients['indirect_import'].shape}")
        
        # Load value-added coefficients
        df_value_added = pd.read_excel(self.data_file, sheet_name='valueaddedcoeff')
        self.coefficients['value_added'] = df_value_added.set_index('code')
        print(f"Loaded value-added coefficient matrix: {self.coefficients['value_added'].shape}")
        
        # Create code-to-product mapping dictionary with proper string formatting
        self.code_to_product = {}
        self.code_to_product_display = {}  # For display purposes
        
        # Use first coefficient matrix to check column format
        sample_coeffs = self.coefficients['A']
        
        for _, row in self.mapping.iterrows():
            original_code = row['code']
            product = row['product']
            
            # Convert code to proper format for coefficient matrix lookup
            if original_code < 1000:
                # 3-digit codes become strings with leading zero (111 -> "0111")  
                formatted_code = f"0{original_code}"
            else:
                # 4-digit codes: check if they exist as integers or strings in coefficient matrix
                if original_code in sample_coeffs.columns:
                    formatted_code = original_code  # Keep as integer
                elif str(original_code) in sample_coeffs.columns:
                    formatted_code = str(original_code)  # Convert to string
                else:
                    formatted_code = original_code  # Default to integer
            
            self.code_to_product[formatted_code] = product
            # Store display version showing the actual coefficient matrix code format
            self.code_to_product_display[formatted_code] = f"{formatted_code}: {product}"
        
        print("Data loading complete!")
    
    def get_sector_options(self) -> Dict:
        """Return all available sector codes and their products for display."""
        return self.code_to_product_display
    
    def get_sector_from_display(self, display_string: str):
        """Extract the formatted sector code from display string."""
        code_part = display_string.split(":")[0]
        # If it's a string starting with "0", keep it as string
        if code_part.startswith("0"):
            return code_part
        else:
            # Otherwise convert to integer
            return int(code_part)
    
    def calculate_direct_effects(self, target_sector, demand_change: float, coeff_type: str = 'A', quiet: bool = False) -> Dict[str, any]:
        """
        Calculate effects of demand change in target sector using specified coefficient matrix.
        
        Args:
            target_sector: Sector code (string like "0111" or integer like 2711)
            demand_change: Change in final demand (positive or negative)
            coeff_type: Type of coefficients to use
            quiet: If True, suppress print output
            
        Returns:
            Dictionary with analysis results
        """
        if target_sector not in self.code_to_product:
            raise ValueError(f"Sector {target_sector} not found in data")
        
        if coeff_type not in self.coefficients:
            raise ValueError(f"Coefficient type '{coeff_type}' not available. Choose from: {list(self.coefficients.keys())}")
        
        target_product = self.code_to_product[target_sector]
        coeff_names = {
            'A': 'Direct Total', 
            'Am': 'Direct Import', 
            'Ad': 'Direct Domestic',
            'indirect_prod': 'Indirect Production (I-Ad)⁻¹',
            'indirect_import': 'Indirect Import',
            'value_added': 'Value-Added'
        }
        
        if not quiet:
            print(f"\nAnalyzing {coeff_names[coeff_type]} effects for {target_sector}: {target_product}")
            print(f"Demand change: {demand_change:,.0f}")
            print(f"Using coefficient type: {coeff_type} ({coeff_names[coeff_type]})")
        
        # Use target_sector directly as it's already in the correct format
        selected_coeffs = self.coefficients[coeff_type]
        
        if target_sector not in selected_coeffs.columns:
            raise ValueError(f"Column for sector {target_sector} not found in {coeff_type} coefficient matrix")
        
        # Calculate direct effects: coefficient * demand_change
        direct_impacts = selected_coeffs[target_sector] * demand_change
        
        # Remove zero or near-zero impacts and NaN values
        significant_impacts = direct_impacts[(abs(direct_impacts) > 1e-6) & pd.notna(direct_impacts)]
        
        # Create results with sector names
        results = []
        for sector_code, impact in significant_impacts.items():
            if sector_code in self.code_to_product:
                results.append({
                    'sector_code': sector_code,
                    'sector_name': self.code_to_product[sector_code],
                    'impact': impact
                })
        
        # Sort by absolute impact (descending)
        results.sort(key=lambda x: abs(x['impact']), reverse=True)
        
        # Calculate summary statistics
        total_impact = sum([r['impact'] for r in results])
        
        return {
            'target_sector': target_sector,
            'target_product': target_product,
            'demand_change': demand_change,
            'coeff_type': coeff_type,
            'coeff_name': coeff_names[coeff_type],
            'impacts': results,
            'total_impact': total_impact,
            'num_affected_sectors': len(results)
        }
    
    def display_results(self, results: Dict):
        """Display analysis results in a formatted way."""
        print(f"\n{'='*60}")
        print(f"DIRECT EFFECTS ANALYSIS - {results['coeff_name'].upper()}")
        print(f"{'='*60}")
        print(f"Target Sector: {results['target_sector']} - {results['target_product']}")
        print(f"Demand Change: {results['demand_change']:,.0f}")
        print(f"Coefficient Type: {results['coeff_type']} ({results['coeff_name']})")
        print(f"Total Direct Impact: {results['total_impact']:,.2f}")
        print(f"Affected Sectors: {results['num_affected_sectors']}")
        
        print(f"\n{'Top 20 Direct Impacts:':<60}")
        print(f"{'Code':<6} {'Sector':<35} {'Impact':>15}")
        print("-" * 60)
        
        for impact in results['impacts'][:20]:
            print(f"{impact['sector_code']:<6} {impact['sector_name']:<35} {impact['impact']:>15,.2f}")
        
        if len(results['impacts']) > 20:
            print(f"\n... and {len(results['impacts']) - 20} more sectors with smaller impacts")