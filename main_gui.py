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
    st.title("🏭 Steel-Coal I-O Table Direct Effects Analyzer")
    st.markdown("---")
    
    # Load analyzer
    with st.spinner("Loading I-O Table data..."):
        analyzer = load_analyzer()
    
    # Sidebar for inputs
    st.sidebar.header("Analysis Parameters")
    
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
        "Demand Change",
        value=1000000,
        step=100000,
        format="%d",
        help="Enter the change in final demand (positive or negative)"
    )
    
    # Analysis button - will calculate all coefficient types
    analyze_button = st.sidebar.button("🔍 Analyze All Effects", type="primary")
    
    # Main content area with tabs
    if analyze_button or st.session_state.get('auto_analyze', False):
        
        # Calculate all coefficient types
        all_results = {}
        coefficient_types = ["A", "Am", "Ad", "indirect_prod", "indirect_import", "value_added"]
        coeff_names = {
            "A": "Direct Total",
            "Am": "Direct Import", 
            "Ad": "Direct Domestic",
            "indirect_prod": "Indirect Production",
            "indirect_import": "Indirect Import",
            "value_added": "Value-Added"
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
        
        if all_results["A"]:
            with col1:
                st.metric("Target Sector", f"{selected_sector}")
            with col2:
                st.metric("Product", all_results["A"]["target_product"])
            with col3:
                st.metric("Demand Change", f"{demand_change:,.0f}")
            with col4:
                st.metric("Analysis Types", len([r for r in all_results.values() if r is not None]))
        
        # Create tabs: Summary first, then each coefficient type
        tab_names = ["📊 Summary"] + [f"{coeff_names[ct]} ({ct})" for ct in coefficient_types]
        tabs = st.tabs(tab_names)
        
        # Summary tab (first tab)
        with tabs[0]:
            st.subheader("📊 Complete Analysis Summary")
            
            # Overall comparison table
            summary_data = []
            for coeff_type in coefficient_types:
                if all_results[coeff_type]:
                    results = all_results[coeff_type]
                    summary_data.append({
                        'Coefficient Type': f"{coeff_names[coeff_type]} ({coeff_type})",
                        'Total Impact': f"{results['total_impact']:,.0f}",
                        'Affected Sectors': results['num_affected_sectors'],
                        'Top Impact Sector': results['impacts'][0]['sector_name'] if results['impacts'] else 'None',
                        'Top Impact Value': f"{results['impacts'][0]['impact']:,.0f}" if results['impacts'] else '0'
                    })
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, width='stretch')
                
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
                    st.error("Excel export requires openpyxl. Using CSV export instead.")
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
                
                # Detailed comparison charts
                st.subheader("📈 Impact Comparison")
                
                # Create comparison chart data
                chart_data = []
                for coeff_type in coefficient_types:
                    if all_results[coeff_type]:
                        chart_data.append({
                            'Coefficient Type': coeff_names[coeff_type],
                            'Total Impact': all_results[coeff_type]['total_impact'],
                            'Affected Sectors': all_results[coeff_type]['num_affected_sectors']
                        })
                
                if chart_data:
                    chart_df = pd.DataFrame(chart_data)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.bar_chart(chart_df.set_index('Coefficient Type')['Total Impact'])
                        st.caption("Total Impact by Coefficient Type")
                    
                    with col2:
                        st.bar_chart(chart_df.set_index('Coefficient Type')['Affected Sectors'])
                        st.caption("Number of Affected Sectors")
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
                        width='stretch',
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
                        st.metric("Std Dev", f"{impacts_series.std():,.0f}")
                        
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