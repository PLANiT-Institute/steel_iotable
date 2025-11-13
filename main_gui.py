from re import U
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from libs.io_analyzer import IOTableAnalyzer
from libs.hydrogen_analyzer import HydrogenTableAnalyzer
from libs.scenario_analyzer import ScenarioAnalyzer

# Define the target years used throughout the analysis
target_years = [2026, 2030, 2040, 2050]

# Configure Streamlit page
st.set_page_config(
    page_title="Hydrogen-reduced steel Input-Output Analysis",
    page_icon="🏭",
    layout="wide"
)

@st.cache_data
def load_analyzer():
    """Load the analyzer with caching to avoid reloading data."""
    return IOTableAnalyzer()

@st.cache_data
def load_hydrogen_analyzer():
    """Load the hydrogen analyzer with caching to avoid reloading data."""
    return HydrogenTableAnalyzer()

@st.cache_data
def load_scenario_analyzer():
    """Load the scenario analyzer with caching."""
    return ScenarioAnalyzer()

def show_scenarios():
    st.title("🎯 Scenarios")
    st.markdown("---")
    # Discover all Excel files in "data" folder whose name starts with "scenario_"
    data_folder = Path("data")
    scenario_files = sorted([f for f in data_folder.glob("scenario_*.xlsx")])
    if not scenario_files:
        st.warning("No scenario files found in the 'data' directory. Please add files named like scenario_x_xxxx.xlsx.")
        return

    # Load all scenario dataframes into a dictionary: {filename: dataframe}
    scenario_dataframes = {}
    for f in scenario_files:
        try:
            df = pd.read_excel(f)
            scenario_dataframes[f.name] = df
        except Exception as e:
            st.error(f"Failed to load {f.name}: {e}")

    # Optionally, display some feedback or all loaded dataframes
    st.info(f"Loaded {len(scenario_dataframes)} scenario files from the data folder.")
    # Preview option: Let user select and preview any scenario file
    if scenario_dataframes:
        file_to_preview = st.selectbox(
            "Select a scenario file to preview",
            list(scenario_dataframes.keys())
        )
        if st.checkbox("Preview selected scenario file"):
            st.dataframe(scenario_dataframes[file_to_preview])

    # Let user pick one or more scenarios
    scenario_names = [f.name for f in scenario_files]
    selected_scenario = st.selectbox("Select a Scenario File", scenario_names, help="Pick a scenario Excel file for batch analysis")

    selected_path = data_folder / selected_scenario

    st.info(f"You selected: `{selected_scenario}`")
    # User option: preview content
    if st.checkbox("Preview scenario file content"):
        try:
            scenario_df = pd.read_excel(selected_path)
            st.dataframe(scenario_df)
        except Exception as e:
            st.error(f"Failed to load scenario file: {e}")
            return


def run_scenario_analysis():
    """Run scenario analysis and store results in session state."""
    st.title("🚀 Run Scenario Analysis")
    st.markdown("---")
    st.markdown("Automatically analyze all scenarios from Data_v10.xlsx")

    # Fixed data file
    data_folder = Path("data")
    data_file = data_folder / "Data_v10.xlsx"

    # Check if file exists
    if not data_file.exists():
        st.error(f"❌ Data file not found: {data_file}")
        st.info("Please ensure Data_v10.xlsx exists in the data folder.")
        return

    # Show file info
    st.info(f"📄 Data file: `Data_v10.xlsx`")

    # Show which file is currently loaded
    if 'current_scenario_file' in st.session_state:
        current = st.session_state.current_scenario_file
        if current == "Data_v10.xlsx":
            st.success(f"✅ Currently loaded: `{current}`")
        else:
            st.warning(f"⚠️ Different file loaded: `{current}`")

    # Show preview option
    if st.checkbox("Preview scenario sheets", key="preview_run_analysis"):
        try:
            excel_file = pd.ExcelFile(data_file)
            scenario_sheets = [sheet for sheet in excel_file.sheet_names if sheet.lower().startswith('scenario')]
            st.write(f"**Found {len(scenario_sheets)} scenario sheets:**")
            for sheet_name in scenario_sheets:
                with st.expander(f"📋 {sheet_name}"):
                    scenario_df = pd.read_excel(data_file, sheet_name=sheet_name)
                    st.dataframe(scenario_df)
        except Exception as e:
            st.error(f"Failed to load data file: {e}")

    st.markdown("---")

    # Display current status
    if st.session_state.get('scenario_results'):
        st.info("✅ Scenario analysis results are available in session.")
        # Show which scenario sheets are loaded
        if 'scenario_analyzer' in st.session_state:
            analyzer = st.session_state.scenario_analyzer
            if hasattr(analyzer, 'scenario_sheet_names'):
                st.write(f"**Loaded scenario sheets:** {', '.join(analyzer.scenario_sheet_names)}")
    else:
        st.warning("⚠️ No scenario analysis results available yet.")

    # Run analysis button
    if st.button("🚀 Run Complete Scenario Analysis", type="primary", use_container_width=True):
        with st.spinner(f"Running scenario analysis for Data_v10.xlsx..."):
            try:
                # Initialize scenario analyzer with Data_v10.xlsx
                scenario_analyzer = ScenarioAnalyzer(scenarios_file=str(data_file))

                # Run all scenarios
                st.info("Running scenario analysis... This may take a few minutes.")
                scenario_analyzer.run_all_scenarios()

                # Store results in session state
                st.session_state.scenario_analyzer = scenario_analyzer
                st.session_state.scenario_results = scenario_analyzer.aggregated_results
                st.session_state.current_scenario_file = "Data_v10.xlsx"

                st.success(f"✅ Analysis complete for Data_v10.xlsx!")

                # Show summary of results
                st.markdown("### 📊 Analysis Summary")
                st.write(f"**Scenario sheets loaded:** {', '.join(scenario_analyzer.scenario_sheet_names)}")

                effect_types = list(scenario_analyzer.aggregated_results.keys())
                st.write(f"**Effect types analyzed:** {len(effect_types)}")
                st.write(f"**Effect types:** {', '.join(effect_types)}")

                # Count years
                years_set = set()
                for effect_type in effect_types:
                    years_set.update(scenario_analyzer.aggregated_results[effect_type].keys())
                st.write(f"**Years covered:** {sorted(years_set)}")

            except Exception as e:
                st.error(f"Error running analysis: {str(e)}")
                st.exception(e)


def filter_results_by_scenario_sheet(scenario_analyzer, sheet_name):
    """Filter and aggregate results for a specific scenario sheet."""
    filtered_results = {}

    # Get all effect types from the original results
    effect_types = list(scenario_analyzer.results.keys())

    for effect_type in effect_types:
        filtered_results[effect_type] = {}

        if effect_type not in scenario_analyzer.results:
            continue

        # Process each year
        for year, year_data in scenario_analyzer.results[effect_type].items():
            # Filter scenarios by sheet name
            filtered_year_data = {}

            for scenario_key, scenario_data in year_data.items():
                # Extract scenario index
                scenario_idx = int(scenario_key.split('_')[1])
                scenario_row = scenario_analyzer.scenarios_data.iloc[scenario_idx]

                # Check if this scenario matches our sheet filter
                if scenario_row['scenario_sheet'] == sheet_name:
                    filtered_year_data[scenario_key] = scenario_data

            if filtered_year_data:
                # Aggregate the filtered results for this year
                all_sector_impacts = {}
                total_aggregate_impact = 0
                scenario_count = 0

                for scenario_key, scenario_data in filtered_year_data.items():
                    result = scenario_data['result']
                    total_aggregate_impact += result['total_impact']
                    scenario_count += 1

                    # Aggregate sector-level impacts
                    for impact in result['impacts']:
                        sector_code = str(impact['sector_code'])
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

                aggregated_impacts.sort(key=lambda x: abs(x['total_impact']), reverse=True)

                filtered_results[effect_type][year] = {
                    'total_aggregate_impact': total_aggregate_impact,
                    'scenario_count': scenario_count,
                    'avg_aggregate_impact': total_aggregate_impact / scenario_count if scenario_count > 0 else 0,
                    'num_affected_sectors': len(all_sector_impacts),
                    'sector_impacts': aggregated_impacts
                }

    return filtered_results


