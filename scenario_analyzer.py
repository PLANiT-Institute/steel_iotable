import pandas as pd
import numpy as np
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import seaborn as sns
from libs.hydrogen_analyzer import HydrogenTableAnalyzer
from libs.io_analyzer import IOTableAnalyzer

class ScenarioAnalyzer:
    def __init__(self, scenarios_file: str = 'data/scenarios.xlsx'):
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
                sector_df.to_excel(writer, sheet_name='Sector_Impacts_by_Year', index=False)

            print(f"Created {filename}")

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