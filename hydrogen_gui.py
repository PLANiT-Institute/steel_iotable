import streamlit as st
import pandas as pd
from libs.hydrogen_analyzer import HydrogenTableAnalyzer

def show_hydrogen_analysis():
    """Hydrogen Table Analysis page using HydrogenTableAnalyzer."""
    st.title("🔬 Hydrogen Table Analysis")
    st.markdown("---")

    # Load analyzer
    @st.cache_data
    def load_hydrogen_analyzer():
        """Load the hydrogen analyzer with caching to avoid reloading data."""
        return HydrogenTableAnalyzer()

    with st.spinner("Loading Hydrogen Table data..."):
        h_analyzer = load_hydrogen_analyzer()

    # Sidebar for inputs
    st.sidebar.header("Hydrogen Analysis Parameters")

    # Hydrogen scenario selection
    scenarios = h_analyzer.get_hydrogen_scenarios()
    selected_scenario = st.sidebar.selectbox(
        "Select Hydrogen Scenario",
        options=scenarios,
        index=0,
        help="Choose the hydrogen scenario for analysis (H2P, H2S, H2T, H2U)"
    )

    demand_change = st.sidebar.number_input(
        "Demand Change (Unit: million won)",
        value=1000000,
        step=100000,
        format="%d",
        help="Enter the change in final demand (positive or negative)"
    )

    # Analysis button - will calculate all coefficient types
    analyze_button = st.sidebar.button("🔍 Analyze Hydrogen Effects", type="primary")

    # Main content area with tabs
    if analyze_button or st.session_state.get('auto_analyze_hydrogen', False):

        # Calculate all coefficient types
        all_results = {}
        coefficient_types = ["productioncoeff", "valueaddedcoeff", "jobcoeff", "directemploycoeff"]
        coeff_names = {
            "productioncoeff": "Production-inducing effect",
            "valueaddedcoeff": "Value-Added creation",
            "jobcoeff": "Wage-inducing effect",
            "directemploycoeff": "Direct Employment effect"
        }

        with st.spinner("Calculating all hydrogen coefficient effects..."):
            for coeff_type in coefficient_types:
                try:
                    results = h_analyzer.calculate_hydrogen_effects(
                        selected_scenario,
                        demand_change,
                        coeff_type,
                        quiet=True  # Suppress output for GUI
                    )
                    all_results[coeff_type] = results
                except Exception as e:
                    st.error(f"Error calculating {coeff_type}: {str(e)}")
                    all_results[coeff_type] = None

        # Display summary
        st.subheader("📊 Hydrogen Analysis Summary")
        col1, col2, col3 = st.columns(3)

        if all_results["productioncoeff"]:
            with col1:
                st.metric("Hydrogen Scenario", selected_scenario)
            with col2:
                st.metric("Demand Change (million won)", f"{demand_change:,.0f}")
            with col3:
                st.metric("Analysis Types", len([r for r in all_results.values() if r is not None]))


        # Create tabs: Summary first, then each coefficient type
        tab_names = ["📊 Summary"] + [f"{coeff_names[ct]}" for ct in coefficient_types]
        tabs = st.tabs(tab_names)

        # Summary tab (first tab)
        with tabs[0]:
            st.subheader("📊 Complete Hydrogen Analysis Summary")

            # Overall comparison table - separate economic and job effects
            economic_summary = []
            job_summary = []

            # Separate data by effect type
            economic_coeffs = ["productioncoeff", "valueaddedcoeff"]
            job_coeffs = ["directemploycoeff"]

            for coeff_type in economic_coeffs:
                if all_results[coeff_type]:
                    results = all_results[coeff_type]
                    economic_summary.append({
                        'Coefficient Type': f"{coeff_names[coeff_type]} ({coeff_type})",
                        'Total Economic Impact (million won)': f"{results['total_economic_impact']:,.0f}",
                        'Affected Sectors': results['num_affected_sectors'],
                        'Top Impact Sector': results['impacts'][0]['sector_name'] if results['impacts'] else 'None',
                        'Top Impact Value (million won)': f"{results['impacts'][0]['impact']:,.0f}" if results['impacts'] else '0'
                    })

            for coeff_type in job_coeffs:
                if all_results[coeff_type]:
                    results = all_results[coeff_type]
                    job_summary.append({
                        'Coefficient Type': f"{coeff_names[coeff_type]} ({coeff_type})",
                        'Total Jobs (person/billion won)': f"{results['total_job_impact']:,.0f}",
                        'Affected Sectors': results['num_affected_sectors'],
                        'Top Impact Sector': results['impacts'][0]['sector_name'] if results['impacts'] else 'None',
                        'Top Impact Value': f"{results['impacts'][0]['impact']:,.0f}" if results['impacts'] else '0'
                    })

            # Display tables
            if economic_summary and job_summary:
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**💰 Economic Effect Summary**")
                    economic_df = pd.DataFrame(economic_summary)
                    st.dataframe(economic_df, use_container_width=True)

                with col2:
                    st.markdown("**👥 Employment Effect Summary**")
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

            # Combined summary for download
            all_summary_data = economic_summary + job_summary
            if all_summary_data:
                summary_df = pd.DataFrame(all_summary_data)

                # Combined results for download
                st.subheader("📥 Download Complete Hydrogen Analysis")

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
                                    ['Hydrogen Scenario', results['scenario'], ''],
                                    ['Demand Change', results['demand_change'], ''],
                                    ['Coefficient Type', f"{results['coeff_name']} ({coeff_type})", ''],
                                    ['Total Economic Impact', results['total_economic_impact'], ''],
                                    ['Total Job Impact', results['total_job_impact'], ''],
                                    ['', '', ''],
                                    ['Sector Code', 'Sector Name', 'Impact']
                                ], columns=['Sector Code', 'Sector Name', 'Impact'])

                                final_df = pd.concat([metadata, df], ignore_index=True)
                                sheet_name = coeff_names[coeff_type][:30]  # Excel sheet name limit
                                final_df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

                    buffer.seek(0)

                    st.download_button(
                        label="📊 Download Complete Hydrogen Analysis (Excel)",
                        data=buffer,
                        file_name=f"hydrogen_analysis_{selected_scenario}_{demand_change}.xlsx",
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
                                    'scenario': selected_scenario,
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
                            label="📊 Download Complete Hydrogen Analysis (CSV)",
                            data=csv_data,
                            file_name=f"hydrogen_analysis_{selected_scenario}_{demand_change}.csv",
                            mime="text/csv"
                        )

                # Detailed comparison charts - separate economic and job effects
                st.subheader("📈 Impact Comparison")

                # Separate coefficient types by category
                economic_coeffs = ["productioncoeff", "valueaddedcoeff"]
                job_coeffs = ["jobcoeff", "directemploycoeff"]

                # Create economic effects chart data
                economic_chart_data = []
                for coeff_type in economic_coeffs:
                    if all_results[coeff_type]:
                        economic_chart_data.append({
                            'Coefficient Type': coeff_names[coeff_type],
                            'Total Economic Impact': all_results[coeff_type]['total_economic_impact'],
                            'Affected Sectors': all_results[coeff_type]['num_affected_sectors']
                        })

                # Create job effects chart data
                job_chart_data = []
                for coeff_type in job_coeffs:
                    if all_results[coeff_type]:
                        job_chart_data.append({
                            'Coefficient Type': coeff_names[coeff_type],
                            'Total Jobs': all_results[coeff_type]['total_job_impact'],
                            'Affected Sectors': all_results[coeff_type]['num_affected_sectors']
                        })

                # Display charts
                if economic_chart_data and job_chart_data:
                    # Two separate sections for economic vs job effects
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**💰 Economic Effects**")
                        economic_df = pd.DataFrame(economic_chart_data)
                        st.caption("Total Economic Impact by Type")
                        st.bar_chart(economic_df.set_index('Coefficient Type')['Total Economic Impact'])

                        st.caption("Economic Sectors Affected")
                        st.bar_chart(economic_df.set_index('Coefficient Type')['Affected Sectors'])


                    with col2:
                        st.markdown("**👥 Employment Effects**")
                        job_df = pd.DataFrame(job_chart_data)
                        st.caption("Total Jobs Created/Affected")
                        st.bar_chart(job_df.set_index('Coefficient Type')['Total Jobs'])

                        st.caption("Employment Sectors Affected")
                        st.bar_chart(job_df.set_index('Coefficient Type')['Affected Sectors'])

                elif economic_chart_data:
                    # Only economic data available
                    economic_df = pd.DataFrame(economic_chart_data)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.bar_chart(economic_df.set_index('Coefficient Type')['Total Economic Impact'])
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
                        st.bar_chart(job_df.set_index('Coefficient Type')['Affected Sectors'])
                        st.caption("Employment Sectors Affected")
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
                    st.metric("Total Economic Impact", f"{results['total_economic_impact']:,.0f}")
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
                        use_container_width=True,
                        height=600
                    )

                    # Download button
                    csv_data = df[['sector_code', 'sector_name', 'impact']].to_csv(index=False)
                    st.download_button(
                        label=f"📥 Download {coeff_names[coeff_type]} Results",
                        data=csv_data,
                        file_name=f"hydrogen_analysis_{selected_scenario}_{coeff_type}.csv",
                        mime="text/csv",
                        key=f"download_hydrogen_{coeff_type}"
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
        st.info("👈 Select a hydrogen scenario, enter demand change, and click 'Analyze Hydrogen Effects' to see results in tabs below")

        # Show available scenarios information
        st.subheader("🔬 Available Hydrogen Scenarios")
        scenario_info = pd.DataFrame({
            'Scenario': scenarios,
            'Description': [
                'Hydrogen Production (H2P)',
                'Hydrogen Storage (H2S)',
                'Hydrogen Transportation (H2T)',
                'Hydrogen Utilization (H2U)'
            ]
        })
        st.dataframe(scenario_info, use_container_width=True)