def filter_results_by_sectors(scenario_analyzer, sector_list):
    """Filter and aggregate results for specific sectors only."""
    filtered_results = {}

    # Get all effect types from the original results
    effect_types = list(scenario_analyzer.results.keys())

    for effect_type in effect_types:
        filtered_results[effect_type] = {}

        if effect_type not in scenario_analyzer.results:
            continue

        # Process each year
        for year, year_data in scenario_analyzer.results[effect_type].items():
            # Filter scenarios by sector
            filtered_year_data = {}

            for scenario_key, scenario_data in year_data.items():
                # Extract scenario index
                scenario_idx = int(scenario_key.split('_')[1])
                scenario_row = scenario_analyzer.scenarios_data.iloc[scenario_idx]

                # Check if this scenario matches our sector filter
                if str(scenario_row['sector']) in sector_list:
                    filtered_year_data[scenario_key] = scenario_data

            if filtered_year_data:
                # Aggregate the filtered results for this year
                all_sector_impacts = {}
                total_aggregate_impact = 0
                scenario_count = 0

                for scenario_key, scenario_data in filtered_year_data.items():
                    result = scenario_data['result']
                    total_aggregate_impact += result['total_impact']
                    scenario_count += 1

                    # Aggregate sector-level impacts
                    for impact in result['impacts']:
                        sector_code = str(impact['sector_code'])
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

                aggregated_impacts.sort(key=lambda x: abs(x['total_impact']), reverse=True)

                filtered_results[effect_type][year] = {
                    'total_aggregate_impact': total_aggregate_impact,
                    'scenario_count': scenario_count,
                    'avg_aggregate_impact': total_aggregate_impact / scenario_count if scenario_count > 0 else 0,
                    'num_affected_sectors': len(all_sector_impacts),
                    'sector_impacts': aggregated_impacts
                }

    return filtered_results


def show_integrated_tables():
    """Display integrated tables combining IO sectors 1610 and 4506."""
    st.subheader("🔗 Integrated Table Analysis")

    # Check if scenario analysis has been run
    if not st.session_state.get('scenario_results') or not st.session_state.get('scenario_analyzer'):
        st.warning("⚠️ No scenario analysis results available. Please run scenario analysis first.")
        st.info("👈 Go to the 'Run Analysis' tab to generate data.")
        return

    scenario_analyzer = st.session_state.scenario_analyzer

    # Filter results for sectors 1610 and 4506 only
    results = filter_results_by_sectors(scenario_analyzer, ['1610', '4506'])

    # SUMMARY TABLES SECTION
    st.markdown("### 📋 Summary Table")

    summary_years = target_years

    # Define effect types to include in summary
    effect_columns = {
        'indirect_prod': 'Indirect Production Impact (Million KRW)',
        'indirect_import': 'Indirect Import Impact (Million KRW)',
        'value_added': 'Value Added Impact (Million KRW)',
        'jobcoeff': 'Job Creation Impact (Persons)'
    }

    # Build consolidated summary table
    summary_data = []
    for year in summary_years:
        row = {'Year': year}

        for effect_type, column_name in effect_columns.items():
            if effect_type in results and year in results[effect_type]:
                # Get total aggregate impact from the scenario_analyzer results
                total_impact = results[effect_type][year]['total_aggregate_impact']
                row[column_name] = total_impact
            else:
                row[column_name] = 0

        summary_data.append(row)

    if summary_data:
        summary_df = pd.DataFrame(summary_data)

        # Remove columns where all values are 0
        cols_to_keep = ['Year']
        for col in summary_df.columns:
            if col != 'Year':
                if summary_df[col].sum() != 0:  # Keep column if sum is not 0
                    cols_to_keep.append(col)
        summary_df = summary_df[cols_to_keep]

        # Format for display
        display_df = summary_df.copy()
        for col in display_df.columns:
            if col != 'Year':
                display_df[col] = display_df[col].apply(lambda x: f"{x:,.2f}" if x != 0 else "0.00")

        st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # FULL TABLES SECTION
    st.markdown("### 📊 Full Tables")

    # Get ALL years from results
    all_years_set = set()
    for effect_type in results.keys():
        if results[effect_type]:
            all_years_set.update(results[effect_type].keys())
    all_years = sorted(all_years_set)

    # Get all effect types that have results
    available_effects = [effect for effect in results.keys() if results[effect]]

    if not available_effects:
        st.error("No effect types available in results.")
        return

    # Effect type descriptions
    effect_descriptions = {
        'indirect_prod': '💰 Indirect Production Effects',
        'indirect_import': '🌐 Indirect Import Effects',
        'value_added': '💎 Value Added Effects',
        'productioncoeff': '⚡ Production Coefficient (H2)',
        'valueaddedcoeff': '💎 Value Added Coefficient (H2)',
        'jobcoeff': '👥 Job Creation Effects',
        'directemploycoeff': '👔 Direct Employment Effects'
    }

    # Define all effect columns
    all_effect_columns = {
        'indirect_prod': 'Indirect Production (Million KRW)',
        'indirect_import': 'Indirect Import (Million KRW)',
        'value_added': 'Value Added (Million KRW)',
        'jobcoeff': 'Job Creation (Persons)',
        'directemploycoeff': 'Direct Employment (Persons)'
    }

    # Build consolidated full table

    full_data = []
    for year in all_years:
        row = {'Year': year}

        for effect_type, column_name in all_effect_columns.items():
            if effect_type in available_effects and year in results[effect_type]:
                # Get total aggregate impact from the scenario_analyzer results
                total_impact = results[effect_type][year]['total_aggregate_impact']
                row[column_name] = total_impact
            else:
                row[column_name] = 0

        full_data.append(row)

    if full_data:
        full_df = pd.DataFrame(full_data)

        # Format for display
        display_df = full_df.copy()
        for col in display_df.columns:
            if col != 'Year':
                display_df[col] = display_df[col].apply(lambda x: f"{x:,.2f}" if x != 0 else "0.00")

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Download button (Excel)
        try:
            from io import BytesIO

            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                full_df.to_excel(writer, sheet_name='Consolidated Full Data', index=False)

            buffer.seek(0)

            st.download_button(
                label=f"📥 Download Consolidated Full Table (Excel)",
                data=buffer,
                file_name=f"integrated_full_consolidated_table.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"download_integrated_full_consolidated"
            )
        except ImportError:
            # Fallback to CSV
            csv = full_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label=f"📥 Download Consolidated Full Table (CSV)",
                data=csv,
                file_name=f"integrated_full_consolidated_table.csv",
                mime="text/csv",
                key=f"download_integrated_full_consolidated"
            )

    st.markdown("---")
    
    st.markdown("#### 📋 Detailed Analysis by Effect Type")

    # Create tabs for each available effect type
    tab_names = [effect_descriptions.get(effect, effect) for effect in available_effects]
    effect_tabs = st.tabs(tab_names)

    for i, effect_type in enumerate(available_effects):
        with effect_tabs[i]:
            st.subheader(f"{effect_descriptions.get(effect_type, effect_type)}")

            if not results[effect_type]:
                st.warning(f"No data available for {effect_type}")
                continue

            # Create sector impact matrix for ALL years
            st.markdown("#### 🎯 Sector Impacts by Year (All Years)")

            # Collect all unique sectors
            all_sectors = set()
            for year in all_years:
                if year in results[effect_type]:
                    for impact in results[effect_type][year]['sector_impacts']:
                        all_sectors.add(str(impact['sector_code']))

            if all_sectors:
                # Create sector matrix
                sector_matrix = []
                for sector_code in sorted(all_sectors):
                    row = {'Sector Code': sector_code, 'Sector Name': ''}

                    # Add code_h and product_h if IO analyzer available
                    if hasattr(scenario_analyzer, 'io_analyzer') and scenario_analyzer.io_analyzer:
                        if effect_type not in ['jobcoeff', 'directemploycoeff']:
                            code_h = scenario_analyzer.io_analyzer.basic_to_code_h.get(sector_code, '')
                            product_h = scenario_analyzer.io_analyzer.code_h_to_product_h.get(code_h, '') if code_h else ''
                            row['Code_H'] = code_h
                            row['Category_H'] = product_h

                    # Add impact values for each year (ALL YEARS)
                    for year in all_years:
                        if year in results[effect_type]:
                            year_data = results[effect_type][year]
                            impact_value = 0
                            sector_name = ''
                            
                            for impact in year_data['sector_impacts']:
                                if str(impact['sector_code']) == sector_code:
                                    impact_value = impact['total_impact']
                                    sector_name = impact['sector_name']
                                    break
                            
                            row[str(year)] = impact_value
                            if not row['Sector Name']:
                                row['Sector Name'] = sector_name
                        else:
                            row[str(year)] = 0
                    
                    sector_matrix.append(row)
                
                sector_df = pd.DataFrame(sector_matrix)

                # Format numeric columns for display
                display_df = sector_df.copy()
                for year in all_years:
                    if str(year) in display_df.columns:
                        display_df[str(year)] = display_df[str(year)].apply(lambda x: f"{x:,.2f}" if isinstance(x, (int, float)) else x)

                # Display with option to show top N sectors
                top_n = st.slider(
                    "Show top N sectors by total impact",
                    min_value=10,
                    max_value=len(sector_df),
                    value=min(20, len(sector_df)),
                    step=10,
                    key=f"slider_{effect_type}"
                )

                # Calculate total impact across years for sorting
                year_cols = [str(year) for year in all_years if str(year) in sector_df.columns]
                sector_df['total_across_years'] = sector_df[year_cols].sum(axis=1)
                sector_df = sector_df.sort_values('total_across_years', ascending=False)
                
                # Remove the sorting column from display
                display_df = sector_df.drop(columns=['total_across_years']).head(top_n)
                
                # Format display
                for year in target_years:
                    if str(year) in display_df.columns:
                        display_df[str(year)] = display_df[str(year)].apply(lambda x: f"{x:,.2f}" if isinstance(x, (int, float)) else x)
                
                st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)

                # Download button for detailed data (Excel)
                try:
                    from io import BytesIO

                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        # Export the sector data
                        export_df = sector_df.drop(columns=['total_across_years'])
                        export_df.to_excel(writer, sheet_name=effect_type[:30], index=False)

                    buffer.seek(0)

                    st.download_button(
                        label=f"📥 Download {effect_type} Detailed Sector Data (Excel)",
                        data=buffer,
                        file_name=f"integrated_sectors_{effect_type}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"download_detailed_{effect_type}"
                    )
                except ImportError:
                    # Fallback to CSV if openpyxl not available
                    csv_detailed = sector_df.drop(columns=['total_across_years']).to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label=f"📥 Download {effect_type} Detailed Sector Data (CSV)",
                        data=csv_detailed,
                        file_name=f"integrated_sectors_{effect_type}.csv",
                        mime="text/csv",
                        key=f"download_detailed_{effect_type}"
                    )
            else:
                st.info("No sector impact data available for the selected years.")

    st.markdown("---")
    st.info("💡 Tip: Go to 'Run Analysis' tab to run analysis with different scenario files.")


