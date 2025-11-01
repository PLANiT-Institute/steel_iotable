"""
Visualization Module for Steel I-O Table Analysis

Leverages existing methods from HydrogenTableAnalyzer, ScenarioAnalyzer, and IOTableAnalyzer.
"""

import plotly.graph_objects as go
import plotly.io as pio
from typing import List

# Set default Plotly template
pio.templates.default = "plotly_white"


class Visualization:
    """Visualization class using existing analyzer methods."""

    def __init__(self, scenario_analyzer):
        """
        Initialize with a ScenarioAnalyzer that has already run analysis.

        Args:
            scenario_analyzer: ScenarioAnalyzer instance with results
        """
        self.scenario_analyzer = scenario_analyzer

    def create_io_yearly_trends(self, effect_type: str, scenarios: List[str] = None,
                                show_fig: bool = True):
        """
        Create yearly trends for IO table scenarios.
        Uses scenario_analyzer.integrate_sectors_1610_4506() for integrated data.

        Args:
            effect_type: 'indirect_prod', 'indirect_import', 'value_added', 'jobcoeff', 'directemploycoeff'
            scenarios: List of scenarios (default: ['1610', '4506', '1610&4506'])
            show_fig: Whether to display the figure

        Returns:
            Plotly Figure
        """
        if scenarios is None:
            scenarios = ['1610', '4506', '1610&4506']

        effect_info = {
            'indirect_prod': {'label': 'Indirect Production', 'unit': 'Billion Won'},
            'indirect_import': {'label': 'Import', 'unit': 'Billion Won'},
            'value_added': {'label': 'Value Added', 'unit': 'Billion Won'},
            'jobcoeff': {'label': 'Job Creation', 'unit': 'Person'},
            'directemploycoeff': {'label': 'Direct Employment', 'unit': 'Person'}
        }

        fig = go.Figure()

        # Get integrated results if needed
        integrated_io = None
        if '1610&4506' in scenarios:
            integrated_io = self.scenario_analyzer.integrate_sectors_1610_4506()

        for scenario in scenarios:
            if scenario == '1610&4506' and integrated_io:
                # Use integration method results
                if effect_type in integrated_io:
                    years = sorted(integrated_io[effect_type].keys())
                    values = [integrated_io[effect_type][y]['total_impact'] /
                             (1000 if effect_type in ['indirect_prod', 'indirect_import', 'value_added'] else 1)
                             for y in years]

                    fig.add_trace(go.Scatter(
                        x=years, y=values, mode='lines+markers',
                        name='1610 & 4506', line=dict(width=3), marker=dict(size=8)
                    ))
            else:
                # Extract from stored results
                years, values = self._get_scenario_data(scenario, effect_type)
                if years:
                    fig.add_trace(go.Scatter(
                        x=years, y=values, mode='lines+markers',
                        name=f'Sector {scenario}', line=dict(width=3), marker=dict(size=8)
                    ))

        fig.update_layout(
            title=f'{effect_info[effect_type]["label"]} - IO Table Yearly Trends',
            xaxis_title='Year',
            yaxis_title=f'{effect_info[effect_type]["label"]} ({effect_info[effect_type]["unit"]})',
            height=600, hovermode='x unified', template='plotly_white',
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )

        if show_fig:
            fig.show()
        return fig

    def create_hydrogen_yearly_trends(self, effect_type: str, scenarios: List[str] = None,
                                      show_fig: bool = True):
        """
        Create yearly trends for hydrogen scenarios.
        Uses scenario_analyzer.integrate_hydrogen_H2S_H2T() for integrated data.

        Args:
            effect_type: 'productioncoeff', 'valueaddedcoeff', 'jobcoeff', 'directemploycoeff'
            scenarios: List of scenarios (default: ['H2S', 'H2T', 'H2S&H2T'])
            show_fig: Whether to display the figure

        Returns:
            Plotly Figure
        """
        if scenarios is None:
            scenarios = ['H2S', 'H2T', 'H2S&H2T']

        effect_info = {
            'productioncoeff': {'label': 'Indirect Production', 'unit': 'Billion Won'},
            'valueaddedcoeff': {'label': 'Value Added', 'unit': 'Billion Won'},
            'jobcoeff': {'label': 'Job Creation', 'unit': 'Billion Won'},
            'directemploycoeff': {'label': 'Direct Employment', 'unit': 'Person'}
        }

        fig = go.Figure()

        # Get integrated results if needed
        integrated_h2 = None
        if 'H2S&H2T' in scenarios:
            integrated_h2 = self.scenario_analyzer.integrate_hydrogen_H2S_H2T()

        for scenario in scenarios:
            if scenario == 'H2S&H2T' and integrated_h2:
                # Use integration method results
                if effect_type in integrated_h2:
                    years = sorted(integrated_h2[effect_type].keys())
                    values = [integrated_h2[effect_type][y]['total_impact'] /
                             (1000 if effect_type != 'directemploycoeff' else 1)
                             for y in years]

                    fig.add_trace(go.Scatter(
                        x=years, y=values, mode='lines+markers',
                        name='H2S & H2T', line=dict(width=3), marker=dict(size=8)
                    ))
            else:
                # Extract from stored results
                years, values = self._get_scenario_data(scenario, effect_type)
                if years:
                    fig.add_trace(go.Scatter(
                        x=years, y=values, mode='lines+markers',
                        name=scenario, line=dict(width=3), marker=dict(size=8)
                    ))

        fig.update_layout(
            title=f'{effect_info[effect_type]["label"]} - Hydrogen Scenarios Yearly Trends',
            xaxis_title='Year',
            yaxis_title=f'{effect_info[effect_type]["label"]} ({effect_info[effect_type]["unit"]})',
            height=600, hovermode='x unified', template='plotly_white',
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )

        if show_fig:
            fig.show()
        return fig

    def _get_scenario_data(self, sector: str, effect_type: str):
        """Extract data from scenario_analyzer.results."""
        # Find scenario index
        idx = None
        for i, row in self.scenario_analyzer.scenarios_data.iterrows():
            if str(row['sector']) == sector:
                idx = i
                break

        if idx is None or effect_type not in self.scenario_analyzer.results:
            return [], []

        scenario_key = f"scenario_{idx}"
        years = sorted(self.scenario_analyzer.results[effect_type].keys())
        values = []

        for year in years:
            if scenario_key in self.scenario_analyzer.results[effect_type][year]:
                total = self.scenario_analyzer.results[effect_type][year][scenario_key]['total_impact']
                # Convert units
                if effect_type in ['indirect_prod', 'indirect_import', 'value_added',
                                  'productioncoeff', 'valueaddedcoeff', 'jobcoeff']:
                    values.append(total / 1000)
                else:
                    values.append(total)
            else:
                values.append(0)

        return years, values

    def create_all_trends(self, output_dir: str = 'output/plotly_charts', save_html: bool = True):
        """
        Create all yearly trends visualizations (IO + Hydrogen).

        Args:
            output_dir: Directory to save HTML files
            save_html: Whether to save HTML files
        """
        import os
        if save_html:
            os.makedirs(f"{output_dir}/yearly_trends", exist_ok=True)
            os.makedirs(f"{output_dir}/yearly_trends_hydrogen", exist_ok=True)

        print("Creating all yearly trends visualizations...")
        print("=" * 80)

        # IO trends
        io_effects = ['indirect_prod', 'indirect_import', 'value_added', 'jobcoeff', 'directemploycoeff']
        io_labels = {
            'indirect_prod': 'indirect_production',
            'indirect_import': 'import',
            'value_added': 'value_added',
            'jobcoeff': 'job_creation',
            'directemploycoeff': 'direct_employment'
        }

        for effect in io_effects:
            print(f"\nCreating IO {io_labels[effect]} trends...")
            fig = self.create_io_yearly_trends(effect, show_fig=False)
            if save_html:
                filename = f"{output_dir}/yearly_trends/yearly_trends_{io_labels[effect]}.html"
                fig.write_html(filename)
                print(f"  ✅ Saved: {filename}")

        # Hydrogen trends
        h2_effects = ['productioncoeff', 'valueaddedcoeff', 'jobcoeff', 'directemploycoeff']
        h2_labels = {
            'productioncoeff': 'indirect_production',
            'valueaddedcoeff': 'value_added',
            'jobcoeff': 'job_creation',
            'directemploycoeff': 'direct_employment'
        }

        for effect in h2_effects:
            print(f"\nCreating Hydrogen {h2_labels[effect]} trends...")
            fig = self.create_hydrogen_yearly_trends(effect, show_fig=False)
            if save_html:
                filename = f"{output_dir}/yearly_trends_hydrogen/hydrogen_yearly_trends_{h2_labels[effect]}.html"
                fig.write_html(filename)
                print(f"  ✅ Saved: {filename}")

        print("\n" + "=" * 80)
        print("All yearly trends created!")
        print("=" * 80)


if __name__ == "__main__":
    from scenario_analyzer import ScenarioAnalyzer

    print("Loading and running scenario analysis...")
    analyzer = ScenarioAnalyzer()
    analyzer.run_all_scenarios()

    print("\nCreating visualizations...")
    viz = Visualization(analyzer)
    viz.create_all_trends(save_html=True)

    print("\nDone!")
