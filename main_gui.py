from re import U
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from libs.io_analyzer import IOTableAnalyzer
from hydrogen_gui import show_hydrogen_analysis
from scenario_analyzer import ScenarioAnalyzer

# Configure Streamlit page
st.set_page_config(
    page_title="Steel-Coal & Hydrogen I-O Table Analyzer",
    page_icon="🏭",
    layout="wide"
)

@st.cache_data
def load_analyzer():
    """Load the analyzer with caching to avoid reloading data."""
    return IOTableAnalyzer()

def main():
    # Sidebar navigation
    st.sidebar.title("Analysis Selection")
    analysis_type = st.sidebar.radio(
        "Choose Analysis Type:",
        ["I-O Table Analysis", "Hydrogen Table Analysis", "Scenario Batch Analysis", "📊 Summary Visualizations"],
        index=0
    )

    if analysis_type == "I-O Table Analysis":
        show_io_analysis()
    elif analysis_type == "Hydrogen Table Analysis":
        show_hydrogen_analysis()
    elif analysis_type == "Scenario Batch Analysis":
        show_scenario_analysis()
    else:  # Summary Visualizations
        show_summary_visualizations()

def show_io_analysis():
    st.title("🏭 Steel-Coal I-O Table Direct Effects Analyzer")
    st.markdown("---")
    
    # Load analyzer
    with st.spinner("Loading I-O Table data..."):
        analyzer = load_analyzer()

    # Sidebar for inputs
    st.sidebar.header("I-O Analysis Parameters")
    
    # Get sector options (already formatted for display)
    sector_options = analyzer.get_sector_options()
    sector_list = list(sector_options.values())  # These are already formatted as "code: name"
    
    # Input controls
    selected_sector_display = st.sidebar.selectbox(
        "Select Sector",
        options=sector_list,
        index=0,
        help="Choose the target sector for analysis"
    )
    
    # Extract formatted sector code using analyzer method
    selected_sector = analyzer.get_sector_from_display(selected_sector_display)
    
    demand_change = st.sidebar.number_input(
        "Demand Change (million won)",
        value=1000000,
        step=100000,
        format="%d",
        help="Enter the change in final demand (positive or negative)"
    )
    
    # Analysis button - will calculate all coefficient types
    analyze_button = st.sidebar.button("🔍 Analyze All Effects", type="primary")
    
    # Main content area with tabs
    if analyze_button or st.session_state.get('auto_analyze', False):
        
        # Calculate all coefficient types including job coefficients
        all_results = {}
        coefficient_types = ["indirect_prod", "indirect_import", "value_added", "jobcoeff", "directemploycoeff"]
        coeff_names = {
            #"A": "Direct Total",
            #"Am": "Direct Import", 
            #"Ad": "Direct Domestic",
            "indirect_prod": "Production-inducing",
            "indirect_import": "Import-inducing",
            "value_added": "Value-Added",
            "jobcoeff": "Total Job Creation",
            "directemploycoeff": "Direct Employment"
        }
        
        with st.spinner("Calculating all coefficient effects..."):
            for coeff_type in coefficient_types:
                try:
                    results = analyzer.calculate_direct_effects(
                        selected_sector, 
                        demand_change, 
                        coeff_type,
                        quiet=True  # Suppress output for GUI
                    )
                    all_results[coeff_type] = results
                except Exception as e:
                    st.error(f"Error calculating {coeff_type}: {str(e)}")
                    all_results[coeff_type] = None
        
        # Display summary
        st.subheader("📊 Analysis Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        if all_results["indirect_prod"]:
            with col1:
                st.metric("Target Sector", f"{selected_sector}")
            with col2:
                st.metric("Product", all_results["indirect_prod"]["target_product"])
            with col3:
                st.metric("Demand Change", f"{demand_change:,.0f}")
            with col4:
                st.metric("Analysis Types", len([r for r in all_results.values() if r is not None]))
        
        # Create tabs: Summary first, then each coefficient type
        tab_names = ["📊 Total"] + [f"{coeff_names[ct]}" for ct in coefficient_types]
        tabs = st.tabs(tab_names)
        
        # Summary tab (first tab)
        with tabs[0]:
            st.subheader("📊 Summary")
            
            # Overall comparison table - separate economic and job effects
            economic_summary = []
            job_summary = []
            
            # Separate data by effect type
            economic_coeffs = ["indirect_prod", "indirect_import", "value_added"]
            job_coeffs = ["jobcoeff", "directemploycoeff"]
            
            for coeff_type in economic_coeffs:
                if all_results[coeff_type]:
                    results = all_results[coeff_type]
                    economic_summary.append({
                        'Coefficient Type': f"{coeff_names[coeff_type]} ({coeff_type})",
                        #'Total Impact (million won)': f"{results['impact'] == 'indirect_prod':,.0f}",
                        'Affected Sectors': results['num_affected_sectors'],
                        'Top Impact Sector': results['impacts'][0]['sector_name'] if results['impacts'] else 'None',
                        'Top Impact Value': f"{results['impacts'][0]['impact']:,.0f}" if results['impacts'] else '0'
                    })
            
            for coeff_type in job_coeffs:
                if all_results[coeff_type]:
                    results = all_results[coeff_type]
                    job_summary.append({
                        'Coefficient Type': f"{coeff_names[coeff_type]} ({coeff_type})",
                        'Total Jobs (person/billion won)': f"{results['total_impact']:,.0f}",
                        'Affected Sub-sectors': results['num_affected_sectors'],
                        'Top Impact Sub-sector': results['impacts'][0]['sector_name'] if results['impacts'] else 'None',
                        'Top Impact Value': f"{results['impacts'][0]['impact']:,.0f}" if results['impacts'] else '0'
                    })
            
            # Display tables
            if economic_summary and job_summary:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**💰 Economic Effects Summary**")
                    economic_df = pd.DataFrame(economic_summary)
                    st.dataframe(economic_df, use_container_width=True)
                
                with col2:
                    st.markdown("**👥 Employment Effects Summary**")
                    job_df = pd.DataFrame(job_summary)
                    st.dataframe(job_df, use_container_width=True)
            
            elif economic_summary:
                st.markdown("**💰 Economic Effects Summary**")
                economic_df = pd.DataFrame(economic_summary)
                st.dataframe(economic_df, use_container_width=True)
                
            elif job_summary:
                st.markdown("**👥 Employment Effects Summary**")
                job_df = pd.DataFrame(job_summary)
                st.dataframe(job_df, use_container_width=True)
            
            # Combined summary for download (maintain backward compatibility)
            all_summary_data = economic_summary + job_summary
            if all_summary_data:
                summary_df = pd.DataFrame(all_summary_data)
                
                # Combined results for download
                st.subheader("📥 Download Complete Analysis")
                
                # Create Excel file with multiple sheets
                try:
                    from io import BytesIO
                    
                    # Create Excel writer object
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        
                        # Summary sheet
                        summary_df.to_excel(writer, sheet_name='Summary', index=False)
                        
                        # Individual coefficient sheets
                        for coeff_type in coefficient_types:
                            if all_results[coeff_type] and all_results[coeff_type]['impacts']:
                                results = all_results[coeff_type]
                                df = pd.DataFrame(results['impacts'])

                                # Add code_h and product_h columns for all coefficient types
                                # Map sector codes to code_h and product_h
                                if hasattr(analyzer, 'basic_to_code_h') and hasattr(analyzer, 'code_h_to_product_h'):
                                    df['code_h'] = df['sector_code'].map(analyzer.basic_to_code_h)
                                    df['product_h'] = df['code_h'].map(analyzer.code_h_to_product_h)
                                else:
                                    df['code_h'] = ''
                                    df['product_h'] = ''

                                # Structure columns based on coefficient type
                                if coeff_type not in ['jobcoeff', 'directemploycoeff']:
                                    df = df[['sector_code', 'sector_name', 'code_h', 'product_h', 'impact']]
                                    df.columns = ['Sector Code', 'Sector Name', 'Code_H', 'Category_H', 'Impact']
                                else:
                                    # For job coefficients, also include code_h and product_h
                                    df = df[['sector_code', 'sector_name', 'code_h', 'product_h', 'impact']]
                                    df.columns = ['Sector Code', 'Sector Name', 'Code_H', 'Category_H', 'Impact']

                                df = df.sort_values('Impact', key=lambda x: abs(x), ascending=False)

                                # Add metadata as first rows (all types now have 5 columns)
                                metadata = pd.DataFrame([
                                    ['Analysis Details', '', '', '', ''],
                                    ['Target Sector', results['target_sector'], '', '', ''],
                                    ['Target Product', results['target_product'], '', '', ''],
                                    ['Demand Change', results['demand_change'], '', '', ''],
                                    ['Coefficient Type', f"{results['coeff_name']} ({coeff_type})", '', '', ''],
                                    ['Total Impact', results['total_impact'], '', '', ''],
                                    ['', '', '', '', ''],
                                    ['Sector Code', 'Sector Name', 'Code_H', 'Category_H', 'Impact']
                                ], columns=['Sector Code', 'Sector Name', 'Code_H', 'Category_H', 'Impact'])

                                final_df = pd.concat([metadata, df], ignore_index=True)
                                sheet_name = coeff_names[coeff_type][:30]  # Excel sheet name limit
                                final_df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                    
                    buffer.seek(0)
                    
                    st.download_button(
                        label="📊 Download Complete Analysis (Excel)",
                        data=buffer,
                        file_name=f"complete_io_analysis_{selected_sector}_{demand_change}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                except ImportError:
                    st.warning("Excel export requires openpyxl. Install with: pip install openpyxl")
                    st.info("Using CSV export instead.")
                    # Fallback to combined CSV
                    combined_data = []
                    for coeff_type in coefficient_types:
                        if all_results[coeff_type] and all_results[coeff_type]['impacts']:
                            results = all_results[coeff_type]
                            for impact in results['impacts']:
                                # Get code_h and product_h if available
                                sector_code = impact['sector_code']
                                code_h = analyzer.basic_to_code_h.get(sector_code, '') if hasattr(analyzer, 'basic_to_code_h') else ''
                                product_h = analyzer.code_h_to_product_h.get(code_h, '') if code_h and hasattr(analyzer, 'code_h_to_product_h') else ''

                                combined_data.append({
                                    'coefficient_type': coeff_type,
                                    'coefficient_name': coeff_names[coeff_type],
                                    'sector_code': sector_code,
                                    'sector_name': impact['sector_name'],
                                    'code_h': code_h,
                                    'product_h': product_h,
                                    'impact': impact['impact']
                                })

                    if combined_data:
                        combined_df = pd.DataFrame(combined_data)
                        csv_data = combined_df.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="📊 Download Complete Analysis (CSV)",
                            data=csv_data,
                            file_name=f"complete_io_analysis_{selected_sector}_{demand_change}.csv",
                            mime="text/csv"
                        )
                
                # Detailed comparison charts - separate economic and job effects
                st.subheader("📈 Impact Comparison")
                
                # Separate coefficient types by category
                economic_coeffs = ["indirect_prod", "indirect_import", "value_added"]
                job_coeffs = ["jobcoeff", "directemploycoeff"]
                
                # Create economic effects chart data
                economic_chart_data = []
                for coeff_type in economic_coeffs:
                    if all_results[coeff_type]:
                        economic_chart_data.append({
                            'Coefficient Type': coeff_names[coeff_type],
                            'Total Impact': all_results[coeff_type]['total_impact'],
                            'Affected Sectors': all_results[coeff_type]['num_affected_sectors']
                        })
                
                # Create job effects chart data
                job_chart_data = []
                for coeff_type in job_coeffs:
                    if all_results[coeff_type]:
                        job_chart_data.append({
                            'Coefficient Type': coeff_names[coeff_type],
                            'Total Jobs': all_results[coeff_type]['total_impact'],
                            'Affected Sub-sectors': all_results[coeff_type]['num_affected_sectors']
                        })
                
                # Display charts
                if economic_chart_data and job_chart_data:
                    # Two separate sections for economic vs job effects
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**💰 Economic Effects**")
                        economic_df = pd.DataFrame(economic_chart_data)
                        st.caption("Total Economic Impact by Type")
                        st.bar_chart(economic_df.set_index('Coefficient Type')['Total Impact'])
                        
                        st.caption("Economic Sectors Affected")
                        st.bar_chart(economic_df.set_index('Coefficient Type')['Affected Sectors'])
                        
                    
                    with col2:
                        st.markdown("**👥 Employment Effects**")
                        job_df = pd.DataFrame(job_chart_data)
                        st.caption("Total Jobs Created/Affected")
                        st.bar_chart(job_df.set_index('Coefficient Type')['Total Jobs'])
                        
                        st.caption("Employment Sub-sectors Affected")
                        st.bar_chart(job_df.set_index('Coefficient Type')['Affected Sub-sectors'])
                        
                
                elif economic_chart_data:
                    # Only economic data available
                    economic_df = pd.DataFrame(economic_chart_data)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.bar_chart(economic_df.set_index('Coefficient Type')['Total Impact'])
                        st.caption("Total Economic Impact by Type")
                    with col2:
                        st.bar_chart(economic_df.set_index('Coefficient Type')['Affected Sectors'])
                        st.caption("Economic Sectors Affected")
                        
                elif job_chart_data:
                    # Only job data available  
                    job_df = pd.DataFrame(job_chart_data)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.bar_chart(job_df.set_index('Coefficient Type')['Total Jobs (person/billion won)'])
                        st.caption("Total Jobs Created/Affected")
                    with col2:
                        st.bar_chart(job_df.set_index('Coefficient Type')['Affected Sub-sectors'])
                        st.caption("Employment Sub-sectors Affected")
            else:
                st.warning("No results available for summary.")
        
        # Individual coefficient type tabs (starting from index 1)
        for i, coeff_type in enumerate(coefficient_types):
            with tabs[i + 1]:  # +1 because summary tab is at index 0
                results = all_results[coeff_type]
                
                if results is None:
                    st.error(f"Failed to calculate {coeff_names[coeff_type]} effects")
                    continue
                
                # Summary metrics for this coefficient type
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Economic Impact (domestic; million won)", f"{results['impacts']}")
                with col2:
                    st.metric("Affected Sectors", results['num_affected_sectors'])
                with col3:
                    if results['impacts']:
                        max_impact = max([abs(imp['impact']) for imp in results['impacts']])
                        st.metric("Max Impact", f"{max_impact:,.0f}")
                
                # Results table
                if results['impacts']:
                    df = pd.DataFrame(results['impacts'])
                    df['abs_impact'] = df['impact'].abs()
                    df = df.sort_values('abs_impact', ascending=False)
                    
                    # Format the DataFrame for display
                    display_df = df[['sector_code', 'sector_name', 'impact']].copy()
                    display_df.columns = ['Code', 'Sector Name', 'Impact']
                    display_df['Impact'] = display_df['Impact'].apply(lambda x: f"{x:,.2f}")
                    display_df.index = range(1, len(display_df) + 1)

                    # Display table
                    st.dataframe(
                        display_df,
                        width=600,
                        height=600
                    )

                    # Add code_h and product_h columns to the DataFrame before download/export
                    # If these columns don't already exist, map them from the sector_code as needed.
                    if 'code_h' not in df.columns or 'product_h' not in df.columns:
                        # Create mappings via analyzer if needed
                        if hasattr(analyzer, "basic_to_code_h") and hasattr(analyzer, "code_h_to_product_h"):
                            df['code_h'] = df['sector_code'].map(analyzer.basic_to_code_h)
                            df['product_h'] = df['code_h'].map(analyzer.code_h_to_product_h)
                        else:
                            df['code_h'] = ""
                            df['product_h'] = ""
                    # Download button
                    csv_data = df[['sector_code', 'sector_name', 'code_h', 'product_h', 'impact']].to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label=f"📥 Download {coeff_names[coeff_type]} Results",
                        data=csv_data,
                        file_name=f"io_analysis_{selected_sector}_{coeff_type}.csv",
                        mime="text/csv",
                        key=f"download_{coeff_type}"
                    )
                    
                    # Quick statistics
                    st.markdown("### 📈 Statistics")
                    col3, col4, col5, col6 = st.columns(4)
                    
                    impacts_series = df['impact']
                    with col3:
                        st.metric("Max", f"{impacts_series.max():,.0f}")
                    with col4:
                        st.metric("Min", f"{impacts_series.min():,.0f}")
                    with col5:
                        st.metric("Mean", f"{impacts_series.mean():,.0f}")
                    with col6:
                        std_val = impacts_series.std()
                        if pd.notna(std_val):
                            st.metric("Std Dev", f"{std_val:,.0f}")
                        else:
                            st.metric("Std Dev", "N/A")

                else:
                    st.warning(f"No significant impacts found for {coeff_names[coeff_type]} analysis.")

    else:
        st.info("👈 Select a sector, enter demand change, and click 'Analyze All Effects' to see results in tabs below")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
    <p>Steel-Coal I-O Table Analyzer | Built with Streamlit | Data: Korean I-O Table 2020</p>
    </div>
    """, unsafe_allow_html=True)

@st.cache_data
def load_scenario_analyzer():
    """Load the scenario analyzer with caching."""
    return ScenarioAnalyzer()

def show_scenario_analysis():
    st.title("📊 Scenario Batch Analysis")
    st.markdown("---")
    st.markdown("""
    This tool analyzes multiple scenarios from the scenarios.xlsx file, processing all input sectors
    across all years for all available effect types automatically.
    """)

    # Load scenario analyzer
    with st.spinner("Loading scenario data..."):
        try:
            scenario_analyzer = load_scenario_analyzer()
            st.success(f"✅ Loaded {len(scenario_analyzer.scenarios_data)} scenarios")

            # Display scenario overview
            st.subheader("📋 Scenario Overview")
            preview_df = scenario_analyzer.scenarios_data.copy()
            # Fix data types for Arrow compatibility
            preview_df['input'] = preview_df['input'].astype(str)
            preview_df['sector'] = preview_df['sector'].astype(str)

            # Convert all column names to strings for consistency
            preview_df.columns = [str(col) for col in preview_df.columns]

            st.dataframe(preview_df, use_container_width=True)

            # Years covered
            year_columns = [col for col in scenario_analyzer.scenarios_data.columns if isinstance(col, int)]

            st.info(f"**Years covered:** {min(year_columns)} - {max(year_columns)} ({len(year_columns)} years)")
            #st.info(f"**Years covered:** {min_year} - {max_year} ({len(data_cols-2)} years)")

        except Exception as e:
            st.error(f"❌ Error loading scenarios: {str(e)}")
            st.info("Make sure the scenarios.xlsx file is in the data/ directory")
            return

    # Analysis button - runs all effect types automatically
    if st.sidebar.button("🚀 Run Complete Scenario Analysis", type="primary"):
        # Initialize session state for results
        if 'scenario_results' not in st.session_state:
            st.session_state.scenario_results = None
            st.session_state.scenario_analyzer = None

        # Define all effect types to analyze
        all_effect_types = [
            #'inputcoeff_A',        # Input coefficients (hydrogen)
            'productioncoeff',        # Indirect production (hydrogen)
            'valueaddedcoeff',     # Value added (hydrogen)
            #'A',                   # Direct total (IO)
            #'Am',                  # Direct import (IO)
            #'Ad',                  # Direct domestic (IO)
            'indirect_prod',       # Indirect production (IO)
            'indirect_import',     # Indirect import (IO)
            'value_added',         # Value added (IO)
            'jobcoeff',           # Job creation
            'directemploycoeff'    # Direct employment
        ]

        with st.spinner("Running complete scenario analysis... This may take a few minutes."):
            try:
                # Run the analysis for all effect types
                scenario_analyzer.run_all_scenarios(effect_types=all_effect_types)

                # Automatically save individual scenario CSV files to output folder
                scenario_analyzer.save_individual_scenario_csvs(output_dir='output')

                # Store results in session state
                st.session_state.scenario_results = scenario_analyzer.aggregated_results
                st.session_state.scenario_analyzer = scenario_analyzer

                st.success("✅ Complete scenario analysis finished! CSV files saved to output folder.")

            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                return

    # Display results if available
    if st.session_state.get('scenario_results') and st.session_state.get('scenario_analyzer'):
        scenario_analyzer = st.session_state.scenario_analyzer
        results = st.session_state.scenario_results

        st.subheader("📈 Analysis Results")

        # Separate results by table type and input source
        io_effects = [ 'indirect_prod', 'indirect_import', 'value_added']
        hydrogen_effects = ['productioncoeff', 'valueaddedcoeff']
        io_job_effects = ['jobcoeff', 'directemploycoeff']  # Job effects for IO scenarios
        hydrogen_job_effects = ['jobcoeff', 'directemploycoeff']  # Job effects for Hydrogen scenarios

        # Top level tabs: IO Table vs Hydrogen Table
        main_tabs = st.tabs(["🏭 IO Table Results", "⚡ Hydrogen Table Results"])

        # IO Table Results
        with main_tabs[0]:
            st.markdown("### Input-Output Table Analysis Results")

            # Get available IO effects (only from IO table scenarios)
            available_io_effects = [effect for effect in io_effects if effect in results and results[effect]]
            available_io_job_effects = [effect for effect in io_job_effects if effect in results and results[effect]]

            if available_io_effects or available_io_job_effects:
                # Effect type descriptions for IO
                io_effect_descriptions = {
                   # 'A': 'Direct Total Effects',
                   # 'Am': 'Direct Import Effects',
                   # 'Ad': 'Direct Domestic Effects',
                    'indirect_prod': 'Indirect Production Effects',
                    'indirect_import': 'Indirect Import Effects',
                    'value_added': 'Value Added Effects',
                    'jobcoeff': 'Job Creation Effects (IO)',
                    'directemploycoeff': 'Direct Employment Effects (IO)'
                }

                # Create tabs for IO effect types
                io_tab_names = []
                io_tab_effects = []

                for effect in available_io_effects:
                    io_tab_names.append(io_effect_descriptions[effect])
                    io_tab_effects.append(effect)

                for effect in available_io_job_effects:
                    io_tab_names.append(io_effect_descriptions[effect])
                    io_tab_effects.append(effect)

                io_effect_tabs = st.tabs(io_tab_names)

                for i, effect_type in enumerate(io_tab_effects):
                    with io_effect_tabs[i]:
                        _display_effect_results(effect_type, results, scenario_analyzer, io_effect_descriptions, table_type="io")
            else:
                st.warning("No IO table results available")

        # Hydrogen Table Results
        with main_tabs[1]:
            st.markdown("### Hydrogen Table Analysis Results")

            # Get available hydrogen effects (only from hydrogen table scenarios)
            available_hydrogen_effects = [effect for effect in hydrogen_effects if effect in results and results[effect]]
            available_hydrogen_job_effects = [effect for effect in hydrogen_job_effects if effect in results and results[effect]]

            if available_hydrogen_effects or available_hydrogen_job_effects:
                # Effect type descriptions for Hydrogen
                hydrogen_effect_descriptions = {
                    'productioncoeff': 'Production-inducing effect',
                    'valueaddedcoeff': 'Value Added Effect',
                    'jobcoeff': 'Job Creation Effect',
                    'directemploycoeff': 'Direct Employment Effect'
                }

                # Create tabs for Hydrogen effect types
                hydrogen_tab_names = []
                hydrogen_tab_effects = []

                for effect in available_hydrogen_effects:
                    hydrogen_tab_names.append(hydrogen_effect_descriptions[effect])
                    hydrogen_tab_effects.append(effect)

                for effect in available_hydrogen_job_effects:
                    hydrogen_tab_names.append(hydrogen_effect_descriptions[effect])
                    hydrogen_tab_effects.append(effect)

                hydrogen_effect_tabs = st.tabs(hydrogen_tab_names)

                for i, effect_type in enumerate(hydrogen_tab_effects):
                    with hydrogen_effect_tabs[i]:
                        _display_effect_results(effect_type, results, scenario_analyzer, hydrogen_effect_descriptions, table_type="hydrogen")
            else:
                st.warning("No hydrogen table results available")

            # Add a download section for all results
            st.markdown("---")
            st.subheader("💾 Download All Results")

            col1, col2 = st.columns(2)

            with col1:
                # Generate Excel files button
                if st.button("📊 Generate Excel Reports"):
                    with st.spinner("Generating Excel reports and CSV files..."):
                        try:
                            scenario_analyzer.create_summary_tables(output_dir='output')
                            scenario_analyzer.save_individual_scenario_csvs(output_dir='output')
                            st.success("✅ Excel reports and CSV files generated in 'output/' directory!")

                            # List generated files
                            import os
                            if os.path.exists('output'):
                                xlsx_files = [f for f in os.listdir('output') if f.endswith('.xlsx')]
                                csv_files = [f for f in os.listdir('output') if f.startswith('scenario_') and f.endswith('.csv')]
                                if xlsx_files:
                                    st.info(f"Generated Excel files: {len(xlsx_files)} files")
                                if csv_files:
                                    st.info(f"Generated CSV files: {len(csv_files)} files")

                        except Exception as e:
                            st.error(f"❌ Error generating reports: {str(e)}")

            with col2:
                # CSV download for all results
                if st.button("📥 Download Complete CSV"):
                    # Prepare combined data for CSV
                    combined_data = []
                    for effect_type in available_effects:
                        if not results[effect_type]:
                            continue

                        for year, year_data in results[effect_type].items():
                            for sector in year_data['sector_impacts']:
                                combined_data.append({
                                    'effect_type': effect_type,
                                    'effect_description': effect_type_descriptions.get(effect_type, effect_type),
                                    'year': year,
                                    'sector_code': sector['sector_code'],
                                    'sector_name': sector['sector_name'],
                                    'total_domestic_impact': sector['total_domestic_impact'],
                                    'total_import_impact': sector['total_import_impact'],
                                    'avg_impact': sector['avg_impact'],
                                    'scenario_count': sector['scenario_count']
                                })

                    if combined_data:
                        combined_df = pd.DataFrame(combined_data)
                        csv_data = combined_df.to_csv(index=False, encoding='utf-8-sig')

                        st.download_button(
                            label="📊 Download Complete Analysis (CSV)",
                            data=csv_data,
                            file_name="complete_scenario_analysis.csv",
                            mime="text/csv",
                            key="download_complete"
                        )
                else:
                    st.warning("No results available. Please run the analysis first.")

    else:
        st.info("👈 Click 'Run Complete Scenario Analysis' to analyze all scenarios and effect types.")

def _display_effect_results(effect_type, results, scenario_analyzer, effect_descriptions, table_type="io"):
    """Helper function to display results for a specific effect type with input sector separation."""
    effect_data = results[effect_type]

    if not effect_data:
        st.warning(f"No results available for {effect_type}")
        return

    st.markdown(f"### {effect_descriptions.get(effect_type, effect_type)}")

    # Get individual scenario results to separate by input sector
    individual_results = scenario_analyzer.results.get(effect_type, {})

    if not individual_results:
        st.warning("No individual scenario data available")
        return

    # Collect unique input sectors from the scenarios data, filtered by table type
    input_sectors = {}
    for idx, row in scenario_analyzer.scenarios_data.iterrows():
        input_table = row['input']
        sector = str(row['sector'])

        # Filter by table type
        is_hydrogen_table = 'hydrogen' in input_table.lower()
        if (table_type == "hydrogen" and not is_hydrogen_table) or (table_type == "io" and is_hydrogen_table):
            continue

        scenario_key = f"{input_table}_{sector}"
        input_sectors[scenario_key] = {
            'input_table': input_table,
            'sector': sector,
            'display_name': f"{sector} ({input_table})"
        }

    if not input_sectors:
        st.warning(f"No {table_type} input sectors found")
        return

    # Create tabs for each input sector
    sector_names = [info['display_name'] for info in input_sectors.values()]
    sector_tabs = st.tabs(sector_names)

    for i, (sector_key, sector_info) in enumerate(input_sectors.items()):
        with sector_tabs[i]:
            st.markdown(f"#### {sector_info['sector']} from {sector_info['input_table']}")

            # Get years with data for this input sector
            available_years = []

            for year in individual_results.keys():
                for scenario_idx, scenario_data in individual_results[year].items():
                    # Check if this scenario matches our input sector
                    scenario_idx_num = int(scenario_idx.split('_')[1])
                    
                    scenario_row = scenario_analyzer.scenarios_data.iloc[scenario_idx_num]

                    print(scenario_row)

                    if (str(scenario_row['sector']) == sector_info['sector'] and
                        scenario_row['input'] == sector_info['input_table']):
                        available_years.append(year)
                        break

            #print("Before sorting: ")
            #print(available_years)

            available_years = sorted(set(available_years))

            #print("After sorting: ")
            #print(available_years)

            if not available_years:
                st.info(f"No data available for {sector_info['sector']}")
                continue

            # Display summary metrics for this input sector
            latest_year = available_years[-1]
            latest_year_data = None

            # Find the latest year data for this input sector
            for scenario_idx, scenario_data in individual_results[latest_year].items():
                scenario_idx_num = int(scenario_idx.split('_')[1])
                scenario_row = scenario_analyzer.scenarios_data.iloc[scenario_idx_num]

                if (str(scenario_row['sector']) == sector_info['sector'] and
                    scenario_row['input'] == sector_info['input_table']):
                    latest_year_data = scenario_data
                    break

            if latest_year_data:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Years Covered", f"{min(available_years)} - {max(available_years)}")
                with col2:
                    st.metric(f"Total Impact ({latest_year})", f"{latest_year_data['total_impact']:,.0f}")
                with col3:
                    st.metric(f"Affected Sectors ({latest_year})", latest_year_data['num_affected_sectors'])

            # Create matrix with sectors as rows and years as columns for this input sector
            if available_years:
                # Collect all unique output sectors for this input sector across all years
                all_output_sectors = {}
                for year in available_years:
                    for scenario_idx, scenario_data in individual_results[year].items():
                        scenario_idx_num = int(scenario_idx.split('_')[1])
                        scenario_row = scenario_analyzer.scenarios_data.iloc[scenario_idx_num]

                        if (str(scenario_row['sector']) == sector_info['sector'] and
                            scenario_row['input'] == sector_info['input_table']):

                            for impact in scenario_data['result']['impacts']:
                                sector_code = str(impact['sector_code'])
                                sector_name = impact['sector_name']
                                if sector_code not in all_output_sectors:
                                    all_output_sectors[sector_code] = sector_name

                # Create the matrix for this input sector
                if all_output_sectors:
                    matrix_data = []
                    for sector_code, sector_name in all_output_sectors.items():
                        row = {
                            'Sector Code': sector_code,
                            'Sector Name': sector_name
                        }

                        # Add data for each year
                        for year in available_years:
                            impact_value = 0.0

                            # Find the impact for this output sector in this year for this input sector
                            for scenario_idx, scenario_data in individual_results[year].items():
                                scenario_idx_num = int(scenario_idx.split('_')[1])
                                scenario_row = scenario_analyzer.scenarios_data.iloc[scenario_idx_num]

                                if (str(scenario_row['sector']) == sector_info['sector'] and
                                    scenario_row['input'] == sector_info['input_table']):

                                    for impact in scenario_data['result']['impacts']:
                                        if str(impact['sector_code']) == sector_code:
                                            impact_value = impact['impact']
                                            break
                                    break

                            row[str(year)] = impact_value

                        matrix_data.append(row)

                    # Create DataFrame and sort by latest year impact
                    if matrix_data:
                        matrix_df = pd.DataFrame(matrix_data)

                        # Sort by the latest year's impact (descending absolute value)
                        latest_year_col = str(latest_year)
                        if latest_year_col in matrix_df.columns:
                            matrix_df['abs_latest'] = matrix_df[latest_year_col].abs()
                            matrix_df = matrix_df.sort_values('abs_latest', ascending=False)
                            matrix_df = matrix_df.drop('abs_latest', axis=1)

                        # Ensure all column names are strings
                        matrix_df.columns = [str(col) for col in matrix_df.columns]

                        # Format numbers for display
                        display_matrix = matrix_df.copy()
                        for year in available_years:
                            year_col = str(year)
                            if year_col in display_matrix.columns:
                                display_matrix[year_col] = display_matrix[year_col].apply(lambda x: f"{x:,.2f}" if x != 0 else "0.00")

                        # Ensure display matrix column names are also strings
                        display_matrix.columns = [str(col) for col in display_matrix.columns]

                        st.markdown("#### Output Sector Impacts by Year (Million KRW)")
                        st.dataframe(display_matrix, use_container_width=True, height=400)

                        # Add charts below the table
                        st.markdown("#### 📈 Trend Charts")

                        # Prepare data for charts
                        chart_df = matrix_df.copy()
                        year_columns = [str(year) for year in available_years]

                        # Chart 1: All sectors over time (line chart)
                        st.markdown("**All Sectors Over Time**")

                        # Create line chart data for ALL sectors
                        line_chart_data = {}
                        for _, row in chart_df.iterrows():
                            sector_label = f"{row['Sector Code']}: {row['Sector Name'][:25]}..."
                            line_chart_data[sector_label] = [row[year_col] for year_col in year_columns]

                        # Convert to DataFrame for Streamlit
                        if line_chart_data:
                            line_df = pd.DataFrame(line_chart_data, index=available_years)
                            st.line_chart(line_df, height=500)

                        # Chart 2: Total impact by year (aggregate line chart)
                        st.markdown("**Total Impact by Year**")

                        # Calculate total impact per year
                        year_totals = {}
                        for year_col in year_columns:
                            if year_col in chart_df.columns:
                                year_totals[int(year_col)] = chart_df[year_col].sum()

                        if year_totals:
                            total_df = pd.DataFrame(list(year_totals.items()), columns=['Year', 'Total Impact'])
                            total_df = total_df.set_index('Year')
                            st.line_chart(total_df, height=300)

                        # Download button for this specific input sector
                        csv_data = matrix_df.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label=f"📥 Download {sector_info['sector']} Results",
                            data=csv_data,
                            file_name=f"scenario_{effect_type}_{sector_info['sector']}_{sector_info['input_table']}.csv",
                            mime="text/csv",
                            key=f"download_{table_type}_{effect_type}_{sector_key}"
                        )
                    else:
                        st.info("No sector impact data available")
                else:
                    st.info("No output sector data found")
            else:
                st.warning("No years available for analysis")

if __name__ == "__main__":
    main()