def show_hydrogen_analysis():
    """Display hydrogen table analysis results for H2S and H2T."""
    st.subheader("⚡ Hydrogen Table Analysis")

    # Check if scenario analysis has been run
    if not st.session_state.get('scenario_results') or not st.session_state.get('scenario_analyzer'):
        st.warning("⚠️ No scenario analysis results available. Please run scenario analysis first.")
        st.info("👈 Go to the 'Run Analysis' tab to generate data.")
        return

    scenario_analyzer = st.session_state.scenario_analyzer

    # Filter results for H2S and H2T only
    results = filter_results_by_sectors(scenario_analyzer, ['H2S', 'H2T'])

    # Filter hydrogen-specific effect types
    hydrogen_effects = ['productioncoeff', 'valueaddedcoeff', 'jobcoeff', 'directemploycoeff']
    available_h2_effects = [effect for effect in hydrogen_effects if effect in results and results[effect]]

    if not available_h2_effects:
        st.warning("No hydrogen analysis results available.")
        return

    # SUMMARY TABLES SECTION
    st.markdown("### 📋 Summary Tables")

    summary_years = target_years

    # Define hydrogen effect columns
    h2_effect_columns = {
        'productioncoeff': 'Indirect production (Million KRW)',
        'valueaddedcoeff': 'Value-added creation (Million KRW)',
        'jobcoeff': 'Job Creation (Million KRW)',
        'directemploycoeff': 'Direct Employment (Persons)'
    }

    # Build consolidated summary table
    summary_data = []
    for year in summary_years:
        row = {'Year': year}

        for effect_type, column_name in h2_effect_columns.items():
            if effect_type in available_h2_effects and year in results[effect_type]:
                # Get total aggregate impact from the scenario_analyzer results
                total_impact = results[effect_type][year]['total_aggregate_impact']
                row[column_name] = total_impact
            else:
                row[column_name] = 0

        summary_data.append(row)

    if summary_data:
        summary_df = pd.DataFrame(summary_data)

        # Format for display
        display_df = summary_df.copy()
        for col in display_df.columns:
            if col != 'Year':
                display_df[col] = display_df[col].apply(lambda x: f"{x:,.2f}" if x != 0 else "0.00")

        st.dataframe(display_df, use_container_width=True, hide_index=True)
    st.markdown("---")

    # FULL TABLES SECTION
    st.markdown("### 📊 Full Tables (All Years)")

    # Get all years
    all_years_set = set()
    for effect_type in available_h2_effects:
        if results[effect_type]:
            all_years_set.update(results[effect_type].keys())
    all_years = sorted(all_years_set)

    # Define hydrogen effect columns for full table
    h2_effect_columns = {
        'productioncoeff': 'Production Coefficient (Million KRW)',
        'valueaddedcoeff': 'Value Added Coefficient (Million KRW)',
        'jobcoeff': 'Job Creation (Million KRW)',
        'directemploycoeff': 'Direct Employment (Persons)'
    }

    # Build consolidated full table
    full_data = []
    for year in all_years:
        row = {'Year': year}

        for effect_type, column_name in h2_effect_columns.items():
            if effect_type in available_h2_effects and year in results[effect_type]:
                # Get total aggregate impact from the scenario_analyzer results
                total_impact = results[effect_type][year]['total_aggregate_impact']
                row[column_name] = total_impact
            else:
                row[column_name] = 0

        full_data.append(row)

    if full_data:
        full_df = pd.DataFrame(full_data)

        # Format for display
        display_df = full_df.copy()
        for col in display_df.columns:
            if col != 'Year':
                display_df[col] = display_df[col].apply(lambda x: f"{x:,.2f}" if x != 0 else "0.00")

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Download button (Excel)
        try:
            from io import BytesIO

            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                full_df.to_excel(writer, sheet_name='H2 Full Data', index=False)

            buffer.seek(0)

            st.download_button(
                label=f"📥 Download H2 Full Table (Excel)",
                data=buffer,
                file_name=f"h2_full_consolidated_table.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"download_h2_full_consolidated"
            )
        except ImportError:
            # Fallback to CSV
            csv = full_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label=f"📥 Download H2 Full Table (CSV)",
                data=csv,
                file_name=f"h2_full_consolidated_table.csv",
                mime="text/csv",
                key=f"download_h2_full_consolidated"
            )


