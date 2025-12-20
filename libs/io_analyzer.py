import pandas as pd
from typing import Dict

class IOTableAnalyzer:
    def __init__(self, data_file: str = 'data/iotable_2020.xlsx'):
        """Initialize the I-O Table Analyzer with clean data structure."""
        self.data_file = data_file
        self.mapping = None
        self.codemap = None
        self.subsectormap = None
        self.coefficients = {}
        self.basic_to_subsector = {}
        self.basic_to_subsector_to_code_h = {}
        self.subsector_to_name = {}
        self.code_h_to_product_h = {}
        self.basic_to_code_h = {}
        self.code_h_options = {}
        self.code_to_product = {}
        self.code_to_product_display = {}
        self.load_data()

    def load_data(self):
        """Load mapping and all coefficient matrices from Excel file."""
        def format_code(code):
            """Format basic sector code to 4-digit string (e.g., '111' -> '0111')."""
            code_str = str(code).strip()
            if code_str.isdigit() and len(code_str) == 3:
                return f"0{code_str}"
            return code_str

        def format_subsector_code(code):
            """Format sub-sector code to 3-digit string."""
            try:
                code_int = int(float(code))
                return f"{code_int:03d}"
            except (ValueError, TypeError):
                return str(code).strip()

        try:
            # Load mapping sheet
            self.mapping = pd.read_excel(self.data_file, sheet_name='basicmap')
            self.mapping['code'] = self.mapping['code'].apply(format_code)

            # Define coefficient sheets to load
            basic_coeff_sheets = {
                'indirect_prod': 'indirectprodcoeff',
                'indirect_import': 'indirectimportcoeff',
                'value_added': 'valueaddedcoeff'
            }

            # Load basic coefficient matrices
            for name, sheet in basic_coeff_sheets.items():
                df = pd.read_excel(self.data_file, sheet_name=sheet)

                # Rename first column to 'code' and format
                df = df.rename(columns={df.columns[0]: 'code'})
                df['code'] = df['code'].apply(format_code)
                df = df.set_index('code')

                # Format column names
                df.columns = [format_code(col) for col in df.columns]

                self.coefficients[name] = df

            # Load job coefficient matrices (use sub-sector format)
            job_coeff_sheets = {
                'jobcoeff': 'jobcoeff',
                'directemploycoeff': 'directemploycoeff'
            }

            for name, sheet in job_coeff_sheets.items():
                df = pd.read_excel(self.data_file, sheet_name=sheet)
                df = df.rename(columns={df.columns[0]: 'code'})

                # Format both index and columns with 3-digit sub-sector codes
                df['code'] = df['code'].apply(format_subsector_code)
                df = df.set_index('code')
                df.columns = [format_subsector_code(col) for col in df.columns]

                self.coefficients[name] = df

            # Load codemap for basic-to-subsector mapping
            self.codemap = pd.read_excel(self.data_file, sheet_name='codemap')

            # Load subsectormap for sub-sector names
            self.subsectormap = pd.read_excel(self.data_file, sheet_name='subsectormap')

            # Create sub-sector code to name mapping
            for _, row in self.subsectormap.iterrows():
                subsector_code = format_subsector_code(row['code'])
                subsector_name = row['name']
                self.subsector_to_name[subsector_code] = subsector_name

            # Create code_h to product_h mapping
            self.code_h_to_product_h = pd.Series(
                self.codemap['product_h'].values,
                index=self.codemap['code_h']
            ).to_dict()

            # Create basic code to code_h mapping
            for _, row in self.codemap.iterrows():
                basic_code = format_code(row['Basic'])
                code_h_value = row['code_h']
                self.basic_to_code_h[basic_code] = code_h_value

            # Create display options for code_h
            unique_code_h = self.codemap[['code_h', 'product_h']].drop_duplicates()
            self.code_h_options = {
                row['code_h']: f"{row['code_h']}: {row['product_h']}"
                for _, row in unique_code_h.iterrows()
            }

            # Create basic-to-subsector mapping
            for _, row in self.codemap.iterrows():
                basic_code = format_code(row['Basic'])
                subsector_code = format_subsector_code(row['Sub-sector'])
                code_h_value = row['code_h']
                self.basic_to_subsector[basic_code] = subsector_code
                self.basic_to_subsector_to_code_h.setdefault(basic_code, {})[subsector_code] = code_h_value

            # Create code-to-product mapping dictionary
            self.code_to_product = pd.Series(
                self.mapping['product'].values,
                index=self.mapping['code']
            ).to_dict()
            self.code_to_product_display = {
                code: f"{code}: {product}"
                for code, product in self.code_to_product.items()
            }

        except Exception as e:
            raise RuntimeError(f"Error loading I-O table data from {self.data_file}: {str(e)}")

    def get_sector_options(self, level: str = 'basic') -> Dict:
        """
        Return available sector codes and their products for display.

        Args:
            level: 'basic' for basic sector codes, 'code_h' for high-level categories

        Returns:
            Dictionary mapping codes to display strings
        """
        if level == 'code_h':
            return self.code_h_options
        else:
            return self.code_to_product_display

    def get_sector_from_display(self, display_string: str):
        """Extract sector code from display string."""
        return display_string.split(":")[0]

    def calculate_direct_effects(self, target_sector, demand_change: float, coeff_type: str = 'indirect_prod', quiet: bool = False) -> Dict[str, any]:
        """
        Calculate effects of demand change in target sector using specified coefficient matrix.

        Args:
            target_sector: Sector code (string like "0111" or integer like 2711)
            demand_change: Change in final demand (positive or negative, in million won)
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
            'indirect_prod': 'Indirect Production (I-Ad)⁻¹',
            'indirect_import': 'Indirect Import',
            'value_added': 'Value-Added',
            'jobcoeff': 'Total Job Creation',
            'directemploycoeff': 'Direct Employment'
        }

        if not quiet:
            print(f"\nAnalyzing {coeff_names[coeff_type]} effects for {final_target_sector}: {target_product}")
            print(f"Demand change: {demand_change:,.0f} million won")
            print(f"Using coefficient type: {coeff_type} ({coeff_names[coeff_type]})")

        # Handle job coefficients which use sub-sector mapping
        if coeff_type in ['jobcoeff', 'directemploycoeff']:
            return self._calculate_job_effects(final_target_sector, demand_change, coeff_type, coeff_names[coeff_type], quiet)

        # Use final_target_sector for regular coefficients
        selected_coeffs = self.coefficients[coeff_type]

        if final_target_sector not in selected_coeffs.columns:
            raise ValueError(f"Column for sector {final_target_sector} not found in {coeff_type} coefficient matrix")

        # Calculate direct effects: coefficient * demand_change
        # Convert from million won to billion won
        direct_impacts = selected_coeffs[final_target_sector] * demand_change / 1000

        significant_impacts = direct_impacts

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
        print(f"Demand Change: {results['demand_change']:,.0f} million won")
        print(f"Coefficient Type: {results['coeff_type']} ({results['coeff_name']})")
        print(f"Total Impact: {results['total_impact']:,.2f} billion won")
        print(f"Affected Sectors: {results['num_affected_sectors']}")

        print(f"\n{'Top 20 Impacts:':<60}")
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

        # Find the sub-sector code for this basic sector
        if target_sector not in self.basic_to_subsector:
            raise ValueError(f"Sub-sector mapping not found for basic sector {target_sector}")

        subsector_code = self.basic_to_subsector[target_sector]

        if not quiet:
            print(f"Basic sector {target_sector} maps to sub-sector {subsector_code}")

        # Get job coefficient matrix
        selected_coeffs = self.coefficients[coeff_type]

        # Check if sub-sector column exists in job coefficient matrix
        if subsector_code not in selected_coeffs.columns:
            raise ValueError(f"Sub-sector column {subsector_code} not found in {coeff_type} coefficient matrix")

        # Calculate job effects: coefficient * demand_change
        # Note: Job coefficients represent jobs per unit of output, so result is in number of jobs
        job_impacts = selected_coeffs[subsector_code] * demand_change / 1000

        significant_impacts = job_impacts

        # Create results with sector names (using sub-sector mapping for job results)
        results = []
        for sector_code, impact in significant_impacts.items():
            # For job coefficients, sector_code represents the sub-sector experiencing job impact
            # Use subsectormap to get proper sub-sector names
            if sector_code in self.subsector_to_name:
                sector_name = self.subsector_to_name.get(sector_code, f"Sub-sector {sector_code}")
            else:
                sector_name = f"Sub-sector {sector_code}"

            results.append({
                'sector_code': sector_code,
                'sector_name': sector_name,
                'impact': impact
            })

        # Sort by absolute impact (descending)
        results.sort(key=lambda x: abs(x['impact']), reverse=True)

        # Calculate summary statistics
        total_impact = sum([r['impact'] for r in results])

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

    def aggregate_to_code_h(self, results: Dict) -> Dict:
        """
        Aggregate basic sector results to code_h level.

        Args:
            results: Dictionary from calculate_direct_effects

        Returns:
            Dictionary with aggregated results by code_h
        """
        code_h_impacts = {}

        for impact in results['impacts']:
            sector_code = impact['sector_code']
            impact_value = impact['impact']

            # Get code_h for this basic sector
            if sector_code in self.basic_to_code_h:
                code_h = self.basic_to_code_h[sector_code]
                product_h = self.code_h_to_product_h.get(code_h, f"Category {code_h}")

                if code_h not in code_h_impacts:
                    code_h_impacts[code_h] = {
                        'code_h': code_h,
                        'product_h': product_h,
                        'impact': 0,
                        'sector_count': 0
                    }

                code_h_impacts[code_h]['impact'] += impact_value
                code_h_impacts[code_h]['sector_count'] += 1

        # Convert to list and sort
        aggregated_results = list(code_h_impacts.values())
        aggregated_results.sort(key=lambda x: abs(x['impact']), reverse=True)

        total_impact = sum([r['impact'] for r in aggregated_results])

        return {
            'target_sector': results['target_sector'],
            'target_product': results['target_product'],
            'demand_change': results['demand_change'],
            'coeff_type': results['coeff_type'],
            'coeff_name': results['coeff_name'],
            'aggregation_level': 'code_h',
            'impacts': aggregated_results,
            'total_impact': total_impact,
            'num_affected_categories': len(aggregated_results)
        }

    def calculate_effects_by_code_h(self, target_sector, demand_change: float, coeff_type: str = 'indirect_prod', quiet: bool = False) -> Dict:
        """
        Calculate effects and automatically aggregate to code_h level.

        Args:
            target_sector: Sector code (string like "0111" or integer like 2711)
            demand_change: Change in final demand (positive or negative, in million won)
            coeff_type: Type of coefficients to use
            quiet: If True, suppress print output

        Returns:
            Dictionary with code_h aggregated results
        """
        # First calculate at basic sector level
        basic_results = self.calculate_direct_effects(target_sector, demand_change, coeff_type, quiet=quiet)

        # Then aggregate to code_h level
        return self.aggregate_to_code_h(basic_results)

    def display_code_h_results(self, results: Dict):
        """Display code_h aggregated analysis results."""
        print(f"\n{'='*70}")
        print(f"CODE_H AGGREGATED EFFECTS - {results['coeff_name'].upper()}")
        print(f"{'='*70}")
        print(f"Target Sector: {results['target_sector']} - {results['target_product']}")
        print(f"Demand Change: {results['demand_change']:,.0f} million won")
        print(f"Coefficient Type: {results['coeff_type']} ({results['coeff_name']})")
        print(f"Total Impact: {results['total_impact']:,.2f} billion won")
        print(f"Affected Categories: {results['num_affected_categories']}")

        print(f"\n{'All Categories:':<70}")
        print(f"{'Code_H':<8} {'Category':<30} {'Sectors':>10} {'Impact':>18}")
        print("-" * 70)

        for impact in results['impacts']:
            print(f"{impact['code_h']:<8} {impact['product_h']:<30} {impact['sector_count']:>10} {impact['impact']:>18,.2f}")

    def calculate_all_effects(self, selected_sector, demand_change: float, quiet: bool = True) -> tuple:
        """
        Calculate all coefficient effects for a given sector and demand change.

        Args:
            selected_sector: Sector code (string like "0111" or integer like 2711)
            demand_change: Change in final demand (positive or negative, in million won)
            quiet: If True, suppress print output (default True)

        Returns:
            Tuple of (all_results, coefficient_types, coeff_names)
            - all_results: Dictionary with results for each coefficient type
            - coefficient_types: List of coefficient types analyzed
            - coeff_names: Dictionary mapping coefficient types to display names
        """
        # Define coefficient types and their display names
        coefficient_types = ["indirect_prod", "indirect_import", "value_added", "jobcoeff", "directemploycoeff"]
        coeff_names = {
            "indirect_prod": "Production-inducing",
            "indirect_import": "Import-inducing",
            "value_added": "Value-Added",
            "jobcoeff": "Total Job Creation",
            "directemploycoeff": "Direct Employment"
        }

        # Calculate all coefficient effects
        all_results = {}
        for coeff_type in coefficient_types:
            try:
                results = self.calculate_direct_effects(
                    selected_sector,
                    demand_change,
                    coeff_type,
                    quiet=quiet
                )
                all_results[coeff_type] = results
            except Exception as e:
                if not quiet:
                    print(f"Error calculating {coeff_type}: {str(e)}")
                all_results[coeff_type] = None

        return all_results, coefficient_types, coeff_names

    def create_combined_data(self, all_results: Dict, coefficient_types: list, coeff_names: Dict) -> list:
        """
        Create combined data from all analysis results with code_h and product_h mappings.

        Args:
            all_results: Dictionary of results from calculate_direct_effects for each coefficient type
            coefficient_types: List of coefficient types to include
            coeff_names: Dictionary mapping coefficient types to display names

        Returns:
            List of dictionaries containing combined data for all coefficient types
        """
        combined_data = []

        for coeff_type in coefficient_types:
            if all_results[coeff_type] and all_results[coeff_type]['impacts']:
                results = all_results[coeff_type]
                for impact in results['impacts']:
                    # Get code_h and product_h if available
                    sector_code = impact['sector_code']
                    code_h = self.basic_to_code_h.get(sector_code, '')
                    product_h = self.code_h_to_product_h.get(code_h, '') if code_h else ''

                    combined_data.append({
                        'coefficient_type': coeff_type,
                        'coefficient_name': coeff_names[coeff_type],
                        'sector_code': sector_code,
                        'sector_name': impact['sector_name'],
                        'code_h': code_h,
                        'product_h': product_h,
                        'impact': impact['impact']
                    })

        return combined_data

    def calculate_linkages(self, sector_code: str = None) -> Dict:
        """
        Calculate backward and forward linkages for a sector or all sectors.

        Backward linkage: How much a sector depends on other sectors as suppliers
        Forward linkage: How much other sectors depend on this sector as supplier

        Values > 1.0 indicate above-average linkage effects

        Args:
            sector_code: Sector code (if None, calculates for all sectors)

        Returns:
            Dictionary with backward and forward linkage values
        """
        import numpy as np

        # Get indirect production coefficient matrix (Leontief inverse)
        leontief = self.coefficients['indirect_prod']
        n = len(leontief)

        # Calculate column sums (backward linkage) - how much each sector demands from all sectors
        backward_linkages = leontief.sum(axis=0)
        avg_backward = backward_linkages.mean()

        # Calculate row sums (forward linkage) - how much each sector supplies to all sectors
        forward_linkages = leontief.sum(axis=1)
        avg_forward = forward_linkages.mean()

        if sector_code:
            # Convert sector code format
            if isinstance(sector_code, str) and sector_code.isdigit():
                sector_int = int(sector_code)
                sector_code = f"0{sector_int}" if sector_int < 1000 else str(sector_int)

            if sector_code not in self.code_to_product:
                raise ValueError(f"Sector {sector_code} not found")

            return {
                'sector_code': sector_code,
                'sector_name': self.code_to_product[sector_code],
                'backward_linkage': backward_linkages[sector_code],
                'forward_linkage': forward_linkages[sector_code],
                'backward_normalized': backward_linkages[sector_code] / avg_backward,
                'forward_normalized': forward_linkages[sector_code] / avg_forward,
                'is_key_sector': (backward_linkages[sector_code] / avg_backward > 1.0 and
                                 forward_linkages[sector_code] / avg_forward > 1.0)
            }
        else:
            # Return for all sectors
            results = []
            for code in leontief.columns:
                if code in self.code_to_product:
                    backward_norm = backward_linkages[code] / avg_backward
                    forward_norm = forward_linkages[code] / avg_forward
                    results.append({
                        'sector_code': code,
                        'sector_name': self.code_to_product[code],
                        'backward_linkage': backward_linkages[code],
                        'forward_linkage': forward_linkages[code],
                        'backward_normalized': backward_norm,
                        'forward_normalized': forward_norm,
                        'is_key_sector': (backward_norm > 1.0 and forward_norm > 1.0)
                    })

            return {
                'sectors': results,
                'avg_backward': avg_backward,
                'avg_forward': avg_forward
            }

    def calculate_multipliers(self, sector_code: str) -> Dict:
        """
        Calculate output, value-added, and employment multipliers.

        Multipliers show total impact per unit of final demand change.

        Args:
            sector_code: Sector code

        Returns:
            Dictionary with multiplier values
        """
        # Convert sector code format
        if isinstance(sector_code, str) and sector_code.isdigit():
            sector_int = int(sector_code)
            sector_code = f"0{sector_int}" if sector_int < 1000 else str(sector_int)

        if sector_code not in self.code_to_product:
            raise ValueError(f"Sector {sector_code} not found")

        # Output multiplier: sum of column in Leontief inverse
        leontief = self.coefficients['indirect_prod']
        output_multiplier = leontief[sector_code].sum()

        # Value-added multiplier: sum of value-added coefficients weighted by Leontief inverse
        value_added_coeffs = self.coefficients['value_added']
        value_added_multiplier = (value_added_coeffs[sector_code] * leontief[sector_code]).sum()

        # Employment multiplier (if using job coefficients)
        subsector_code = self.basic_to_subsector.get(sector_code)
        if subsector_code and subsector_code in self.coefficients['jobcoeff'].columns:
            job_coeffs = self.coefficients['jobcoeff']
            employment_multiplier = job_coeffs[subsector_code].sum()
        else:
            employment_multiplier = None

        return {
            'sector_code': sector_code,
            'sector_name': self.code_to_product[sector_code],
            'output_multiplier': output_multiplier,
            'value_added_multiplier': value_added_multiplier,
            'employment_multiplier': employment_multiplier,
            'interpretation': {
                'output': f"1 billion won increase → {output_multiplier:.2f} billion won total output",
                'value_added': f"1 billion won increase → {value_added_multiplier:.2f} billion won value added",
                'employment': f"1 billion won increase → {employment_multiplier:.2f} jobs" if employment_multiplier else "N/A"
            }
        }

    def compare_sectors(self, sector_codes: list, demand_change: float, coeff_type: str = 'indirect_prod') -> Dict:
        """
        Compare multiple sectors side-by-side.

        Args:
            sector_codes: List of sector codes to compare
            demand_change: Demand change amount (same for all sectors)
            coeff_type: Coefficient type to analyze

        Returns:
            Dictionary with comparison results
        """
        comparison_results = []

        for sector_code in sector_codes:
            try:
                results = self.calculate_direct_effects(sector_code, demand_change, coeff_type, quiet=True)
                comparison_results.append({
                    'sector_code': results['target_sector'],
                    'sector_name': results['target_product'],
                    'total_impact': results['total_impact'],
                    'num_affected_sectors': results['num_affected_sectors'],
                    'top_5_impacts': results['impacts'][:5]
                })
            except Exception as e:
                comparison_results.append({
                    'sector_code': sector_code,
                    'sector_name': 'Error',
                    'total_impact': 0,
                    'error': str(e)
                })

        # Sort by total impact
        comparison_results.sort(key=lambda x: abs(x.get('total_impact', 0)), reverse=True)

        return {
            'demand_change': demand_change,
            'coeff_type': coeff_type,
            'sectors': comparison_results
        }

    def export_results(self, results: Dict, filename: str, format: str = 'xlsx'):
        """
        Export analysis results to file.

        Args:
            results: Results dictionary from calculate_direct_effects
            filename: Output filename (without extension)
            format: 'xlsx' or 'csv'
        """
        import pandas as pd

        # Create DataFrame from impacts
        df = pd.DataFrame(results['impacts'])

        # Add metadata sheet/header
        metadata = {
            'Target Sector': results['target_sector'],
            'Target Product': results['target_product'],
            'Demand Change (Million Won)': results['demand_change'],
            'Coefficient Type': results['coeff_type'],
            'Total Impact (Billion Won)': results['total_impact'],
            'Affected Sectors': results['num_affected_sectors']
        }

        if format == 'xlsx':
            with pd.ExcelWriter(f"{filename}.xlsx", engine='openpyxl') as writer:
                # Write metadata
                pd.DataFrame([metadata]).T.to_excel(writer, sheet_name='Metadata', header=False)
                # Write impacts
                df.to_excel(writer, sheet_name='Impacts', index=False)
        else:
            # For CSV, write metadata as header comments
            with open(f"{filename}.csv", 'w') as f:
                for key, value in metadata.items():
                    f.write(f"# {key}: {value}\n")
                f.write("\n")
            df.to_csv(f"{filename}.csv", mode='a', index=False)

    def identify_key_sectors(self, threshold: float = 1.0) -> Dict:
        """
        Identify key sectors with high backward AND forward linkages.

        Key sectors have above-average linkages in both directions,
        meaning they have the biggest ripple effects in the economy.

        Args:
            threshold: Normalized linkage threshold (default 1.0 = average)

        Returns:
            Dictionary with key sectors and their linkages
        """
        all_linkages = self.calculate_linkages()

        key_sectors = []
        backward_only = []
        forward_only = []
        weak_linkage = []

        for sector in all_linkages['sectors']:
            backward_norm = sector['backward_normalized']
            forward_norm = sector['forward_normalized']

            if backward_norm > threshold and forward_norm > threshold:
                key_sectors.append(sector)
            elif backward_norm > threshold:
                backward_only.append(sector)
            elif forward_norm > threshold:
                forward_only.append(sector)
            else:
                weak_linkage.append(sector)

        # Sort each category by combined linkage strength
        key_sectors.sort(key=lambda x: x['backward_normalized'] + x['forward_normalized'], reverse=True)
        backward_only.sort(key=lambda x: x['backward_normalized'], reverse=True)
        forward_only.sort(key=lambda x: x['forward_normalized'], reverse=True)

        return {
            'key_sectors': key_sectors,  # High backward AND forward
            'backward_only': backward_only,  # High backward, low forward
            'forward_only': forward_only,  # Low backward, high forward
            'weak_linkage': weak_linkage,  # Low in both
            'threshold': threshold,
            'summary': {
                'key_sectors_count': len(key_sectors),
                'backward_only_count': len(backward_only),
                'forward_only_count': len(forward_only),
                'weak_linkage_count': len(weak_linkage)
            }
        }

    def sensitivity_analysis(self, sector_code: str, demand_changes: list, coeff_type: str = 'indirect_prod') -> Dict:
        """
        Test multiple demand change scenarios to see how effects scale.

        Args:
            sector_code: Sector code to analyze
            demand_changes: List of demand change values to test
            coeff_type: Coefficient type to use

        Returns:
            Dictionary with results for each scenario
        """
        scenarios = []

        for demand_change in demand_changes:
            results = self.calculate_direct_effects(sector_code, demand_change, coeff_type, quiet=True)
            scenarios.append({
                'demand_change': demand_change,
                'total_impact': results['total_impact'],
                'num_affected_sectors': results['num_affected_sectors'],
                'impact_ratio': results['total_impact'] / (demand_change / 1000) if demand_change != 0 else 0,
                'top_3_sectors': results['impacts'][:3]
            })

        return {
            'sector_code': sector_code,
            'sector_name': self.code_to_product[sector_code],
            'coeff_type': coeff_type,
            'scenarios': scenarios
        }

if __name__ == "__main__":
    analyzer = IOTableAnalyzer()

    # Test calculate_all_effects
    print("\n" + "="*70)
    print("TEST: calculate_all_effects()")
    print("="*70)
    target_sector = "1610"
    demand_change = 345000

    all_results, coefficient_types, coeff_names = analyzer.calculate_all_effects(
        target_sector,
        demand_change,
        quiet=False
    )
    for coeff_type in coefficient_types:
        print(f"\n--- Results for coefficient type: {coeff_type} ({coeff_names[coeff_type]}) ---")
        results = all_results[coeff_type]
        if results:
            analyzer.display_results(results)
        else:
            print("No results available.")

    # Test create_combined_data
    print("\n" + "="*70)
    print("TEST: create_combined_data()")
    print("="*70)
    combined_data = analyzer.create_combined_data(all_results, coefficient_types, coeff_names)

    if combined_data:
        print(f"{'CoeffType':<18} {'CoeffName':<18} {'SectorCode':<10} {'SectorName':<30} {'Code_H':<8} {'Product_H':<16} {'Impact':>12}")
        print("-" * 110)
        for row in combined_data[:10]:
            print(f"{row['coefficient_type']:<18} {row['coefficient_name']:<18} {row['sector_code']:<10} {row['sector_name']:<30} {row['code_h']:<8} {row['product_h']:<16} {row['impact']:>12,.2f}")
        if len(combined_data) > 10:
            print(f"... ({len(combined_data)} total rows)")
    else:
        print("No combined data available.")
