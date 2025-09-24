import streamlit as st
import pandas as pd
from libs.io_analyzer import IOTableAnalyzer

# Configure Streamlit page
st.set_page_config(
    page_title="Steel-Coal I-O Table Analyzer", 
    page_icon="🏭",
    layout="wide"
)

@st.cache_data
def load_analyzer():
    """Load the analyzer with caching to avoid reloading data."""
    return IOTableAnalyzer()

def main():
    st.title("🏭 Steel Input Output Analysis Results")
    st.markdown("---")
    
    # Load analyzer
    with st.spinner("Loading I-O Table data..."):
        analyzer = load_analyzer()
        # Load demand change data for scenario selection
        try:
            analyzer.load_damageshock_data()
            shock_available = True
        except Exception as e:
            shock_available = False
            st.warning(f"Demand change data not available: {e}")

        # Load hydrogen coefficient data
        try:
            analyzer.load_hydrogen_coefficient()
            hydrogen_available = True
        except Exception as e:
            hydrogen_available = False
            st.warning(f"Hydrogen coefficient data not available: {e}")

    # Sidebar for inputs
    st.sidebar.header("Analysis Parameters")

    # Demand change source selection section
    st.sidebar.markdown("### 📊 Demand Change Source")

    demand_source = st.sidebar.radio(
        "Select demand change source:",
        ["Manual Input", "Demand Change Scenario"],
        help="Choose between manual input or predefined demand change scenarios"
    )

    # Initialize auto_selected_sector variable
    auto_selected_sector = None

    if demand_source == "Manual Input":
        demand_change = st.sidebar.number_input(
            "Demand Change (단위: 백만원)",
            value=1000000,
            step=100000,
            format="%d",
            help="Enter the change in final demand (positive or negative) (단위: 백만원)"
        )
        scenario_info = None

    elif demand_source == "Demand Change Scenario" and shock_available:
        # Get available scenarios and columns
        try:
            scenarios = analyzer.get_shock_scenarios()
            shock_columns = analyzer.get_shock_columns()

            # Filter out 2022, 2023, 2024 from shock_columns
            if shock_columns:
                shock_columns = [col for col in shock_columns if col not in [2022, 2023, 2024, '2022', '2023', '2024']]

            if scenarios and shock_columns:
                selected_scenario = st.sidebar.selectbox(
                    "Select Scenario (내역)",
                    scenarios,
                    help="Choose a demand change scenario from the data sheet"
                )

                # Auto-select sector based on scenario
                if "석탄사용감소량" in selected_scenario:
                    auto_selected_sector = "0611"
                elif any(keyword in selected_scenario for keyword in ["재생에너지", "부생가스전력", "전기로"]):
                    auto_selected_sector = "4506"
                elif "수소사용량" in selected_scenario:
                    # For hydrogen usage, we'll handle this specially
                    auto_selected_sector = None  # Will be handled by hydrogen coefficient selection

                selected_column = st.sidebar.selectbox(
                    "Select Year/Column",
                    shock_columns,
                    help="Choose the year or column for the shock value"
                )

                # Get the demand change value
                try:
                    demand_change = analyzer.get_shock_value(selected_scenario, selected_column)
                    st.sidebar.success(f"Value: {demand_change/1000:,.0f} (백만원)")
                    scenario_info = f"{selected_scenario} ({selected_column})"

                    # Check if this is hydrogen usage scenario
                    is_hydrogen_scenario = "수소사용량" in selected_scenario and hydrogen_available

                except Exception as e:
                    st.sidebar.error(f"Error getting demand change value: {e}")
                    demand_change = 1000000
                    scenario_info = None
                    is_hydrogen_scenario = False
            else:
                st.sidebar.error("No demand change scenarios or columns available")
                demand_change = 1000000
                scenario_info = None
                auto_selected_sector = None

        except Exception as e:
            st.sidebar.error(f"Error loading demand change data: {e}")
            demand_change = 1000000
            scenario_info = None
            auto_selected_sector = None

    else:
        # Fallback to manual input if SHOCK not available
        demand_change = st.sidebar.number_input(
            "Demand Change (단위: 백만원)",
            value=1000000,
            step=100000,
            format="%d",
            help="Enter the change in final demand (positive or negative, 단위: 백만원)"
        )
        st.sidebar.caption("단위: 백만원")
        scenario_info = None
        auto_selected_sector = None

    # Check if this is hydrogen scenario for UI visibility
    is_hydrogen_scenario_for_ui = False
    if (demand_source == "Demand Change Scenario" and shock_available and
        'selected_scenario' in locals() and "수소사용량" in selected_scenario and hydrogen_available):
        is_hydrogen_scenario_for_ui = True

    # Sector selection section (hide for hydrogen scenarios)
    if not is_hydrogen_scenario_for_ui:
        st.sidebar.markdown("### 🏭 Sector Selection")

        # Get sector options (already formatted for display)
        sector_options = analyzer.get_sector_options()
        sector_list = list(sector_options.values())  # These are already formatted as "code: name"

        # Auto-select sector index based on scenario if applicable
        default_index = 0
        if demand_source == "Demand Change Scenario" and shock_available and auto_selected_sector:
            # Find the index of the auto-selected sector in the list
            for i, sector_display in enumerate(sector_list):
                if sector_display.startswith(auto_selected_sector + ":"):
                    default_index = i
                    st.sidebar.info(f"Auto-selected sector: {auto_selected_sector}")
                    break

        # Input controls
        selected_sector_display = st.sidebar.selectbox(
            "Select Sector",
            options=sector_list,
            index=default_index,
            help="Choose the target sector for analysis (auto-selected based on scenario)"
        )

        # Extract formatted sector code using analyzer method
        selected_sector = analyzer.get_sector_from_display(selected_sector_display)
    else:
        # For hydrogen scenarios, we don't need sector selection
        selected_sector = None
        selected_sector_display = "Hydrogen Analysis (All Sectors)"

    # Analysis button - will calculate all coefficient types
    analyze_button = st.sidebar.button("🔍 Analyze All Effects", type="primary")
    
    # Main content area with tabs
    if analyze_button or st.session_state.get('auto_analyze', False):
        
        # Check if this is hydrogen scenario
        if 'is_hydrogen_scenario' in locals() and is_hydrogen_scenario:
            # Handle hydrogen analysis specially using all coefficient sheets
            with st.spinner("Calculating hydrogen effects using all coefficient sheets..."):
                try:
                    hydrogen_results = analyzer.calculate_hydrogen_effects(demand_change, quiet=True)

                    # Display hydrogen results
                    st.subheader("🔋 Hydrogen Year-based Analysis (All Coefficient Sheets)")

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Impact", f"{hydrogen_results['total_impact']:,.0f}")
                    with col2:
                        st.metric("Affected Sectors", hydrogen_results['num_affected_sectors'])
                    with col3:
                        st.metric("Demand Change", f"{demand_change:,.0f}")
                    with col4:
                        sheets_used = hydrogen_results.get('sheets_used', [])
                        st.metric("Coefficient Sheets", f"{len(sheets_used)} sheets")

                    # Display used sheets
                    if sheets_used:
                        st.info(f"Using coefficient sheets: {', '.join(sheets_used)}")

                    # Results table - Matrix format: rows=sectors, columns=years, values=impact
                    if hydrogen_results['impacts']:
                        # Get impact matrix (main output format: sectors x years)
                        impact_matrix = analyzer.get_hydrogen_impact_matrix(demand_change)

                        if not impact_matrix.empty:
                            # Format for display
                            display_df = impact_matrix.copy()

                            # Format numeric columns
                            numeric_cols = [col for col in display_df.columns if '(백만원)' in col]
                            for col in numeric_cols:
                                display_df[col] = display_df[col].apply(lambda x: f"{x:,.2f}")

                            st.markdown("### 📊 Year-based Impact Matrix (Rows: Sectors, Columns: Years)")
                            st.dataframe(display_df, use_container_width=True, height=600)

                            # Show year breakdown
                            st.markdown("### 📈 Year-wise Summary")
                            year_columns = [col for col in impact_matrix.columns if '(백만원)' in col and col != 'Total (백만원)']

                            if year_columns:
                                # Show first 5 years in metrics
                                display_years = year_columns[:5]
                                cols = st.columns(len(display_years))

                                for i, col in enumerate(display_years):
                                    year_name = col.replace(' (백만원)', '')
                                    total = impact_matrix[col].sum()
                                    with cols[i]:
                                        st.metric(f"{year_name}", f"{total:,.0f}")

                                if len(year_columns) > 5:
                                    st.info(f"... and {len(year_columns) - 5} more years. See full matrix above.")

                        else:
                            st.warning("No impact matrix data available.")

                        # Download buttons
                        col1, col2 = st.columns(2)

                        with col1:
                            # CSV download with Korean encoding support
                            import io
                            csv_buffer = io.StringIO()
                            impact_matrix.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                            st.download_button(
                                label="📥 Download CSV",
                                data=csv_buffer.getvalue(),
                                file_name=f"hydrogen_economic_impact_{demand_change}.csv",
                                mime="text/csv"
                            )

                        with col2:
                            # Excel export using the analyzer's method
                            if st.button("📊 Generate Excel Report", key="hydrogen_excel"):
                                with st.spinner("Generating Excel report..."):
                                    try:
                                        output_path = analyzer.export_hydrogen_results_to_excel(hydrogen_results)
                                        st.success(f"Excel report generated!")
                                        st.info(f"File saved to: {output_path}")

                                        # Read the file for download
                                        with open(output_path, 'rb') as f:
                                            excel_data = f.read()

                                        st.download_button(
                                            label="📥 Download Excel",
                                            data=excel_data,
                                            file_name=f"hydrogen_impact_matrix_{demand_change}.xlsx",
                                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                        )
                                    except Exception as e:
                                        st.error(f"Error generating Excel report: {str(e)}")

                    else:
                        st.warning("No hydrogen impacts found.")

                except Exception as e:
                    st.error(f"Error calculating hydrogen effects: {str(e)}")

            return  # Exit early for hydrogen analysis

        # Calculate all coefficient types including job coefficients for regular analysis
        all_results = {}
        coefficient_types = ["indirect_prod", "indirect_import", "value_added", "jobcoeff", "directemploycoeff"]
        coeff_names = {
            "indirect_prod": "Domestic Production-Inducing Effect",
            "indirect_import": "Import-Inducing Effect",
            "value_added": "Value-Added Creation Effect",
            "jobcoeff": "Job Creating Effect",
            "directemploycoeff": "Direct Employment Effect"
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

        if scenario_info:
            col1, col2, col3, col4 = st.columns(4)
        else:
            col1, col2, col3 = st.columns(3)

        # Find first available result for product name
        first_result = next((result for result in all_results.values() if result is not None), None)
        if first_result:
            with col1:
                st.metric("Target Sector", f"{selected_sector}")
            with col2:
                st.metric("Product", first_result["target_product"])
            with col3:
                st.metric("Demand Change (백만원)", f"{demand_change/1000:,.0f}")
            if scenario_info:
                with col4:
                    st.metric("Demand Change Scenario", scenario_info)
        
            st.subheader("📊 Economic and Employment Impact")
            
            # Create consolidated impact matrix with all coefficient results
            sector_impacts = {}

            # Collect all unique sectors first
            all_sectors = set()
            for coeff_type in coefficient_types:
                if all_results[coeff_type] and all_results[coeff_type]['impacts']:
                    for impact in all_results[coeff_type]['impacts']:
                        sector_code = str(impact['sector_code']).replace(',', '')  # Remove commas from sector codes
                        all_sectors.add((sector_code, impact['sector_name']))

            # Sort sectors by code for consistent ordering
            sorted_sectors = sorted(list(all_sectors), key=lambda x: x[0])

            # Build the consolidated matrix
            matrix_data = []
            for idx, (sector_code, sector_name) in enumerate(sorted_sectors, 1):
                row = {
                    '코드번호': sector_code,
                    '섹터명': sector_name
                }

                # Add impact values for each coefficient type
                for coeff_type in coefficient_types:
                    if all_results[coeff_type]:
                        # Find matching sector impact
                        sector_impact = 0
                        for impact in all_results[coeff_type]['impacts']:
                            impact_code = str(impact['sector_code']).replace(',', '')
                            if impact_code == sector_code:
                                sector_impact = impact['impact']
                                break

                        # Add unit suffix based on coefficient type
                        if coeff_type in ["jobcoeff", "directemploycoeff"]:
                            unit = "명"
                        else:
                            unit = "백만원"

                        col_name = f"{coeff_names[coeff_type]} ({unit})"
                        row[col_name] = f"{sector_impact:,.2f}"

                matrix_data.append(row)

            # Display the consolidated matrix with row and column sums
            if matrix_data:
                consolidated_df = pd.DataFrame(matrix_data)

                # Add column totals (sum for each coefficient type)
                numeric_columns = [col for col in consolidated_df.columns if col not in ['코드번호', '섹터명']]

                # Calculate column sums
                column_sums = {'코드번호': 'Total', '섹터명': '열합계'}
                for col in numeric_columns:
                    # Convert formatted strings back to numbers for sum calculation
                    numeric_values = consolidated_df[col].str.replace(',', '').astype(float)
                    column_sums[col] = f"{numeric_values.sum():,.2f}"

                # 경제효과 계산
                econ_columns = ['Domestic Production-Inducing Effect (백만원)', 'Import-Inducing Effect (백만원)', 'Value-Added Creation Effect (백만원)']
                row_totals = []
                for _, row in consolidated_df.iterrows():
                    total = 0
                    for col in econ_columns:
                        value = float(row[col].replace(',', ''))
                        total += abs(value)  # Use absolute values for row totals
                    row_totals.append(f"{total:,.2f}")
                consolidated_df['경제효과(백만원)'] = row_totals

                # Add column sums as the last row
                column_sums['경제효과(백만원)'] = f"{sum(float(val.replace(',', '')) for val in row_totals):,.2f}"
                consolidated_df = pd.concat([consolidated_df, pd.DataFrame([column_sums])], ignore_index=True)

                st.dataframe(consolidated_df, use_container_width=True, height=600)

            # Prepare data for download
            all_summary_data = matrix_data
            if all_summary_data:
                summary_df = pd.DataFrame(all_summary_data)
                
                # Combined results for download
                st.subheader("📥 Download Economic and Employment Impact")
                
                # Create Excel file with multiple sheets
                try:
                    from io import BytesIO

                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        summary_df.to_excel(writer, sheet_name='종합', index=False)
                    buffer.seek(0)
                    
                    st.download_button(
                        label="📊 Download Economic and Employment Impact (Excel)",
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
                                combined_data.append({
                                    'coefficient_type': coeff_type,
                                    'coefficient_name': coeff_names[coeff_type],
                                    'sector_code': impact['sector_code'],
                                    'sector_name': impact['sector_name'],
                                    'impact': impact['impact']
                                })
                    
                    if combined_data:
                        combined_df = pd.DataFrame(combined_data)
                        csv_data = combined_df.to_csv(index=False)
                        st.download_button(
                            label="📊 Download Economic and Employment Impact (CSV)",
                            data=csv_data,
                            file_name=f"complete_io_analysis_{selected_sector}_{demand_change}.csv",
                            mime="text/csv"
                        )
                
                # Comprehensive Scenario Impact Table
                st.subheader("📊 Comprehensive Scenario Impact Table")

                try:
                    comprehensive_table = analyzer.create_comprehensive_scenario_table()
                    if not comprehensive_table.empty:
                        st.markdown("**Year-wise Total Effects by Scenario Type**")

                        # Display the comprehensive table
                        st.dataframe(comprehensive_table, use_container_width=True, height=600)

                        # Download option for comprehensive table
                        col1, col2 = st.columns(2)
                        with col1:
                            # CSV download
                            import io
                            csv_buffer = io.StringIO()
                            comprehensive_table.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                            st.download_button(
                                label="📥 Download Comprehensive Table (CSV)",
                                data=csv_buffer.getvalue(),
                                file_name="comprehensive_scenario_impact_table.csv",
                                mime="text/csv"
                            )

                        with col2:
                            # Excel download
                            from io import BytesIO
                            excel_buffer = BytesIO()
                            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                                comprehensive_table.to_excel(writer, sheet_name='Comprehensive_Impact', index=False)
                            excel_buffer.seek(0)

                            st.download_button(
                                label="📊 Download Comprehensive Table (Excel)",
                                data=excel_buffer,
                                file_name="comprehensive_scenario_impact_table.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    else:
                        st.warning("No comprehensive scenario data available.")

                except Exception as e:
                    st.warning(f"Could not generate comprehensive scenario table: {str(e)}")

                # Detailed comparison charts - separate economic and job effects
                st.subheader("📈 Visualization")
            else:
                st.warning("No results available for summary.")
        

    else:
        st.info("👈 Select a sector, enter demand change, and click 'Analyze All Effects' to see results in tabs below")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
    <p>Steel-Coal I-O Table Analyzer | Built with Streamlit | Data: Korean I-O Table 2020</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()