def filter_and_group_by_code_h(scenario_analyzer, sector_list):
    """Filter results by sectors and group by code_h categories."""
    filtered_results = {}

    # Get all effect types from the original results
    effect_types = list(scenario_analyzer.results.keys())

    for effect_type in effect_types:
        filtered_results[effect_type] = {}

        if effect_type not in scenario_analyzer.results:
            continue

        # Process each year
        for year, year_data in scenario_analyzer.results[effect_type].items():
            # Filter scenarios by sector
            filtered_year_data = {}

            for scenario_key, scenario_data in year_data.items():
                # Extract scenario index
                scenario_idx = int(scenario_key.split('_')[1])
                scenario_row = scenario_analyzer.scenarios_data.iloc[scenario_idx]

                # Check if this scenario matches our sector filter
                if str(scenario_row['sector']) in sector_list:
                    filtered_year_data[scenario_key] = scenario_data

            if filtered_year_data:
                # Aggregate the filtered results for this year, grouped by code_h
                all_code_h_impacts = {}
                total_aggregate_impact = 0
                scenario_count = 0

                for scenario_key, scenario_data in filtered_year_data.items():
                    result = scenario_data['result']
                    total_aggregate_impact += result['total_impact']
                    scenario_count += 1

                    # Aggregate sector-level impacts by code_h
                    for impact in result['impacts']:
                        sector_code = str(impact['sector_code'])
                        sector_name = impact['sector_name']
                        impact_value = impact['impact']

                        # Map to code_h
                        code_h = ''
                        product_h = ''
                        if hasattr(scenario_analyzer, 'io_analyzer') and scenario_analyzer.io_analyzer:
                            code_h = scenario_analyzer.io_analyzer.basic_to_code_h.get(sector_code, sector_code)
                            product_h = scenario_analyzer.io_analyzer.code_h_to_product_h.get(code_h, '') if code_h else ''

                        # Use code_h as the grouping key
                        group_key = code_h if code_h else sector_code

                        if group_key not in all_code_h_impacts:
                            all_code_h_impacts[group_key] = {
                                'code_h': code_h,
                                'product_h': product_h,
                                'total_impact': 0,
                                'scenario_count': 0
                            }

                        all_code_h_impacts[group_key]['total_impact'] += impact_value
                        all_code_h_impacts[group_key]['scenario_count'] += 1

                # Convert to sorted list
                aggregated_impacts = []
                for group_key, data in all_code_h_impacts.items():
                    aggregated_impacts.append({
                        'code_h': data['code_h'],
                        'product_h': data['product_h'],
                        'total_impact': data['total_impact'],
                        'avg_impact': data['total_impact'] / data['scenario_count'],
                        'scenario_count': data['scenario_count']
                    })

                aggregated_impacts.sort(key=lambda x: abs(x['total_impact']), reverse=True)

                filtered_results[effect_type][year] = {
                    'total_aggregate_impact': total_aggregate_impact,
                    'scenario_count': scenario_count,
                    'avg_aggregate_impact': total_aggregate_impact / scenario_count if scenario_count > 0 else 0,
                    'num_affected_categories': len(all_code_h_impacts),
                    'code_h_impacts': aggregated_impacts
                }

    return filtered_results


def show_total_tables():
    """Display total tables with 1610 + 4506 + H2 grouped by code_h categories."""
    st.subheader("📊 Total Table Summary (Coal+Renewable+H2)")

    # Check if scenario analysis has been run
    if not st.session_state.get('scenario_results') or not st.session_state.get('scenario_analyzer'):
        st.warning("⚠️ No scenario analysis results available. Please run scenario analysis first.")
        st.info("👈 Go to the 'Run Analysis' tab to generate data.")
        return

    scenario_analyzer = st.session_state.scenario_analyzer

    # Filter and group results for all sectors by code_h
    results = filter_and_group_by_code_h(scenario_analyzer, ['1610', '4506', 'H2S', 'H2T'])

    # Get all effect types that have results
    available_effects = [effect for effect in results.keys() if results[effect]]

    if not available_effects:
        st.warning("No analysis results available.")
        return

    # SUMMARY TABLES SECTION
    st.markdown("### 📋 Summary Tables")
    st.markdown("Combined impacts: Indirect Production, Value Added, Job Creation")

    summary_years = target_years

    # Build consolidated summary table with combined effects
    summary_data = []
    for year in summary_years:
        row = {'Year': year}

        # 1. Indirect Production = indirect_prod + productioncoeff (H2)
        indirect_prod_val = 0
        if 'indirect_prod' in available_effects and year in results['indirect_prod']:
            indirect_prod_val += results['indirect_prod'][year]['total_aggregate_impact']
        if 'productioncoeff' in available_effects and year in results['productioncoeff']:
            indirect_prod_val += results['productioncoeff'][year]['total_aggregate_impact']
        row['Indirect Production (Million KRW)'] = indirect_prod_val

        # 2. Indirect Import (IO only)
        if 'indirect_import' in available_effects and year in results['indirect_import']:
            row['Indirect Import (Million KRW)'] = results['indirect_import'][year]['total_aggregate_impact']
        else:
            row['Indirect Import (Million KRW)'] = 0

        # 3. Value Added = value_added + valueaddedcoeff (H2)
        value_added_val = 0
        if 'value_added' in available_effects and year in results['value_added']:
            value_added_val += results['value_added'][year]['total_aggregate_impact']
        if 'valueaddedcoeff' in available_effects and year in results['valueaddedcoeff']:
            value_added_val += results['valueaddedcoeff'][year]['total_aggregate_impact']
        row['Value Added (Million KRW)'] = value_added_val

        # 4. Job Creation = sum of jobcoeff for 1610+4506 and direct employment for H2S+H2T
        job_totals = scenario_analyzer.calculate_combined_job_creation(year)
        row['Job Creation (Persons)'] = job_totals['combined_total']

        summary_data.append(row)

    if summary_data:
        summary_df = pd.DataFrame(summary_data)

        # Remove columns where all values are 0 (except Job Creation - always show)
        cols_to_keep = ['Year']
        for col in summary_df.columns:
            if col != 'Year':
                # Always keep Job Creation column, even if zero
                if col == 'Job Creation (Persons)' or summary_df[col].sum() != 0:
                    cols_to_keep.append(col)
        summary_df = summary_df[cols_to_keep]

        # Format for display
        display_df = summary_df.copy()
        for col in display_df.columns:
            if col != 'Year':
                display_df[col] = display_df[col].apply(lambda x: f"{x:,.2f}" if x != 0 else "0.00")

        st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # DETAILED TABLES BY CODE_H
    st.markdown("### 📊 Detailed Impact by Code_H Category")

    # Effect type descriptions
    effect_descriptions = {
        'indirect_prod': '💰 Indirect Production Effects',
        'indirect_import': '🌐 Indirect Import Effects',
        'value_added': '💎 Value Added Effects',
        'productioncoeff': '⚡ Production Coefficient (H2)',
        'valueaddedcoeff': '💎 Value Added Coefficient (H2)',
        'directemploycoeff': '👔 Direct Employment Effects'
    }

    # Create tabs for each available effect type
    tab_names = [effect_descriptions.get(effect, effect) for effect in available_effects]
    effect_tabs = st.tabs(tab_names)

    for i, effect_type in enumerate(available_effects):
        with effect_tabs[i]:
            st.subheader(f"{effect_descriptions.get(effect_type, effect_type)}")

            if not results[effect_type]:
                st.warning(f"No data available for {effect_type}")
                continue

            # Get all years
            all_years = sorted(results[effect_type].keys())

            # Create code_h impact matrix
            st.markdown("#### 📊 Impact by Code_H Category and Year")

            # Collect all unique code_h categories
            all_code_h = {}
            for year in all_years:
                if 'code_h_impacts' in results[effect_type][year]:
                    for impact in results[effect_type][year]['code_h_impacts']:
                        code_h = impact['code_h']
                        if code_h not in all_code_h:
                            all_code_h[code_h] = impact['product_h']

            if all_code_h:
                # Create matrix
                matrix_data = []
                for code_h, product_h in sorted(all_code_h.items()):
                    row = {
                        'Code_H': code_h,
                        'Category_H': product_h
                    }

                    # Add impact values for each year
                    for year in all_years:
                        impact_value = 0
                        if 'code_h_impacts' in results[effect_type][year]:
                            for impact in results[effect_type][year]['code_h_impacts']:
                                if impact['code_h'] == code_h:
                                    impact_value = impact['total_impact']
                                    break
                        row[str(year)] = impact_value

                    matrix_data.append(row)

                if matrix_data:
                    matrix_df = pd.DataFrame(matrix_data)

                    # Calculate total impact across years for sorting
                    year_cols = [str(year) for year in all_years]
                    matrix_df['total_across_years'] = matrix_df[year_cols].sum(axis=1)
                    matrix_df = matrix_df.sort_values('total_across_years', ascending=False)

                    # Format for display
                    display_df = matrix_df.drop(columns=['total_across_years']).copy()
                    for year_col in year_cols:
                        if year_col in display_df.columns:
                            display_df[year_col] = display_df[year_col].apply(lambda x: f"{x:,.2f}" if x != 0 else "0.00")

                    st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)

                    # Download button
                    try:
                        from io import BytesIO

                        buffer = BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            export_df = matrix_df.drop(columns=['total_across_years'])
                            export_df.to_excel(writer, sheet_name=effect_type[:30], index=False)

                        buffer.seek(0)

                        st.download_button(
                            label=f"📥 Download {effect_type} by Code_H (Excel)",
                            data=buffer,
                            file_name=f"total_{effect_type}_by_code_h.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"download_total_{effect_type}"
                        )
                    except ImportError:
                        # Fallback to CSV
                        csv_data = matrix_df.drop(columns=['total_across_years']).to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label=f"📥 Download {effect_type} by Code_H (CSV)",
                            data=csv_data,
                            file_name=f"total_{effect_type}_by_code_h.csv",
                            mime="text/csv",
                            key=f"download_total_{effect_type}"
                        )
            else:
                st.info("No code_h category data available")

