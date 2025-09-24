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
            # Handle hydrogen analysis specially
            with st.spinner("Calculating hydrogen effects..."):
                try:
                    hydrogen_results = analyzer.calculate_hydrogen_effects(demand_change, quiet=True)

                    # Display hydrogen results
                    st.subheader("🔋 Hydrogen Usage Analysis")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Impact", f"{hydrogen_results['total_impact']:,.0f}")
                    with col2:
                        st.metric("Sector-Category Combinations", hydrogen_results['num_affected_sectors'])
                    with col3:
                        st.metric("Demand Change Multiplier", f"{demand_change:,.0f}")

                    # Results table - Matrix format: rows=sectors, columns=categories, values=impact
                    if hydrogen_results['impacts']:
                        # Get impact matrix (main output format)
                        impact_matrix = analyzer.get_hydrogen_impact_matrix(demand_change)

                        # Format for display
                        display_df = impact_matrix.copy()
                        for col in ['Production (백만원)', 'Storage (백만원)', 'Transportation (백만원)', 'Utilization (백만원)', 'Total (백만원)']:
                            display_df[col] = display_df[col].apply(lambda x: f"{x:,.2f}")

                        # Display table
                        st.dataframe(display_df, use_container_width=True, height=600)

                        # Show column totals
                        st.subheader("Percentage allocated")
                        col_totals = {}
                        # 각 컬럼에 맞는 값을 직접 할당하려면 아래처럼 작성하면 됩니다.
                        col_totals['Production (%)'] = 34.1
                        col_totals['Storage (%)'] = 10.4
                        col_totals['Transportation (%)'] = 11.2
                        col_totals['Utilization (%)'] = 44.4
                        col_totals['Total (%)'] = 100.0

                        totals_df = pd.DataFrame([col_totals])
                        totals_df = totals_df.round(2)
                        st.dataframe(totals_df, use_container_width=True)

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
        coefficient_types = ["A", "Am", "Ad", "indirect_prod", "indirect_import", "value_added", "jobcoeff", "directemploycoeff"]
        coeff_names = {
            "A": "Direct Total",
            "Am": "Direct Import", 
            "Ad": "Direct Domestic",
            "indirect_prod": "Indirect Production",
            "indirect_import": "Indirect Import",
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

        if scenario_info:
            col1, col2, col3, col4, col5 = st.columns(5)
        else:
            col1, col2, col3, col4 = st.columns(4)

        if all_results["A"]:
            with col1:
                st.metric("Target Sector", f"{selected_sector}")
            with col2:
                st.metric("Product", all_results["A"]["target_product"])
            with col3:
                st.metric("Demand Change", f"{demand_change:,.0f}")
            with col4:
                st.metric("Analysis Types", len([r for r in all_results.values() if r is not None]))

            if scenario_info:
                with col5:
                    st.metric("Demand Change Scenario", scenario_info)
        
        # Create tabs: Summary first, then each coefficient type
        tab_names = ["📊 Summary"] + [f"{coeff_names[ct]} ({ct})" for ct in coefficient_types]
        tabs = st.tabs(tab_names)
        
        # Summary tab (first tab)
        with tabs[0]:
            st.subheader("📊 Complete Analysis Summary")
            
            # Overall comparison table - separate economic and job effects
            economic_summary = []
            job_summary = []
            
            # Separate data by effect type
            economic_coeffs = ["A", "Am", "Ad", "indirect_prod", "indirect_import", "value_added"]
            job_coeffs = ["jobcoeff", "directemploycoeff"]
            
            for coeff_type in economic_coeffs:
                if all_results[coeff_type]:
                    results = all_results[coeff_type]
                    economic_summary.append({
                        'Coefficient Type': f"{coeff_names[coeff_type]} ({coeff_type})",
                        'Total Impact': f"{results['total_impact']:,.0f}",
                        'Number of Affected Sectors': results['num_affected_sectors'],
                        'Top Impact Sector': results['impacts'][0]['sector_name'] if results['impacts'] else 'None',
                        'Top Impact Value': f"{results['impacts'][0]['impact']:,.0f}" if results['impacts'] else '0'
                    })
            
            for coeff_type in job_coeffs:
                if all_results[coeff_type]:
                    results = all_results[coeff_type]
                    job_summary.append({
                        'Coefficient Type': f"{coeff_names[coeff_type]} ({coeff_type})",
                        'Total Jobs': f"{results['total_impact']:,.0f}",
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
                                df = df[['sector_code', 'sector_name', 'impact']]
                                df.columns = ['Sector Code', 'Sector Name', 'Impact']
                                df = df.sort_values('Impact', key=lambda x: abs(x), ascending=False)
                                
                                # Add metadata as first rows
                                metadata = pd.DataFrame([
                                    ['Analysis Details', '', ''],
                                    ['Target Sector', results['target_sector'], ''],
                                    ['Target Product', results['target_product'], ''],
                                    ['Demand Change', results['demand_change'], ''],
                                    ['Coefficient Type', f"{results['coeff_name']} ({coeff_type})", ''],
                                    ['Total Impact', results['total_impact'], ''],
                                    ['', '', ''],
                                    ['Sector Code', 'Sector Name', 'Impact']
                                ], columns=['Sector Code', 'Sector Name', 'Impact'])
                                
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
                            label="📊 Download Complete Analysis (CSV)",
                            data=csv_data,
                            file_name=f"complete_io_analysis_{selected_sector}_{demand_change}.csv",
                            mime="text/csv"
                        )
                
                # Detailed comparison charts - separate economic and job effects
                st.subheader("📈 Impact Comparison")
                
                # Separate coefficient types by category
                economic_coeffs = ["A", "Am", "Ad", "indirect_prod", "indirect_import", "value_added"]
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
                        st.bar_chart(job_df.set_index('Coefficient Type')['Total Jobs'])
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
                    st.metric("Total Impact", f"{results['total_impact']:,.0f}")
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
                    
                    # Display controls
                    show_top = st.selectbox(f"Show top", [20, 50, 100, "All"], index=0, key=f"top_{coeff_type}")
                    
                    # Format the DataFrame for display
                    display_df = df[['sector_code', 'sector_name', 'impact']].copy()
                    display_df.columns = ['Code', 'Sector Name', 'Impact']
                    display_df['Impact'] = display_df['Impact'].apply(lambda x: f"{x:,.2f}")
                    display_df.index = range(1, len(display_df) + 1)
                    
                    # Filter data based on selection
                    if show_top != "All":
                        filtered_df = display_df.head(show_top)
                    else:
                        filtered_df = display_df
                    
                    # Display table
                    st.dataframe(
                        filtered_df,
                        width=800,
                        height=400
                    )
                    
                    # Download button
                    csv_data = df[['sector_code', 'sector_name', 'impact']].to_csv(index=False)
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

if __name__ == "__main__":
    main()