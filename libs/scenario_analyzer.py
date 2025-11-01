import pandas as pd
import numpy as np
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import seaborn as sns
from libs.hydrogen_analyzer import HydrogenTableAnalyzer
from libs.io_analyzer import IOTableAnalyzer

class ScenarioAnalyzer:
    def __init__(self, scenarios_file: str = 'data/scenarios_3.xlsx'):
        """Initialize the Scenario Analyzer with scenarios data."""
        self.scenarios_file = scenarios_file
        self.scenarios_data = None
        self.hydrogen_analyzer = None
        self.io_analyzer = None
        self.results = {}
        self.aggregated_results = {}
        self.load_scenarios()

    def load_scenarios(self):
        """Load scenarios from Excel file."""
        print("Loading scenarios data...")
        self.scenarios_data = pd.read_excel(self.scenarios_file)

        # Convert mixed data types to strings for consistency
        self.scenarios_data['input'] = self.scenarios_data['input'].astype(str)
        self.scenarios_data['sector'] = self.scenarios_data['sector'].astype(str)

        print(f"Loaded {len(self.scenarios_data)} scenarios")
        print(f"Years covered: {self.scenarios_data.columns[2:].tolist()}")

    def initialize_analyzers(self):
        """Initialize the hydrogen and IO table analyzers."""
        print("Initializing analyzers...")
        self.hydrogen_analyzer = HydrogenTableAnalyzer()
        self.io_analyzer = IOTableAnalyzer()

    def run_all_scenarios(self, effect_types: List[str] = None):
        """
        Run analysis for all scenarios across all years.

        Args:
            effect_types: List of effect types to analyze. If None, analyzes all available types.
        """
        if self.hydrogen_analyzer is None or self.io_analyzer is None:
            self.initialize_analyzers()
        if effect_types is None:
            # Default effect types based on available coefficient matrices
            effect_types = [
                'productioncoeff',  # (for hydrogen)
                'indirect_prod',  # (for IO)
                'indirect_import',  # (for IO)
                'jobcoeff',  # Job creation
                'valueaddedcoeff',  # Value added (hydrogen)
                'value_added'  # Value added (IO)
            ]

        print(f"Running scenario analysis for effect types: {effect_types}")

        # Get year columns (exclude 'input' and 'sector' columns)
        year_columns = [col for col in self.scenarios_data.columns if isinstance(col, int)]

        # Initialize results structure
        for effect_type in effect_types:
            self.results[effect_type] = {}
            self.aggregated_results[effect_type] = {}

        # Process each scenario row
        for idx, scenario_row in self.scenarios_data.iterrows():
            input_table = scenario_row['input']
            sector = scenario_row['sector']

            print(idx)

            print(f"\nProcessing scenario {idx + 1}: {input_table} - {sector}")

            # Determine analyzer type based on input table
            is_hydrogen = 'hydrogen' in input_table.lower()

            # Process each year for this scenario
            for year in year_columns:
                demand_change = scenario_row[year]

                if pd.isna(demand_change) or demand_change == 0:
                    continue

                print(f"  Processing year {year}: demand change = {demand_change}")

                # Run analysis for each effect type
                for effect_type in effect_types:
                    try:
                        if is_hydrogen:
                            # Use hydrogen analyzer
                            if effect_type in ['productioncoeff', 'valueaddedcoeff', 'jobcoeff', 'directemploycoeff']:
                                result = self.hydrogen_analyzer.calculate_hydrogen_effects(
                                    scenario=sector,
                                    demand_change=demand_change,
                                    coeff_type=effect_type,
                                    quiet=True
                                )
                                self._store_result(effect_type, year, idx, result, is_hydrogen=True)

                        else:
                            # Use IO analyzer - convert sector to proper format for IO table
                            # try:
                            #     # Try to convert sector to int if it's a numeric string
                            #     if sector.isdigit():
                            #         target_sector = int(sector)
                            #     else:
                            #         target_sector = sector
                            # except (ValueError, AttributeError):
                            #     target_sector = sector

                            if effect_type in [ 'indirect_prod', 'indirect_import', 'value_added', 'jobcoeff', 'directemploycoeff']:
                                result = self.io_analyzer.calculate_direct_effects(
                                    target_sector=sector,
                                    demand_change=demand_change,
                                    coeff_type=effect_type,
                                    quiet=True
                                )
                                self._store_result(effect_type, year, idx, result, is_hydrogen=False)

                    except Exception as e:
                        print(f"    Error in {effect_type}: {str(e)}")
                        continue

        # Aggregate results by year and effect type
        self._aggregate_results(year_columns, effect_types)
        print("\nScenario analysis complete!")

    def _store_result(self, effect_type: str, year: int, scenario_idx: int, result: Dict, is_hydrogen: bool):
        """Store individual scenario result."""
        if year not in self.results[effect_type]:
            self.results[effect_type][year] = {}

        
        total_impact = 0 # 기본값 설정
        # if 'total_job_impact' in result and result['total_job_impact'] != 0:
        #     total_impact = result['total_job_impact']
        # elif 'total_economic_impact' in result:
        #     total_impact = result['total_economic_impact']

        scenario_key = f"scenario_{scenario_idx}"
        self.results[effect_type][year][scenario_key] = {
            'result': result,
            'is_hydrogen': is_hydrogen,
            'total_impact': result['total_impact'],
            'num_affected_sectors': result['num_affected_sectors']
        }


    def _aggregate_results(self, year_columns: List[int], effect_types: List[str]):
        """Aggregate results across all scenarios for each year and effect type."""
        print("Aggregating results...")

        for effect_type in effect_types:
            self.aggregated_results[effect_type] = {}

            for year in year_columns:
                if year not in self.results[effect_type]:
                    continue

                # Aggregate all scenarios for this year and effect type
                year_results = self.results[effect_type][year]

                # Combine all sector impacts
                all_sector_impacts = {}
                total_aggregate_impact = 0
                scenario_count = 0

                for scenario_key, scenario_data in year_results.items():
                    result = scenario_data['result']
                    total_aggregate_impact += result['total_impact']
                    scenario_count += 1

                    # Aggregate sector-level impacts
                    for impact in result['impacts']:
                        sector_code = str(impact['sector_code'])  # Ensure string
                        sector_name = impact['sector_name']
                        impact_value = impact['impact']

                        if sector_code not in all_sector_impacts:
                            all_sector_impacts[sector_code] = {
                                'sector_name': sector_name,
                                'total_impact': 0,
                                'scenario_count': 0
                            }

                        all_sector_impacts[sector_code]['total_impact'] += impact_value
                        all_sector_impacts[sector_code]['scenario_count'] += 1

                # Convert to sorted list
                aggregated_impacts = []
                for sector_code, data in all_sector_impacts.items():
                    aggregated_impacts.append({
                        'sector_code': sector_code,
                        'sector_name': data['sector_name'],
                        'total_impact': data['total_impact'],
                        'avg_impact': data['total_impact'] / data['scenario_count'],
                        'scenario_count': data['scenario_count']
                    })

                # Sort by total impact
                aggregated_impacts.sort(key=lambda x: abs(x['total_impact']), reverse=True)

                self.aggregated_results[effect_type][year] = {
                    'total_aggregate_impact': total_aggregate_impact,
                    'scenario_count': scenario_count,
                    'avg_aggregate_impact': total_aggregate_impact / scenario_count if scenario_count > 0 else 0,
                    'sector_impacts': aggregated_impacts,
                    'num_affected_sectors': len(aggregated_impacts)
                }

    def create_summary_tables(self, output_dir: str = 'output'):
        """Create Excel files with summary tables for each effect type."""
        import os
        os.makedirs(output_dir, exist_ok=True)

        print(f"Creating summary tables in {output_dir}/...")

        for effect_type in self.aggregated_results.keys():
            if not self.aggregated_results[effect_type]:
                continue

            # Create Excel file for this effect type
            filename = f"{output_dir}/scenario_analysis_{effect_type}.xlsx"

            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Summary by year (aggregated totals)
                summary_data = []
                for year, data in self.aggregated_results[effect_type].items():
                    summary_data.append({
                        'Year': year,
                        'Total_Impact': data['total_aggregate_impact'],
                        'Avg_Impact': data['avg_aggregate_impact'],
                        'Scenario_Count': data['scenario_count'],
                        'Affected_Sectors': data['num_affected_sectors']
                    })

                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary_by_Year', index=False)

                # Detailed sector impacts by year
                all_years = sorted(self.aggregated_results[effect_type].keys())
                all_sectors = set()

                # Collect all unique sectors
                for year_data in self.aggregated_results[effect_type].values():
                    for impact in year_data['sector_impacts']:
                        all_sectors.add(str(impact['sector_code']))

                # Create sector impact matrix
                sector_matrix = []
                for sector_code in sorted(all_sectors):
                    row = {'Sector_Code': sector_code, 'Sector_Name': ''}

                    # Add code_h and product_h columns if IO analyzer is available and this is not a job coefficient
                    if self.io_analyzer and effect_type not in ['jobcoeff', 'directemploycoeff']:
                        code_h = self.io_analyzer.basic_to_code_h.get(sector_code, '')
                        product_h = self.io_analyzer.code_h_to_product_h.get(code_h, '') if code_h else ''
                        row['Code_H'] = code_h
                        row['Category_H'] = product_h

                    for year in all_years:
                        year_data = self.aggregated_results[effect_type][year]
                        impact_value = 0
                        sector_name = ''

                        for impact in year_data['sector_impacts']:
                            if str(impact['sector_code']) == sector_code:
                                impact_value = impact['total_impact']
                                sector_name = impact['sector_name']
                                break

                        row[f'Year_{year}'] = impact_value
                        if not row['Sector_Name']:
                            row['Sector_Name'] = sector_name

                    sector_matrix.append(row)

                sector_df = pd.DataFrame(sector_matrix)

                # Reorder columns to have Code_H and Category_H after Sector_Name
                if self.io_analyzer and effect_type not in ['jobcoeff', 'directemploycoeff']:
                    cols = ['Sector_Code', 'Sector_Name', 'Code_H', 'Category_H'] + [col for col in sector_df.columns if col.startswith('Year_')]
                    sector_df = sector_df[cols]

                sector_df.to_excel(writer, sheet_name='Sector_Impacts_by_Year', index=False)

            print(f"Created {filename}")

    def save_individual_scenario_csvs(self, output_dir: str = 'output'):
        """
        Save individual CSV files for each scenario (input table + sector combination).
        Files are named: scenario_{effect_type}_{sector}_{input_table}.csv
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        print(f"Saving individual scenario CSV files to {output_dir}/...")

        # Group results by (effect_type, input_table, sector)
        scenario_data_map = {}

        for effect_type in self.results.keys():
            if not self.results[effect_type]:
                continue

            for year in self.results[effect_type].keys():
                for scenario_key, scenario_result in self.results[effect_type][year].items():
                    # Extract scenario index from scenario_key (e.g., "scenario_0" -> 0)
                    scenario_idx = int(scenario_key.split('_')[1])

                    # Get scenario metadata from scenarios_data
                    scenario_row = self.scenarios_data.iloc[scenario_idx]
                    input_table = scenario_row['input']
                    sector = str(scenario_row['sector'])

                    # Create unique key for this scenario
                    unique_key = (effect_type, sector, input_table)

                    if unique_key not in scenario_data_map:
                        scenario_data_map[unique_key] = {}

                    # Store results for this year
                    scenario_data_map[unique_key][year] = scenario_result['result']

        # Now create CSV files for each unique scenario
        for (effect_type, sector, input_table), year_results in scenario_data_map.items():
            # Sort years
            sorted_years = sorted(year_results.keys())

            # Collect all unique output sectors across all years
            all_output_sectors = {}
            for year, result in year_results.items():
                for impact in result['impacts']:
                    sector_code = str(impact['sector_code'])
                    sector_name = impact['sector_name']
                    if sector_code not in all_output_sectors:
                        all_output_sectors[sector_code] = sector_name

            # Create matrix data (rows = output sectors, columns = years)
            matrix_data = []
            for sector_code, sector_name in all_output_sectors.items():
                row = {
                    'Sector_Code': sector_code,
                    'Sector_Name': sector_name
                }

                # Add impact values for each year
                for year in sorted_years:
                    impact_value = 0.0
                    result = year_results[year]

                    for impact in result['impacts']:
                        if str(impact['sector_code']) == sector_code:
                            impact_value = impact['impact']
                            break

                    row[str(year)] = impact_value

                matrix_data.append(row)

            # Create DataFrame
            if matrix_data:
                df = pd.DataFrame(matrix_data)

                # Sort by the latest year's absolute impact
                latest_year_col = str(sorted_years[-1])
                if latest_year_col in df.columns:
                    df['abs_latest'] = df[latest_year_col].abs()
                    df = df.sort_values('abs_latest', ascending=False)
                    df = df.drop('abs_latest', axis=1)

                # Clean up the input_table name for filename
                input_table_clean = input_table.replace('.xlsx', '').replace(' ', '_')

                # Create filename: scenario_{effect_type}_{sector}_{input_table}.csv
                filename = f"{output_dir}/scenario_{effect_type}_{sector}_{input_table_clean}.csv"

                # Save to CSV with UTF-8-BOM encoding for proper Korean character display in Excel
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"Created {filename}")

        print(f"Saved {len(scenario_data_map)} individual scenario CSV files.")

    def create_summary_charts(self, output_dir: str = 'output'):
        """Create summary charts showing aggregated effects by year and effect type."""
        import os
        os.makedirs(output_dir, exist_ok=True)

        print(f"Creating summary charts in {output_dir}/...")

        # Set up the plotting style
        plt.style.use('default')
        sns.set_palette("husl")

        # Create summary chart for total impacts by effect type and year
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Scenario Analysis Summary - Aggregated Effects by Year', fontsize=16, fontweight='bold')

        # Chart 1: Total aggregate impact by year for each effect type
        ax1 = axes[0, 0]
        effect_types_with_data = []
        years_list = []

        for effect_type in self.aggregated_results.keys():
            if not self.aggregated_results[effect_type]:
                continue

            years = sorted(self.aggregated_results[effect_type].keys())
            totals = [self.aggregated_results[effect_type][year]['total_aggregate_impact'] for year in years]

            ax1.plot(years, totals, marker='o', linewidth=2, label=effect_type)
            effect_types_with_data.append(effect_type)
            if not years_list:
                years_list = years

        ax1.set_title('Total Aggregate Impact by Year')
        ax1.set_xlabel('Year')
        ax1.set_ylabel('Total Impact (Million KRW)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Chart 2: Number of affected sectors by year
        ax2 = axes[0, 1]
        for effect_type in effect_types_with_data:
            years = sorted(self.aggregated_results[effect_type].keys())
            sector_counts = [self.aggregated_results[effect_type][year]['num_affected_sectors'] for year in years]
            ax2.plot(years, sector_counts, marker='s', linewidth=2, label=effect_type)

        ax2.set_title('Number of Affected Sectors by Year')
        ax2.set_xlabel('Year')
        ax2.set_ylabel('Number of Sectors')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # Chart 3: Average impact per scenario by year
        ax3 = axes[1, 0]
        for effect_type in effect_types_with_data:
            years = sorted(self.aggregated_results[effect_type].keys())
            avg_impacts = [self.aggregated_results[effect_type][year]['avg_aggregate_impact'] for year in years]
            ax3.plot(years, avg_impacts, marker='^', linewidth=2, label=effect_type)

        ax3.set_title('Average Impact per Scenario by Year')
        ax3.set_xlabel('Year')
        ax3.set_ylabel('Average Impact (Million KRW)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # Chart 4: Heatmap of total impacts
        ax4 = axes[1, 1]
        if effect_types_with_data and years_list:
            heatmap_data = []
            heatmap_labels = []

            for effect_type in effect_types_with_data:
                row_data = []
                for year in years_list:
                    if year in self.aggregated_results[effect_type]:
                        row_data.append(self.aggregated_results[effect_type][year]['total_aggregate_impact'])
                    else:
                        row_data.append(0)
                heatmap_data.append(row_data)
                heatmap_labels.append(effect_type)

            sns.heatmap(heatmap_data,
                       xticklabels=years_list,
                       yticklabels=heatmap_labels,
                       annot=True,
                       fmt='.0f',
                       cmap='RdYlBu_r',
                       ax=ax4)
            ax4.set_title('Impact Heatmap (Effect Type vs Year)')
            ax4.set_xlabel('Year')
            ax4.set_ylabel('Effect Type')

        plt.tight_layout()
        plt.savefig(f'{output_dir}/scenario_summary_charts.png', dpi=300, bbox_inches='tight')
        plt.show()

        # Create individual charts for each effect type
        for effect_type in effect_types_with_data:
            self._create_effect_type_chart(effect_type, output_dir)

        print(f"Charts saved to {output_dir}/")

    def _create_effect_type_chart(self, effect_type: str, output_dir: str):
        """Create detailed chart for a specific effect type."""
        if not self.aggregated_results[effect_type]:
            return

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'Detailed Analysis - {effect_type}', fontsize=16, fontweight='bold')

        years = sorted(self.aggregated_results[effect_type].keys())

        # Chart 1: Total impact trend
        ax1 = axes[0, 0]
        totals = [self.aggregated_results[effect_type][year]['total_aggregate_impact'] for year in years]
        ax1.plot(years, totals, marker='o', linewidth=3, color='blue')
        ax1.set_title('Total Aggregate Impact Over Time')
        ax1.set_xlabel('Year')
        ax1.set_ylabel('Total Impact (Million KRW)')
        ax1.grid(True, alpha=0.3)

        # Chart 2: Top sectors for the last year
        ax2 = axes[0, 1]
        if years:
            last_year = years[-1]
            top_sectors = self.aggregated_results[effect_type][last_year]['sector_impacts'][:10]

            sector_names = [impact['sector_name'][:30] + '...' if len(impact['sector_name']) > 30
                           else impact['sector_name'] for impact in top_sectors]
            sector_impacts = [impact['total_impact'] for impact in top_sectors]

            bars = ax2.barh(range(len(sector_names)), sector_impacts)
            ax2.set_yticks(range(len(sector_names)))
            ax2.set_yticklabels(sector_names)
            ax2.set_title(f'Top 10 Affected Sectors ({last_year})')
            ax2.set_xlabel('Total Impact (Million KRW)')

            # Color bars based on impact (positive/negative)
            for i, (bar, impact) in enumerate(zip(bars, sector_impacts)):
                bar.set_color('green' if impact > 0 else 'red')

        # Chart 3: Scenario count by year
        ax3 = axes[1, 0]
        scenario_counts = [self.aggregated_results[effect_type][year]['scenario_count'] for year in years]
        ax3.bar(years, scenario_counts, alpha=0.7, color='orange')
        ax3.set_title('Number of Scenarios by Year')
        ax3.set_xlabel('Year')
        ax3.set_ylabel('Number of Scenarios')
        ax3.grid(True, alpha=0.3)

        # Chart 4: Impact distribution (histogram for last year)
        ax4 = axes[1, 1]
        if years:
            last_year = years[-1]
            impacts = [impact['total_impact'] for impact in self.aggregated_results[effect_type][last_year]['sector_impacts']]
            ax4.hist(impacts, bins=20, alpha=0.7, color='purple', edgecolor='black')
            ax4.set_title(f'Impact Distribution ({last_year})')
            ax4.set_xlabel('Total Impact (Million KRW)')
            ax4.set_ylabel('Number of Sectors')
            ax4.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(f'{output_dir}/detailed_{effect_type}.png', dpi=300, bbox_inches='tight')
        plt.show()

    def display_summary(self, effect_type: str = None, year: int = None):
        """Display summary results."""
        if effect_type and year:
            # Display specific effect type and year
            if effect_type in self.aggregated_results and year in self.aggregated_results[effect_type]:
                data = self.aggregated_results[effect_type][year]
                print(f"\n{'='*60}")
                print(f"SUMMARY: {effect_type.upper()} - YEAR {year}")
                print(f"{'='*60}")
                print(f"Total Aggregate Impact: {data['total_aggregate_impact']:,.2f} Million KRW")
                print(f"Average Impact per Scenario: {data['avg_aggregate_impact']:,.2f} Million KRW")
                print(f"Number of Scenarios: {data['scenario_count']}")
                print(f"Affected Sectors: {data['num_affected_sectors']}")

                print(f"\nTop 10 Affected Sectors:")
                print(f"{'Code':<8} {'Sector':<40} {'Total Impact':>15} {'Avg Impact':>15}")
                print("-" * 80)

                for impact in data['sector_impacts'][:10]:
                    print(f"{impact['sector_code']:<8} {impact['sector_name']:<40} "
                          f"{impact['total_impact']:>15,.2f} {impact['avg_impact']:>15,.2f}")
        else:
            # Display overall summary
            print(f"\n{'='*60}")
            print(f"SCENARIO ANALYSIS OVERALL SUMMARY")
            print(f"{'='*60}")
            print(f"Effect Types Analyzed: {list(self.aggregated_results.keys())}")

            for effect_type in self.aggregated_results.keys():
                if not self.aggregated_results[effect_type]:
                    continue

                years = sorted(self.aggregated_results[effect_type].keys())
                print(f"\n{effect_type}:")
                print(f"  Years: {years}")
                print(f"  Total Years: {len(years)}")

                if years:
                    last_year_data = self.aggregated_results[effect_type][years[-1]]
                    print(f"  Latest Year ({years[-1]}) Total Impact: {last_year_data['total_aggregate_impact']:,.2f} Million KRW")

    def integrate_sectors_1610_4506(self, effect_types: List[str] = None):
        """
        Integrate results from sectors 1610 and 4506 (IO Table) by summing impacts for each sector code.

        Args:
            effect_types: List of effect types to integrate. If None, uses IO table effect types.

        Returns:
            Dictionary with integrated results for each effect type and year
        """
        if effect_types is None:
            effect_types = ['indirect_prod', 'indirect_import', 'value_added', 'jobcoeff', 'directemploycoeff']

        print("Integrating sectors 1610 and 4506 (sector-by-sector)...")

        # Find scenario indices for 1610 and 4506
        idx_1610 = None
        idx_4506 = None

        for idx, row in self.scenarios_data.iterrows():
            sector = str(row['sector'])
            if sector == '1610':
                idx_1610 = idx
            elif sector == '4506':
                idx_4506 = idx

        if idx_1610 is None or idx_4506 is None:
            print("Could not find scenarios for sectors 1610 and/or 4506")
            return None

        # Create integrated results
        integrated_results = {}

        for effect_type in effect_types:
            if effect_type not in self.results:
                continue

            integrated_results[effect_type] = {}

            for year in self.results[effect_type].keys():
                scenario_key_1610 = f"scenario_{idx_1610}"
                scenario_key_4506 = f"scenario_{idx_4506}"

                # Get results for both sectors
                result_1610 = self.results[effect_type][year].get(scenario_key_1610)
                result_4506 = self.results[effect_type][year].get(scenario_key_4506)

                if not result_1610 or not result_4506:
                    continue

                # Merge the impacts sector-by-sector (summing for each sector code)
                combined_impacts = {}

                # Add impacts from 1610
                for impact in result_1610['result']['impacts']:
                    sector_code = str(impact['sector_code'])
                    combined_impacts[sector_code] = {
                        'sector_code': sector_code,
                        'sector_name': impact['sector_name'],
                        'impact': impact['impact']
                    }

                # Add impacts from 4506 (sum if sector exists, add new if not)
                for impact in result_4506['result']['impacts']:
                    sector_code = str(impact['sector_code'])
                    if sector_code in combined_impacts:
                        # Sum the impacts for this sector
                        combined_impacts[sector_code]['impact'] += impact['impact']
                    else:
                        # New sector from 4506
                        combined_impacts[sector_code] = {
                            'sector_code': sector_code,
                            'sector_name': impact['sector_name'],
                            'impact': impact['impact']
                        }

                # Convert to list and sort by absolute impact
                impacts_list = list(combined_impacts.values())
                impacts_list.sort(key=lambda x: abs(x['impact']), reverse=True)

                # Calculate total impact
                total_impact = sum([imp['impact'] for imp in impacts_list])

                integrated_results[effect_type][year] = {
                    'impacts': impacts_list,
                    'total_impact': total_impact,
                    'num_affected_sectors': len(impacts_list)
                }

        return integrated_results

    def integrate_hydrogen_H2S_H2T(self, effect_types: List[str] = None):
        """
        Integrate results from hydrogen scenarios H2S and H2T by summing impacts for each sector code.

        Args:
            effect_types: List of effect types to integrate. If None, uses hydrogen effect types.

        Returns:
            Dictionary with integrated results for each effect type and year
        """
        if effect_types is None:
            effect_types = ['productioncoeff', 'valueaddedcoeff', 'jobcoeff', 'directemploycoeff']

        print("Integrating hydrogen scenarios H2S and H2T (sector-by-sector)...")

        # Find scenario indices for H2S and H2T
        idx_H2S = None
        idx_H2T = None

        for idx, row in self.scenarios_data.iterrows():
            sector = str(row['sector'])
            input_table = str(row['input'])
            if 'hydrogen' in input_table.lower():
                if sector == 'H2S':
                    idx_H2S = idx
                elif sector == 'H2T':
                    idx_H2T = idx

        if idx_H2S is None or idx_H2T is None:
            print("Could not find scenarios for H2S and/or H2T")
            return None

        # Create integrated results
        integrated_results = {}

        for effect_type in effect_types:
            if effect_type not in self.results:
                continue

            integrated_results[effect_type] = {}

            for year in self.results[effect_type].keys():
                scenario_key_H2S = f"scenario_{idx_H2S}"
                scenario_key_H2T = f"scenario_{idx_H2T}"

                # Get results for both scenarios
                result_H2S = self.results[effect_type][year].get(scenario_key_H2S)
                result_H2T = self.results[effect_type][year].get(scenario_key_H2T)

                if not result_H2S or not result_H2T:
                    continue

                # Merge the impacts sector-by-sector (summing for each sector code)
                combined_impacts = {}

                # Add impacts from H2S
                for impact in result_H2S['result']['impacts']:
                    sector_code = str(impact['sector_code'])
                    combined_impacts[sector_code] = {
                        'sector_code': sector_code,
                        'sector_name': impact['sector_name'],
                        'impact': impact['impact']
                    }

                # Add impacts from H2T (sum if sector exists, add new if not)
                for impact in result_H2T['result']['impacts']:
                    sector_code = str(impact['sector_code'])
                    if sector_code in combined_impacts:
                        # Sum the impacts for this sector
                        combined_impacts[sector_code]['impact'] += impact['impact']
                    else:
                        # New sector from H2T
                        combined_impacts[sector_code] = {
                            'sector_code': sector_code,
                            'sector_name': impact['sector_name'],
                            'impact': impact['impact']
                        }

                # Convert to list and sort by absolute impact
                impacts_list = list(combined_impacts.values())
                impacts_list.sort(key=lambda x: abs(x['impact']), reverse=True)

                # Calculate total impact
                total_impact = sum([imp['impact'] for imp in impacts_list])

                integrated_results[effect_type][year] = {
                    'impacts': impacts_list,
                    'total_impact': total_impact,
                    'num_affected_sectors': len(impacts_list)
                }

        return integrated_results

    def save_integrated_scenarios(self, output_dir: str = 'output'):
        """
        Save integrated scenario results to CSV files for both 1610+4506 and H2S+H2T.
        Each CSV contains sector-by-sector impacts across all years.
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        print(f"Saving integrated scenario results to {output_dir}/...")

        # Integrate 1610 + 4506
        integrated_io = self.integrate_sectors_1610_4506()
        if integrated_io:
            self._save_integrated_csv(integrated_io, '1610_4506', 'iotable_2020', output_dir)

        # Integrate H2S + H2T
        integrated_h2 = self.integrate_hydrogen_H2S_H2T()
        if integrated_h2:
            self._save_integrated_csv(integrated_h2, 'H2S_H2T', 'hydrogentable_2020', output_dir)

        print("Integrated scenarios saved successfully!")

    def _save_integrated_csv(self, integrated_results: Dict, scenario_name: str,
                            input_table: str, output_dir: str):
        """
        Helper function to save integrated results to CSV files.

        Args:
            integrated_results: Dictionary of integrated results (from integrate methods)
            scenario_name: Name of the integrated scenario (e.g., '1610_4506' or 'H2S_H2T')
            input_table: Input table name
            output_dir: Output directory
        """
        for effect_type, year_results in integrated_results.items():
            if not year_results:
                continue

            # Sort years
            sorted_years = sorted(year_results.keys())

            # Collect all unique output sectors across all years
            all_output_sectors = {}
            for year, result in year_results.items():
                for impact in result['impacts']:
                    sector_code = str(impact['sector_code'])
                    sector_name = impact['sector_name']
                    if sector_code not in all_output_sectors:
                        all_output_sectors[sector_code] = sector_name

            # Create matrix data (rows = output sectors, columns = years)
            matrix_data = []
            for sector_code, sector_name in all_output_sectors.items():
                row = {
                    'Sector_Code': sector_code,
                    'Sector_Name': sector_name
                }

                # Add impact values for each year
                for year in sorted_years:
                    impact_value = 0.0
                    result = year_results[year]

                    for impact in result['impacts']:
                        if str(impact['sector_code']) == sector_code:
                            impact_value = impact['impact']
                            break

                    row[str(year)] = impact_value

                matrix_data.append(row)

            # Create DataFrame
            if matrix_data:
                df = pd.DataFrame(matrix_data)

                # Sort by the latest year's absolute impact
                latest_year_col = str(sorted_years[-1])
                if latest_year_col in df.columns:
                    df['abs_latest'] = df[latest_year_col].abs()
                    df = df.sort_values('abs_latest', ascending=False)
                    df = df.drop('abs_latest', axis=1)

                # Create filename
                filename = f"{output_dir}/scenario_{effect_type}_{scenario_name}_{input_table}.csv"

                # Save to CSV with UTF-8-BOM encoding
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"Created {filename}")


if __name__ == "__main__":
    # Example usage
    analyzer = ScenarioAnalyzer()

    # Run analysis for all scenarios
    analyzer.run_all_scenarios()

    # Display summary
    analyzer.display_summary()

    # Create output tables and charts
    analyzer.create_summary_tables()
    analyzer.create_summary_charts()

    print("\nScenario analysis complete! Check the 'output' directory for detailed results.")