def show_scenario_comparison():
    """Display comparison between different scenario sheets."""
    st.subheader("🔀 Scenario Sheet Comparison")

    # Check if scenario analysis has been run
    if not st.session_state.get('scenario_results') or not st.session_state.get('scenario_analyzer'):
        st.warning("⚠️ No scenario analysis results available. Please run scenario analysis first.")
        st.info("👈 Go to the 'Run Analysis' tab to generate data.")
        return

    scenario_analyzer = st.session_state.scenario_analyzer

    # Get scenario sheet names
    if not hasattr(scenario_analyzer, 'scenario_sheet_names'):
        st.error("Scenario sheet information not available.")
        return

    scenario_sheets = scenario_analyzer.scenario_sheet_names
    st.info(f"**Available scenario sheets:** {', '.join(scenario_sheets)}")

    # Select scenarios to compare
    selected_scenarios = st.multiselect(
        "Select scenario sheets to compare:",
        options=scenario_sheets,
        default=scenario_sheets,  # Select all by default
        key="scenario_comparison_selection"
    )

    if len(selected_scenarios) < 1:
        st.warning("Please select at least one scenario sheet to display.")
        return

    st.markdown("---")

    # Select effect type for comparison
    effect_options = {
        'indirect_prod': '💰 Indirect Production',
        'indirect_import': '🌐 Indirect Import',
        'value_added': '💎 Value Added',
        'jobcoeff': '👥 Job Creation',
        'directemploycoeff': '👔 Direct Employment',
        'productioncoeff': '⚡ Production Coefficient (H2)',
        'valueaddedcoeff': '💎 Value Added Coefficient (H2)'
    }

    selected_effect = st.selectbox(
        "Select effect type to compare:",
        options=list(effect_options.keys()),
        format_func=lambda x: effect_options[x],
        key="scenario_comparison_effect"
    )

    st.markdown("---")
    st.markdown(f"### 📊 Comparison Table: {effect_options[selected_effect]}")

    # Get all years
    all_years_set = set()
    for effect_type in scenario_analyzer.aggregated_results.keys():
        if scenario_analyzer.aggregated_results[effect_type]:
            all_years_set.update(scenario_analyzer.aggregated_results[effect_type].keys())
    all_years = sorted(all_years_set)

    # Build comparison table
    comparison_data = []
    for year in all_years:
        row = {'Year': year}

        for sheet_name in selected_scenarios:
            # Filter results for this scenario sheet
            sheet_results = filter_results_by_scenario_sheet(scenario_analyzer, sheet_name)

            if selected_effect in sheet_results and year in sheet_results[selected_effect]:
                total_impact = sheet_results[selected_effect][year]['total_aggregate_impact']
                row[sheet_name] = total_impact
            else:
                row[sheet_name] = 0

        comparison_data.append(row)

    if comparison_data:
        comparison_df = pd.DataFrame(comparison_data)

        # Format for display
        display_df = comparison_df.copy()
        for col in display_df.columns:
            if col != 'Year':
                display_df[col] = display_df[col].apply(lambda x: f"{x:,.2f}" if x != 0 else "0.00")

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Download button
        try:
            from io import BytesIO

            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                comparison_df.to_excel(writer, sheet_name='Scenario Comparison', index=False)

            buffer.seek(0)

            st.download_button(
                label=f"📥 Download Scenario Comparison (Excel)",
                data=buffer,
                file_name=f"scenario_comparison_{selected_effect}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"download_scenario_comparison"
            )
        except ImportError:
            # Fallback to CSV
            csv_data = comparison_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label=f"📥 Download Scenario Comparison (CSV)",
                data=csv_data,
                file_name=f"scenario_comparison_{selected_effect}.csv",
                mime="text/csv",
                key=f"download_scenario_comparison"
            )

        # Visualization: Line chart comparing scenarios over years
        st.markdown("---")
        st.markdown("### 📈 Trend Comparison")

        fig = go.Figure()

        for sheet_name in selected_scenarios:
            y_values = [comparison_df[comparison_df['Year'] == year][sheet_name].values[0]
                       if len(comparison_df[comparison_df['Year'] == year]) > 0 else 0
                       for year in all_years]

            fig.add_trace(go.Scatter(
                x=all_years,
                y=y_values,
                mode='lines+markers',
                name=sheet_name,
                line=dict(width=2),
                marker=dict(size=8)
            ))

        fig.update_layout(
            title=f"{effect_options[selected_effect]} - Scenario Comparison",
            xaxis_title="Year",
            yaxis_title="Impact Value",
            hovermode='x unified',
            height=500,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )

        st.plotly_chart(fig, use_container_width=True)


