import pandas as pd
from typing import Dict
import os
from datetime import datetime

class IOTableAnalyzer:
    def __init__(self, data_file: str = 'data/iotable_2020.xlsx'):
        """Initialize the I-O Table Analyzer with clean data structure."""
        self.data_file = data_file
        self.mapping = None
        self.codemap = None
        self.subsectormap = None
        self.coefficients = {}  # Will store A, Am, Ad, job coefficients
        self.basic_to_subsector = {}  # Mapping from basic sector to sub-sector
        self.subsector_to_name = {}  # Mapping from sub-sector code to name
        self.load_data()
        self.load_data()
    
    def load_damageshock_data(self, damageshock_file: str = 'data/Data_V2.xlsx'):
        """Load SHOCK data from Data_V2.xlsx for scenario selection."""
        self.damageshock_file = damageshock_file
        self.damageshock_data = pd.read_excel(self.damageshock_file, sheet_name='SHOCK', engine='openpyxl')
        print(f"Loaded damageshock data: {self.damageshock_data.shape}")

    def get_shock_scenarios(self):
        """Get available shock scenarios from the SHOCK sheet."""
        if not hasattr(self, 'damageshock_data'):
            self.load_damageshock_data()

        # Get scenarios from "내역" column
        scenarios = []
        if '내역' in self.damageshock_data.columns:
            scenarios = self.damageshock_data['내역'].dropna().tolist()

        return scenarios

    def get_shock_columns(self):
        """Get available year/column options from the first row."""
        if not hasattr(self, 'damageshock_data'):
            self.load_damageshock_data()

        # Get numeric columns from first row (excluding text columns like "내역")
        numeric_columns = []
        for col in self.damageshock_data.columns:
            if isinstance(col, (int, float)) or (isinstance(col, str) and col.isdigit()):
                numeric_columns.append(col)

        return numeric_columns

    def get_shock_value(self, scenario_name: str, column_name):
        """Get specific shock value for given scenario and column."""
        if not hasattr(self, 'damageshock_data'):
            self.load_damageshock_data()

        # Find row with matching scenario
        scenario_row = self.damageshock_data[self.damageshock_data['내역'] == scenario_name]

        if scenario_row.empty:
            raise ValueError(f"Scenario '{scenario_name}' not found")

        if column_name not in self.damageshock_data.columns:
            raise ValueError(f"Column '{column_name}' not found")

        value = scenario_row.iloc[0][column_name]
        return value if pd.notna(value) else 0

    def load_hydrogen_coefficient(self, hydrocoefficient_file: str = 'data/Data_V2.xlsx'):
        """Load hydrogen coefficient data from Data_V2.xlsx for hydrogen usage analysis."""
        self.hydrogen_file = hydrocoefficient_file

        # Read the raw data to understand structure
        raw_data = pd.read_excel(self.hydrogen_file, sheet_name='생산유발계수', header=None, engine='openpyxl')

        # The data structure has sector codes in row 4 (index 4) starting from column 1
        # and category names in row 5 (index 5) starting from column 2
        # Data starts from row 6 (index 6)

        # Extract sector information from row 6 onwards
        data_rows = raw_data.iloc[6:].copy()

        # Create proper column structure
        # First column (index 0) has sector codes, second column (index 1) has sector names
        # Columns 2-5 have the coefficient values for the 4 categories
        sectors_data = []
        for i, row in data_rows.iterrows():
            if pd.notna(row.iloc[0]) and pd.notna(row.iloc[1]):  # Valid sector row
                sector_info = {
                    '부문': row.iloc[1],  # Sector name
                    'production': pd.to_numeric(row.iloc[2], errors='coerce') if pd.notna(row.iloc[2]) else 0,
                    'storage': pd.to_numeric(row.iloc[3], errors='coerce') if pd.notna(row.iloc[3]) else 0,
                    'transportation': pd.to_numeric(row.iloc[4], errors='coerce') if pd.notna(row.iloc[4]) else 0,
                    'utilization': pd.to_numeric(row.iloc[5], errors='coerce') if pd.notna(row.iloc[5]) else 0
                }
                sectors_data.append(sector_info)

        # Create the hydrogen_data DataFrame
        self.hydrogen_data = pd.DataFrame(sectors_data)
        print(f"Loaded hydrogen data: {self.hydrogen_data.shape}")
        print(f"Available sectors: {len(self.hydrogen_data)} sectors")

        # Debug: show first few rows
        if not self.hydrogen_data.empty:
            print("Sample data:")
            print(self.hydrogen_data.head())

    def get_hydrogen_categories(self):
        """Get available hydrogen categories (production, transportation, utilization, storage)."""
        if not hasattr(self, 'hydrogen_data'):
            self.load_hydrogen_coefficient()

        # Return the specific column names for hydrogen categories
        categories = ['production', 'transportation', 'utilization', 'storage']
        available_categories = [cat for cat in categories if cat in self.hydrogen_data.columns]
        return available_categories

    def get_hydrogen_sectors(self):
        """Get available sectors from hydrogen data (부문 column)."""
        if not hasattr(self, 'hydrogen_data'):
            self.load_hydrogen_coefficient()

        if '부문' in self.hydrogen_data.columns:
            return self.hydrogen_data['부문'].dropna().tolist()
        return []

    def get_hydrogen_coefficient(self, sector_name: str, category: str):
        """Get hydrogen coefficient for specific sector and category."""
        if not hasattr(self, 'hydrogen_data'):
            self.load_hydrogen_coefficient()

        # Find row with matching sector
        sector_row = self.hydrogen_data[self.hydrogen_data['부문'] == sector_name]

        if sector_row.empty:
            raise ValueError(f"Sector '{sector_name}' not found in hydrogen data")

        if category not in self.hydrogen_data.columns:
            raise ValueError(f"Category '{category}' not found in hydrogen data")

        value = sector_row.iloc[0][category]
        return value if pd.notna(value) else 0

    def calculate_hydrogen_effects(self, demand_change: float, selected_sheet: str = None, quiet: bool = False) -> Dict[str, any]:
        """
        Calculate hydrogen effects with year-based output structure using all coefficient sheets.
        Returns results with rows=sectors, columns=years(2025-2050), values=impact.
        """
        if not hasattr(self, 'hydrogen_data'):
            self.load_hydrogen_coefficient()

        if not self.hydrogen_data:
            return {
                'target_sector': 'Hydrogen Analysis',
                'target_product': 'No coefficient sheets available',
                'demand_change': demand_change,
                'coeff_type': 'hydrogen',
                'coeff_name': 'Hydrogen Year-based Analysis',
                'impacts': [],
                'total_impact': 0,
                'num_affected_sectors': 0
            }

        if not quiet:
            print(f"\nAnalyzing Hydrogen effects using all coefficient sheets")
            print(f"Demand change: {demand_change:,.0f}")
            print(f"Available sheets: {list(self.hydrogen_data.keys())}")

        # Combine data from all coefficient sheets
        all_sectors = set()
        years = []
        year_columns = []

        # First, determine the common year structure from the first available sheet
        first_sheet = list(self.hydrogen_data.keys())[0]
        first_data = self.hydrogen_data[first_sheet]

        # Extract years from the first row
        for col_idx in range(3, min(29, first_data.shape[1])):
            try:
                cell_value = first_data.iloc[0, col_idx]
                if pd.notna(cell_value):
                    year = int(float(cell_value))
                    if 2025 <= year <= 2050:
                        years.append(year)
                        year_columns.append(col_idx)
            except (ValueError, TypeError):
                continue

        if not years:
            years = list(range(2025, 2051))
            year_columns = list(range(3, min(29, first_data.shape[1])))

        # Collect all sectors from all sheets
        for sheet_name, sheet_data in self.hydrogen_data.items():
            for row_idx in range(1, min(21, sheet_data.shape[0])):
                try:
                    sector_name = sheet_data.iloc[row_idx, 0]
                    if pd.notna(sector_name) and str(sector_name).strip():
                        all_sectors.add(str(sector_name).strip())
                    else:
                        break
                except:
                    break

        sectors = sorted(list(all_sectors))

        # Calculate combined effects matrix: sectors x years (sum across all sheets)
        results_matrix = []
        for sector in sectors:
            sector_row = {'sector': sector}
            sector_total = 0

            for year, col_idx in zip(years, year_columns):
                year_total = 0

                # Sum impacts from all coefficient sheets for this sector and year
                for sheet_name, sheet_data in self.hydrogen_data.items():
                    try:
                        # Find sector row in this sheet
                        sector_row_idx = None
                        for row_idx in range(1, sheet_data.shape[0]):
                            if (pd.notna(sheet_data.iloc[row_idx, 0]) and
                                str(sheet_data.iloc[row_idx, 0]).strip() == sector):
                                sector_row_idx = row_idx
                                break

                        if sector_row_idx is not None and col_idx < sheet_data.shape[1]:
                            coefficient = sheet_data.iloc[sector_row_idx, col_idx]
                            if pd.notna(coefficient):
                                coefficient = float(coefficient)
                                impact = coefficient * demand_change
                                year_total += impact
                    except:
                        continue

                sector_row[str(year)] = year_total
                sector_total += abs(year_total)

            sector_row['total'] = sector_total
            if sector_total > 0:  # Only include sectors with non-zero impact
                results_matrix.append(sector_row)

        # Sort by total impact
        results_matrix.sort(key=lambda x: x['total'], reverse=True)

        return {
            'target_sector': 'Hydrogen Analysis',
            'target_product': f'All Coefficient Sheets ({len(self.hydrogen_data)} sheets)',
            'demand_change': demand_change,
            'selected_sheet': 'All Sheets Combined',
            'sheets_used': list(self.hydrogen_data.keys()),
            'years': years,
            'coeff_type': 'hydrogen',
            'coeff_name': f'Hydrogen Year-based Analysis (All Coefficient Sheets)',
            'impacts': results_matrix,
            'total_impact': sum([row['total'] for row in results_matrix]),
            'num_affected_sectors': len(results_matrix)
        }

    def get_hydrogen_impact_matrix(self, demand_change: float, selected_sheet: str = None) -> pd.DataFrame:
        """
        Get hydrogen impact results in matrix format: rows=sectors, columns=years(2025-2050), values=impact.
        Returns DataFrame with sectors as index and years as columns.
        """
        # Get the year-based results using all coefficient sheets
        results = self.calculate_hydrogen_effects(demand_change, selected_sheet, quiet=True)

        if not results['impacts']:
            return pd.DataFrame()

        # Convert results to DataFrame format
        impact_matrix_data = []
        for sector_data in results['impacts']:
            row_data = {'Sector': sector_data['sector']}

            # Add year columns
            for year in results['years']:
                year_str = str(year)
                if year_str in sector_data:
                    row_data[f'{year} (백만원)'] = sector_data[year_str]
                else:
                    row_data[f'{year} (백만원)'] = 0.0

            # Add total column
            row_data['Total (백만원)'] = sector_data.get('total', 0.0)
            impact_matrix_data.append(row_data)

        return pd.DataFrame(impact_matrix_data)

    def export_hydrogen_results_to_excel(self, results: Dict, output_file: str = None):
        """Export hydrogen analysis results to Excel file with matrix format as main output."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"hydrogen_impact_matrix_{timestamp}.xlsx"

        # Create output directory if it doesn't exist
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        output_path = os.path.join(output_dir, output_file)

        # Get impact matrix (main output format)
        impact_matrix = self.get_hydrogen_impact_matrix(results['demand_change'])

        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            # Main Impact Matrix sheet (rows=sectors, columns=categories, values=impact)
            impact_matrix.to_excel(writer, sheet_name='Impact_Matrix', index=False)

            # Summary sheet
            summary_data = {
                'Parameter': ['Demand Change', 'Total Sectors', 'Production Total', 'Storage Total', 'Transportation Total', 'Utilization Total', 'Overall Total'],
                'Value': [
                    results['demand_change'],
                    len(impact_matrix),
                    impact_matrix['Production (백만원)'].sum(),
                    impact_matrix['Storage (백만원)'].sum(),
                    impact_matrix['Transportation (백만원)'].sum(),
                    impact_matrix['Utilization (백만원)'].sum(),
                    impact_matrix['Total (백만원)'].sum()
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)

            # Category allocation sheet
            category_data = []
            for category, percentage in results['category_percentages'].items():
                allocated_demand = results['demand_change'] * percentage
                category_data.append({
                    'Category': category.title(),
                    'Allocation %': f"{percentage*100:.1f}%",
                    'Allocated Demand': allocated_demand
                })

            category_df = pd.DataFrame(category_data)
            category_df.to_excel(writer, sheet_name='Category_Allocation', index=False)

        print(f"Impact matrix exported to: {output_path}")
        return output_path


    def load_data(self):
        """Load mapping and all three coefficient matrices from Excel file."""
        print("Loading I-O Table data...")
        
        # Load mapping sheet
        self.mapping = pd.read_excel(self.data_file, sheet_name='basicmap')
        print(f"Loaded {len(self.mapping)} sectors from basicmap sheet")
        
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
        
        # Load job coefficients (total job creation)
        df_jobcoeff = pd.read_excel(self.data_file, sheet_name='jobcoeff')
        self.coefficients['jobcoeff'] = df_jobcoeff.set_index('code')
        print(f"Loaded job coefficient matrix: {self.coefficients['jobcoeff'].shape}")
        
        # Load direct employment coefficients
        df_directemploy = pd.read_excel(self.data_file, sheet_name='directemploycoeff')
        self.coefficients['directemploycoeff'] = df_directemploy.set_index('code')
        print(f"Loaded direct employment coefficient matrix: {self.coefficients['directemploycoeff'].shape}")
        
        # Load codemap for basic-to-subsector mapping
        self.codemap = pd.read_excel(self.data_file, sheet_name='codemap')
        print(f"Loaded codemap with {len(self.codemap)} sector mappings")
        
        # Load subsectormap for sub-sector names
        self.subsectormap = pd.read_excel(self.data_file, sheet_name='subsectormap')
        print(f"Loaded subsectormap with {len(self.subsectormap)} sub-sector names")
        
        # Create sub-sector code to name mapping
        for _, row in self.subsectormap.iterrows():
            subsector_code = row['code']
            subsector_name = row['name']
            self.subsector_to_name[subsector_code] = subsector_name
        
        print(f"Created sub-sector-to-name mapping for {len(self.subsector_to_name)} sub-sectors")
        
        # Create basic-to-subsector mapping
        for _, row in self.codemap.iterrows():
            basic_code = row['Basic']
            subsector_code = row['Sub-sector']
            
            # Format basic code consistently (same logic as main mapping)
            if basic_code < 1000:
                formatted_basic = f"0{basic_code}"
            else:
                formatted_basic = str(basic_code)
                
            # Format subsector code (typically 2-3 digit codes)
            if subsector_code < 100:
                formatted_subsector = f"0{subsector_code:02d}"  # Ensure 3 digits with leading zeros
            else:
                formatted_subsector = f"{subsector_code:03d}"
                
            self.basic_to_subsector[formatted_basic] = formatted_subsector
        
        print(f"Created basic-to-subsector mapping for {len(self.basic_to_subsector)} sectors")
        
        # Create code-to-product mapping dictionary with proper string formatting
        self.code_to_product = {}
        self.code_to_product_display = {}  # For display purposes
        
        # Use first available coefficient matrix to check column format
        sample_coeffs = next(iter(self.coefficients.values()))
        
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
        # Convert target_sector to the proper format used internally
        if isinstance(target_sector, str) and target_sector.isdigit():
            target_sector_int = int(target_sector)
        elif isinstance(target_sector, int):
            target_sector_int = target_sector
        else:
            target_sector_int = None
            
        # Check both string and integer formats
        if target_sector not in self.code_to_product and target_sector_int not in self.code_to_product:
            raise ValueError(f"Sector {target_sector} not found in data")
            
        # Use the format that exists in the mapping
        if target_sector in self.code_to_product:
            final_target_sector = target_sector
        else:
            final_target_sector = target_sector_int
        
        if coeff_type not in self.coefficients:
            raise ValueError(f"Coefficient type '{coeff_type}' not available. Choose from: {list(self.coefficients.keys())}")
        
        target_product = self.code_to_product[final_target_sector]
        coeff_names = {
            'indirect_prod': 'Domestic Production-Inducing Effect',
            'indirect_import': 'Import-Inducing Effect',
            'value_added': 'Value-Added Creation Effect',
            'jobcoeff': 'Job Creating Effect',
            'directemploycoeff': 'Direct Employment Effect'
        }
        
        if not quiet:
            print(f"\nAnalyzing {coeff_names[coeff_type]} effects for {final_target_sector}: {target_product}")
            print(f"Demand change: {demand_change:,.0f}")
            print(f"Using coefficient type: {coeff_type} ({coeff_names[coeff_type]})")
        
        # Handle job coefficients which use sub-sector mapping
        if coeff_type in ['jobcoeff', 'directemploycoeff']:
            return self._calculate_job_effects(final_target_sector, demand_change, coeff_type, coeff_names[coeff_type], quiet)
        
        # Use final_target_sector for regular coefficients 
        selected_coeffs = self.coefficients[coeff_type]
        
        if final_target_sector not in selected_coeffs.columns:
            raise ValueError(f"Column for sector {final_target_sector} not found in {coeff_type} coefficient matrix")
        
        # Calculate direct effects: coefficient * demand_change
        direct_impacts = selected_coeffs[final_target_sector] * demand_change

        # Remove zero or near-zero impacts and NaN values - optimized filtering
        mask = (abs(direct_impacts) > 1e-6) & pd.notna(direct_impacts)
        significant_impacts = direct_impacts[mask]

        # Create results with vectorized operations
        results = [
            {
                'sector_code': sector_code,
                'sector_name': self.code_to_product.get(sector_code, f'Unknown-{sector_code}'),
                'impact': impact
            }
            for sector_code, impact in significant_impacts.items()
            if sector_code in self.code_to_product
        ]

        # Sort by absolute impact (descending) - single operation
        results.sort(key=lambda x: abs(x['impact']), reverse=True)
        
        # Calculate summary statistics - optimized
        total_impact = sum(r['impact'] for r in results)
        
        return {
            'target_sector': final_target_sector,
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
    
    def _calculate_job_effects(self, target_sector, demand_change: float, coeff_type: str, coeff_name: str, quiet: bool = False) -> Dict[str, any]:
        """
        Calculate job effects using sub-sector mapping.
        Job coefficients use sub-sector codes, so we need to map basic sector to sub-sector first.
        """
        target_product = self.code_to_product[target_sector]
        
        # Convert target_sector to string format for basic_to_subsector mapping
        if isinstance(target_sector, int):
            target_sector_str = str(target_sector)
        else:
            target_sector_str = target_sector
            
        # Find the sub-sector code for this basic sector
        if target_sector_str not in self.basic_to_subsector:
            raise ValueError(f"Sub-sector mapping not found for basic sector {target_sector_str}")
        
        subsector_code = self.basic_to_subsector[target_sector_str]
        
        if not quiet:
            print(f"Basic sector {target_sector} maps to sub-sector {subsector_code}")
        
        # Get job coefficient matrix
        selected_coeffs = self.coefficients[coeff_type]
        
        # Check if sub-sector column exists in job coefficient matrix
        if subsector_code not in selected_coeffs.columns:
            raise ValueError(f"Sub-sector column {subsector_code} not found in {coeff_type} coefficient matrix")
        
        # Calculate job effects with proper unit conversion:
        # - Job coefficients: 명/10억원 (jobs per 10 billion won)
        # - Demand change: 백만원 (million won)
        job_impacts = selected_coeffs[subsector_code] * 0.001 * demand_change / 1000
   
        # Remove zero or near-zero impacts and NaN values
        significant_impacts = job_impacts[(abs(job_impacts) > 1e-6) & pd.notna(job_impacts)]
        
        # Create results with sector names (using sub-sector mapping for job results)
        results = []
        for sector_code, impact in significant_impacts.items():
            # For job coefficients, sector_code represents the sub-sector experiencing job impact
            # Use subsectormap to get proper sub-sector names
            if sector_code in self.subsector_to_name:
                sector_name = f"{self.subsector_to_name[sector_code]}"
            else:
                sector_name = f"Sub-sector {sector_code}"  # Fallback if name not found
            
            results.append({
                'sector_code': sector_code,
                'sector_name': sector_name,
                'impact': impact
            })
        
        # Sort by absolute impact (descending)
        results.sort(key=lambda x: abs(x['impact']), reverse=True)
        
        # Calculate summary statistics - optimized
        total_impact = sum(r['impact'] for r in results)
        
        return {
            'target_sector': target_sector,
            'target_product': target_product,
            'subsector_code': subsector_code,
            'demand_change': demand_change,
            'coeff_type': coeff_type,
            'coeff_name': coeff_name,
            'impacts': results,
            'total_impact': total_impact,
            'num_affected_sectors': len(results)
        }

    def create_comprehensive_scenario_table(self):
        """
        Create comprehensive scenario impact table showing totals by year and scenario.
        Returns DataFrame with scenarios as rows, years as columns, and effect totals.
        """
        if not hasattr(self, 'damageshock_data'):
            self.load_damageshock_data()

        # Get available scenarios and years
        scenarios = self.get_shock_scenarios()
        years = self.get_shock_columns()

        # Filter years to 2025-2050 range
        valid_years = [year for year in years if isinstance(year, (int, float)) and 2025 <= year <= 2050]
        valid_years = sorted(valid_years)

        # Effect types
        effect_types = [
            'Total Domestic Production-Inducing Effect',
            'Total Import-Inducing Effect',
            'Total Value-Added Creation Effect',
            'Total Job Creating Effect',
            'Total Direct Employment Effect'
        ]

        # Group scenarios by type
        scenario_groups = {}
        for scenario in scenarios:
            scenario_str = str(scenario)
            if '석탄' in scenario_str:
                group = '석탄수요감소량'
            elif '재생에너지' in scenario_str or '전력' in scenario_str:
                group = '재생에너지전력수요량'
            elif '수소' in scenario_str:
                group = '수소수요량'
            else:
                group = '기타'

            if group not in scenario_groups:
                scenario_groups[group] = []
            scenario_groups[group].append(scenario)

        # Build comprehensive table
        table_data = []

        for group_name, group_scenarios in scenario_groups.items():
            # Add group header
            group_row = {'Category': group_name, 'Effect Type': ''}
            for year in valid_years:
                group_row[str(year)] = ''
            table_data.append(group_row)

            # Add effect type rows for this group
            for effect_name in effect_types:
                effect_row = {'Category': '', 'Effect Type': effect_name}

                for year in valid_years:
                    total_effect = 0

                    # Calculate total effect across all scenarios in this group
                    for scenario in group_scenarios:
                        try:
                            demand_change = self.get_shock_value(scenario, year)
                            if demand_change != 0:
                                # Simplified calculation - use absolute value as proxy
                                total_effect += abs(demand_change)
                        except:
                            continue

                    effect_row[str(year)] = f"{total_effect:,.0f}" if total_effect > 0 else "0"

                table_data.append(effect_row)

            # Add spacing row
            if group_name != list(scenario_groups.keys())[-1]:  # Don't add after last group
                table_data.append({'Category': '', 'Effect Type': '', **{str(year): '' for year in valid_years}})

        return pd.DataFrame(table_data)