def show_individual_tables():
    """Display individual sector tables for 1610, 4506, H2S, H2T."""
    st.subheader("👤 Individual Sector Analysis")

    # Check if scenario analysis has been run
    if not st.session_state.get('scenario_results') or not st.session_state.get('scenario_analyzer'):
        st.warning("⚠️ No scenario analysis results available. Please run scenario analysis first.")
        st.info("👈 Go to the 'Run Analysis' tab to generate data.")
        return

    scenario_analyzer = st.session_state.scenario_analyzer

    # Define sectors to analyze
    sectors = {
        '1610': '🏭 Sector 1610 (Coal)',
        '4506': '♻️ Sector 4506 (Renewable Energy)',
        'H2S': '⚡ H2S (Hydrogen Storage)',
        'H2T': '🚛 H2T (Hydrogen Transportation)'
    }

    # Create tabs for each sector
    sector_tabs = st.tabs([sectors[s] for s in sectors.keys()])

    for i, (sector_code, sector_name) in enumerate(sectors.items()):
        with sector_tabs[i]:
            st.markdown(f"### {sector_name}")

            # Filter results for this sector only
            sector_results = filter_results_by_sectors(scenario_analyzer, [sector_code])

            # Get available effect types for this sector
            available_effects = [effect for effect in sector_results.keys() if sector_results[effect]]

            if not available_effects:
                st.warning(f"No analysis results available for sector {sector_code}.")
                continue

            # Build summary table
            summary_years = target_years

            # Define effect columns based on sector type
            if sector_code in ['H2S', 'H2T']:
                effect_columns = {
                    'productioncoeff': 'Indirect Production (Million KRW)',
                    'valueaddedcoeff': 'Value Added (Million KRW)',
                    'jobcoeff': 'Job Creation (Million KRW)',
                    'directemploycoeff': 'Direct Employment (Persons)'
                }
            else:  # 1610, 4506
                effect_columns = {
                    'indirect_prod': 'Indirect Production (Million KRW)',
                    'indirect_import': 'Indirect Import (Million KRW)',
                    'value_added': 'Value Added (Million KRW)',
                    'jobcoeff': 'Job Creation (Persons)',
                    'directemploycoeff': 'Direct Employment (Persons)'
                }

            # Build summary table
            summary_data = []
            for year in summary_years:
                row = {'Year': year}

                for effect_type, column_name in effect_columns.items():
                    if effect_type in available_effects and year in sector_results[effect_type]:
                        total_impact = sector_results[effect_type][year]['total_aggregate_impact']
                        row[column_name] = total_impact
                    else:
                        row[column_name] = 0

                summary_data.append(row)

            if summary_data:
                summary_df = pd.DataFrame(summary_data)

                # Remove columns where all values are 0
                cols_to_keep = ['Year']
                for col in summary_df.columns:
                    if col != 'Year':
                        if summary_df[col].sum() != 0:
                            cols_to_keep.append(col)
                summary_df = summary_df[cols_to_keep]

                # Format for display
                display_df = summary_df.copy()
                for col in display_df.columns:
                    if col != 'Year':
                        display_df[col] = display_df[col].apply(lambda x: f"{x:,.2f}" if x != 0 else "0.00")

                st.dataframe(display_df, use_container_width=True, hide_index=True)

            st.markdown("---")

            # FULL YEARS TABLE
            st.markdown("### 📊 Full Years Table")
            st.markdown("Impact data across all available years")

            # Get all years for this sector
            all_years_set = set()
            for effect_type in available_effects:
                if sector_results[effect_type]:
                    all_years_set.update(sector_results[effect_type].keys())
            all_years = sorted(all_years_set)

            # Build full years table
            full_data = []
            for year in all_years:
                row = {'Year': year}

                for effect_type, column_name in effect_columns.items():
                    if effect_type in available_effects and year in sector_results[effect_type]:
                        total_impact = sector_results[effect_type][year]['total_aggregate_impact']
                        row[column_name] = total_impact
                    else:
                        row[column_name] = 0

                full_data.append(row)

            if full_data:
                full_df = pd.DataFrame(full_data)

                # Remove columns where all values are 0
                cols_to_keep = ['Year']
                for col in full_df.columns:
                    if col != 'Year':
                        if full_df[col].sum() != 0:
                            cols_to_keep.append(col)
                full_df = full_df[cols_to_keep]

                # Format for display
                display_full_df = full_df.copy()
                for col in display_full_df.columns:
                    if col != 'Year':
                        display_full_df[col] = display_full_df[col].apply(lambda x: f"{x:,.2f}" if x != 0 else "0.00")

                st.dataframe(display_full_df, use_container_width=True, hide_index=True)

                # Download button
                try:
                    from io import BytesIO

                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        full_df.to_excel(writer, sheet_name=f'Sector {sector_code}', index=False)

                    buffer.seek(0)

                    st.download_button(
                        label=f"📥 Download {sector_code} Full Data (Excel)",
                        data=buffer,
                        file_name=f"sector_{sector_code}_full_analysis.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"download_sector_full_{sector_code}"
                    )
                except ImportError:
                    # Fallback to CSV
                    csv_data = full_df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label=f"📥 Download {sector_code} Full Data (CSV)",
                        data=csv_data,
                        file_name=f"sector_{sector_code}_full_analysis.csv",
                        mime="text/csv",
                        key=f"download_sector_full_{sector_code}"
                    )

def show_summary_visualizations():
    """Display summary visualizations and charts."""
    st.title("📊 Visualizations")

    # Check if scenario analysis has been run
    if not st.session_state.get('scenario_results') or not st.session_state.get('scenario_analyzer'):
        st.warning("⚠️ No scenario analysis results available. Please run scenario analysis first.")
        st.info("👈 Go to the 'Run Analysis' tab to generate data.")
        return

    scenario_analyzer = st.session_state.scenario_analyzer

    # Import visualization module
    try:
        from libs.visualisation import Visualization
        viz = Visualization(scenario_analyzer)
    except Exception as e:
        st.error(f"Error loading visualization module: {e}")
        return

    # Create tabs for different visualization types
    viz_tabs = st.tabs(["📈 Yearly Trends", "🗺️ Sector Maps", "🔥 Code_H Heatmap", "📊 Grid Comparison"])

    # TAB 1: Yearly Trends
    with viz_tabs[0]:
        st.markdown("### 📈 Yearly Trends")
        st.markdown("Visualize how impacts change over time for different sectors and effect types")

        # Sub-tabs for IO and Hydrogen
        trend_sub_tabs = st.tabs(["IO Table Trends", "Hydrogen Trends"])

        # IO Table Trends
        with trend_sub_tabs[0]:
            st.markdown("#### IO Table Yearly Trends (1610 + 4506)")

            io_effect = st.selectbox(
                "Select Effect Type",
                options=['indirect_prod', 'indirect_import', 'value_added', 'jobcoeff', 'directemploycoeff'],
                format_func=lambda x: {
                    'indirect_prod': '💰 Indirect Production',
                    'indirect_import': '🌐 Indirect Import',
                    'value_added': '💎 Value Added',
                    'jobcoeff': '👥 Job Creation',
                    'directemploycoeff': '👔 Direct Employment'
                }[x],
                key="io_trend_effect"
            )

            scenarios_io = st.multiselect(
                "Select Scenarios",
                options=['1610', '4506', '1610&4506'],
                default=['1610', '4506', '1610&4506'],
                key="io_trend_scenarios"
            )

            if st.button("Generate IO Trends", key="btn_io_trends"):
                try:
                    fig = viz.create_io_yearly_trends(io_effect, scenarios=scenarios_io, show_fig=False)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error generating IO trends: {e}")

        # Hydrogen Trends
        with trend_sub_tabs[1]:
            st.markdown("#### Hydrogen Yearly Trends (H2S + H2T)")

            h2_effect = st.selectbox(
                "Select Effect Type",
                options=['productioncoeff', 'valueaddedcoeff', 'jobcoeff', 'directemploycoeff'],
                format_func=lambda x: {
                    'productioncoeff': '⚡ Indirect Production (H2)',
                    'valueaddedcoeff': '💎 Value Added (H2)',
                    'jobcoeff': '👥 Job Creation',
                    'directemploycoeff': '👔 Direct Employment'
                }[x],
                key="h2_trend_effect"
            )

            scenarios_h2 = st.multiselect(
                "Select Scenarios",
                options=['H2S', 'H2T', 'H2S&H2T'],
                default=['H2S', 'H2T', 'H2S&H2T'],
                key="h2_trend_scenarios"
            )

            if st.button("Generate H2 Trends", key="btn_h2_trends"):
                try:
                    fig = viz.create_hydrogen_yearly_trends(h2_effect, scenarios=scenarios_h2, show_fig=False)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error generating H2 trends: {e}")

    # TAB 2: Sector Maps
    with viz_tabs[1]:
        st.markdown("### 🗺️ Top Sectors Analysis")
        st.markdown("Visualize which sectors have the highest impacts for a given year and effect type")

        col1, col2 = st.columns(2)

        with col1:
            sector_scenario = st.selectbox(
                "Select Scenario",
                options=['1610', '4506', '1610&4506', 'H2S', 'H2T', 'H2S&H2T'],
                format_func=lambda x: {
                    '1610': '🏭 Sector 1610 (Coal)',
                    '4506': '♻️ Sector 4506 (Renewable)',
                    '1610&4506': '🔗 1610 & 4506 (Combined)',
                    'H2S': '⚡ H2S (Hydrogen Storage)',
                    'H2T': '🚛 H2T (Hydrogen Transport)',
                    'H2S&H2T': '⚡ H2S & H2T (Combined)'
                }[x],
                key="sector_scenario"
            )

        with col2:
            sector_year = st.selectbox(
                "Select Year",
                options=[2026, 2030, 2040, 2050],
                index=3,  # Default to 2050
                key="sector_year"
            )

        # Effect type selection based on scenario
        if sector_scenario in ['H2S', 'H2T', 'H2S&H2T']:
            effect_options = ['productioncoeff', 'valueaddedcoeff', 'jobcoeff', 'directemploycoeff']
            effect_labels = {
                'productioncoeff': '⚡ Indirect Production (H2)',
                'valueaddedcoeff': '💎 Value Added (H2)',
                'jobcoeff': '👥 Job Creation',
                'directemploycoeff': '👔 Direct Employment'
            }
        else:
            effect_options = ['indirect_prod', 'indirect_import', 'value_added', 'jobcoeff', 'directemploycoeff']
            effect_labels = {
                'indirect_prod': '💰 Indirect Production',
                'indirect_import': '🌐 Indirect Import',
                'value_added': '💎 Value Added',
                'jobcoeff': '👥 Job Creation',
                'directemploycoeff': '👔 Direct Employment'
            }

        sector_effect = st.selectbox(
            "Select Effect Type",
            options=effect_options,
            format_func=lambda x: effect_labels[x],
            key="sector_effect"
        )

        if st.button("Generate Top 10 Sectors", key="btn_top10"):
            try:
                fig = viz.plot_top_10_sectors(sector_scenario, sector_effect, sector_year, show_fig=False)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No data available for the selected combination.")
            except Exception as e:
                st.error(f"Error generating sector map: {e}")

    # TAB 3: Code_H Heatmap
    with viz_tabs[2]:
        st.markdown("### 🔥 Code_H Sector Heatmap")
        st.markdown("Interactive heatmap showing top sectors by Product_H category, ranked by impact magnitude")
        
        st.info("💡 **How to use**: Select an effect type and year, then click 'Generate Heatmap' to create an interactive visualization showing the top sectors for each product category.")
        
        # Configuration options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            heatmap_effect = st.selectbox(
                "Effect Type",
                options=['indirect_prod', 'indirect_import', 'value_added', 'jobcoeff', 'directemploycoeff',
                        'productioncoeff', 'valueaddedcoeff'],
                format_func=lambda x: {
                    'indirect_prod': '💰 Indirect Production',
                    'indirect_import': '🌐 Indirect Import',
                    'value_added': '💎 Value Added',
                    'jobcoeff': '👥 Job Creation',
                    'directemploycoeff': '👔 Direct Employment',
                    'productioncoeff': '⚡ Production Coeff (H2)',
                    'valueaddedcoeff': '💎 Value Added Coeff (H2)'
                }[x],
                key="heatmap_effect"
            )
        
        with col2:
            heatmap_year = st.selectbox(
                "Year",
                options=[2026, 2030, 2040, 2050],
                index=1,  # Default to 2030
                key="heatmap_year"
            )
        
        with col3:
            heatmap_top_n = st.slider(
                "Top N Sectors per Category",
                min_value=5,
                max_value=20,
                value=10,
                step=5,
                key="heatmap_top_n"
            )
        
        # Generate button
        if st.button("🎨 Generate Heatmap", type="primary", key="btn_heatmap"):
            with st.spinner("Creating interactive heatmap... This may take a moment."):
                try:
                    # Check if data exists for this effect type and year
                    if heatmap_effect not in scenario_analyzer.aggregated_results:
                        st.error(f"No data available for effect type: {heatmap_effect}")
                        st.info("Please run scenario analysis first to generate data.")
                    elif heatmap_year not in scenario_analyzer.aggregated_results[heatmap_effect]:
                        st.error(f"No data available for year: {heatmap_year}")
                        available_years = sorted(scenario_analyzer.aggregated_results[heatmap_effect].keys())
                        st.info(f"Available years: {', '.join(map(str, available_years))}")
                    else:
                        # Get scenario information for this effect type
                        year_data = scenario_analyzer.aggregated_results[heatmap_effect][heatmap_year]
                        scenario_count = year_data['scenario_count']
                        
                        # Get actual scenarios from the analyzer's scenario data
                        scenarios_list = []
                        for idx, row in scenario_analyzer.scenarios_data.iterrows():
                            sector = str(row['sector'])
                            input_table = str(row['input'])
                            scenarios_list.append(f"{sector} ({input_table})")
                        
                        # Determine which scenarios are included based on effect type
                        if heatmap_effect in ['indirect_prod', 'indirect_import', 'value_added']:
                            scenario_info = "📊 **IO Table Scenarios**: 1610 + 4506"
                            scenario_detail = "Combined IO table results from coal and renewable sectors"
                        elif heatmap_effect in ['productioncoeff', 'valueaddedcoeff']:
                            scenario_info = "⚡ **Hydrogen Table Scenarios**: H2S + H2T"
                            scenario_detail = "Combined hydrogen table results from storage and transport scenarios"
                        elif heatmap_effect in ['jobcoeff', 'directemploycoeff']:
                            scenario_info = f"👥 **Employment Scenarios**: All sectors ({scenario_count} scenarios)"
                            scenario_detail = "Includes both IO (1610, 4506) and Hydrogen (H2S, H2T) employment effects"
                        else:
                            scenario_info = f"📊 **Scenarios**: {scenario_count} scenarios included"
                            scenario_detail = "Mixed scenarios"
                        
                        # Show scenario information before heatmap
                        st.info(f"{scenario_info} | 📅 Year: {heatmap_year} | 🎯 Top {heatmap_top_n} per category")
                        st.caption(scenario_detail)
                        
                        # Generate the heatmap
                        fig = viz.create_code_h_heatmap(
                            effect_type=heatmap_effect,
                            year=heatmap_year,
                            top_n=heatmap_top_n,
                            use_plotly=True,
                            show_fig=False
                        )
                        
                        # Display the interactive Plotly chart
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.success(f"✅ Heatmap generated successfully for {heatmap_year}!")
                        
                        # Add explanation
                        with st.expander("ℹ️ How to read this heatmap"):
                            st.markdown("""
                            **Understanding the Code_H Heatmap:**
                            
                            - **X-axis (Columns)**: Product categories (Product_H names)
                            - **Y-axis (Rows)**: Ranking (#1 = highest impact, #10 = 10th highest)
                            - **Colors**: 
                                - 🔴 **Red** = Positive impact
                                - 🔵 **Blue** = Negative impact
                                - ⚪ **White** = Near zero impact
                            - **Cell Text**: Sector names (split into multiple lines for readability)
                            - **Ranking**: Based on **absolute values** (magnitude of impact)
                            
                            **Interactive Features:**
                            - 🖱️ **Hover**: See full sector name and exact impact value
                            - 🔍 **Zoom**: Click and drag to zoom into specific areas
                            - 📐 **Pan**: Drag to move around the heatmap
                            - 🔄 **Reset**: Double-click to reset the view
                            - 💾 **Download**: Use the camera icon to save as PNG
                            """)
                        
                        # Download option for HTML
                        st.markdown("---")
                        st.markdown("**📥 Save Interactive Heatmap**")
                        st.info("The heatmap has been saved as an HTML file. You can download it from the 'libs/output/plotly_charts/' directory or use the camera icon in the chart to save as PNG.")
                        
                except Exception as e:
                    st.error(f"❌ Error generating heatmap: {e}")
                    st.exception(e)
        
        # Show sample if not generated yet
        else:
            st.markdown("---")
            st.markdown("**📊 Sample Output Preview**")
            st.image("https://via.placeholder.com/1200x600/f0f0f0/666666?text=Click+Generate+Heatmap+to+create+interactive+visualization",
                    caption="Interactive heatmap will appear here after clicking 'Generate Heatmap'")

    # TAB 4: Grid Comparison
    with viz_tabs[3]:
        st.markdown("### 📊 Multi-Scenario Grid Comparison")
        st.markdown("View multiple effect types and scenarios in a grid layout")

        # Check if scenario analyzer is available
        if not hasattr(scenario_analyzer, 'scenario_sheet_names'):
            st.error("Scenario sheet information not available.")
        else:
            scenario_sheets = scenario_analyzer.scenario_sheet_names

            # Select scenarios to compare
            selected_scenarios_grid = st.multiselect(
                "Select scenario sheets to display:",
                options=scenario_sheets,
                default=scenario_sheets[:min(4, len(scenario_sheets))],  # Default to first 4
                key="grid_scenario_selection"
            )

            if len(selected_scenarios_grid) < 1:
                st.warning("Please select at least one scenario sheet.")
            else:
                # Select effect types to display
                effect_options_grid = {
                    'indirect_prod': '💰 Indirect Production',
                    'indirect_import': '🌐 Indirect Import',
                    'value_added': '💎 Value Added',
                    'jobcoeff': '👥 Job Creation'
                }

                selected_effects_grid = st.multiselect(
                    "Select effect types to display:",
                    options=list(effect_options_grid.keys()),
                    default=['indirect_prod', 'value_added'],
                    format_func=lambda x: effect_options_grid[x],
                    key="grid_effect_selection"
                )

                if len(selected_effects_grid) < 1:
                    st.warning("Please select at least one effect type.")
                else:
                    # Generate grid button
                    if st.button("🎨 Generate Grid Comparison", type="primary", key="btn_grid_comparison"):
                        with st.spinner("Creating grid comparison charts..."):
                            # Get all years
                            all_years_set = set()
                            for effect_type in scenario_analyzer.aggregated_results.keys():
                                if scenario_analyzer.aggregated_results[effect_type]:
                                    all_years_set.update(scenario_analyzer.aggregated_results[effect_type].keys())
                            all_years = sorted(all_years_set)

                            # Create subplot grid
                            n_effects = len(selected_effects_grid)
                            n_scenarios = len(selected_scenarios_grid)

                            # Determine grid layout (try to keep it balanced)
                            if n_effects * n_scenarios <= 4:
                                rows, cols = 2, 2
                            elif n_effects * n_scenarios <= 6:
                                rows, cols = 2, 3
                            elif n_effects * n_scenarios <= 8:
                                rows, cols = 2, 4
                            else:
                                rows, cols = 4, 4

                            # Create subplots
                            from plotly.subplots import make_subplots

                            subplot_titles = []
                            for effect in selected_effects_grid:
                                for scenario in selected_scenarios_grid:
                                    subplot_titles.append(f"{effect_options_grid[effect]}<br>{scenario}")

                            fig = make_subplots(
                                rows=rows,
                                cols=cols,
                                subplot_titles=subplot_titles[:rows*cols],
                                vertical_spacing=0.12,
                                horizontal_spacing=0.08
                            )

                            # Fill subplots
                            plot_idx = 0
                            for effect_idx, effect in enumerate(selected_effects_grid):
                                for scenario_idx, scenario in enumerate(selected_scenarios_grid):
                                    if plot_idx >= rows * cols:
                                        break

                                    row = (plot_idx // cols) + 1
                                    col = (plot_idx % cols) + 1

                                    # Get data for this scenario and effect
                                    sheet_results = filter_results_by_scenario_sheet(scenario_analyzer, scenario)

                                    y_values = []
                                    for year in all_years:
                                        if effect in sheet_results and year in sheet_results[effect]:
                                            y_values.append(sheet_results[effect][year]['total_aggregate_impact'])
                                        else:
                                            y_values.append(0)

                                    fig.add_trace(
                                        go.Scatter(
                                            x=all_years,
                                            y=y_values,
                                            mode='lines+markers',
                                            name=f"{scenario}",
                                            line=dict(width=2),
                                            marker=dict(size=6),
                                            showlegend=False
                                        ),
                                        row=row,
                                        col=col
                                    )

                                    plot_idx += 1

                            # Update layout
                            fig.update_layout(
                                title_text="Multi-Scenario Grid Comparison",
                                height=300 * rows,
                                showlegend=False
                            )

                            # Update axes
                            for i in range(1, rows * cols + 1):
                                fig.update_xaxes(title_text="Year", row=(i-1)//cols + 1, col=(i-1)%cols + 1)
                                fig.update_yaxes(title_text="Impact", row=(i-1)//cols + 1, col=(i-1)%cols + 1)

                            st.plotly_chart(fig, use_container_width=True)

                            st.success("✅ Grid comparison generated successfully!")

def main():
    # Sidebar - Show scenario file info
    st.sidebar.title("🏭 Input Output Analysis")

    # Display currently loaded scenario file
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📁 Data File")

    data_folder = Path("data")
    data_file = data_folder / "Data_v10.xlsx"

    if 'current_scenario_file' in st.session_state:
        current_file = st.session_state.current_scenario_file
        st.sidebar.success(f"✅ {current_file}")

        # Show loaded scenario sheets
        if 'scenario_analyzer' in st.session_state:
            analyzer = st.session_state.scenario_analyzer
            if hasattr(analyzer, 'scenario_sheet_names'):
                with st.sidebar.expander("📋 Loaded Scenario Sheets"):
                    for sheet_name in analyzer.scenario_sheet_names:
                        st.text(f"• {sheet_name}")
    else:
        st.sidebar.warning("⚠️ No data loaded")
        st.sidebar.info("Go to '🚀 Run Analysis' tab to load Data_v10.xlsx")

    # Show data file status
    if data_file.exists():
        st.sidebar.markdown(f"**Data file:** `Data_v10.xlsx` ✅")
    else:
        st.sidebar.error("❌ Data_v10.xlsx not found")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📍 Main Menu")
    main_option = st.sidebar.radio(
        "      ",
        ["Scenarios", "Analysis", "Visualisation"],
        index=0
    )

    # Show the respective content area depending on high-level selection
    if main_option == "Scenarios":
        # Scenario analysis/batch analysis area: now loads scenario_x_xxxx excel files from data folder!
        show_scenarios()
    elif main_option == "Analysis":
        # Show tabs for different table types
        st.title("📊 Analysis results")

        # Create tabs for different table views
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🚀 Run Analysis", "🔀 Scenario Comparison", "🔗 Integrated", "⚡ H2", "📊 Total", "👤 Individual"])

        with tab1:
            run_scenario_analysis()

        with tab2:
            show_scenario_comparison()

        with tab3:
            show_integrated_tables()

        with tab4:
            show_hydrogen_analysis()

        with tab5:
            show_total_tables()

        with tab6:
            show_individual_tables()
    else:  # Visualisation
        show_summary_visualizations()


if __name__ == "__main__":
    main()