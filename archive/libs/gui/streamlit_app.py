#!/usr/bin/env python3
"""
Steel-Coal I-O Table Analysis Streamlit GUI Application

A comprehensive web-based interface for Korean Input-Output table analysis
focusing on steel-coal supply chain impacts with interactive visualizations
and downloadable reports.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import io
from datetime import datetime
import base64

# Import the analysis modules
import sys
import os
# Add the parent directory (project root) to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from enhanced_sector_analyzer import EnhancedSectorAnalyzer
from config import AnalysisConfig, DEFAULT_CONFIG

# Page configuration
st.set_page_config(
    page_title="Steel-Coal I-O Analysis Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .analysis-section {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_analyzer():
    """Load the enhanced sector analyzer with caching."""
    try:
        return EnhancedSectorAnalyzer()
    except Exception as e:
        st.error(f"Error loading analyzer: {str(e)}")
        return None

@st.cache_data
def get_all_sectors():
    """Get all available sectors from the I-O data."""
    try:
        analyzer = load_analyzer()
        if analyzer is None:
            return {}
        
        # Get sectors from the I-O loader
        sectors = {}
        if hasattr(analyzer.io_loader, 'sector_codes') and analyzer.io_loader.sector_codes:
            print(f"Debug: Loading {len(analyzer.io_loader.sector_codes)} sectors from I-O data")
            for code in analyzer.io_loader.sector_codes[:10]:  # Show first 10 for debugging
                name = analyzer.io_loader.get_sector_name(code)
                print(f"Debug sector: {code}: {name}")
                
            # Load all sectors
            for code in analyzer.io_loader.sector_codes:
                name = analyzer.io_loader.get_sector_name(code)
                sectors[f"{code}: {name}"] = code
                
            # Check for coal sectors specifically
            coal_codes = [code for code in analyzer.io_loader.sector_codes if code.startswith('051')]
            if coal_codes:
                print(f"Debug: Found coal sectors: {coal_codes}")
                for code in coal_codes:
                    name = analyzer.io_loader.get_sector_name(code)
                    print(f"  {code}: {name}")
        else:
            print("Debug: Using fallback sectors - I-O data not loaded properly")
            # Fallback: common sectors
            common_sectors = {
                "0111: 쌀": "0111",
                "2411: 제철업": "2411", 
                "2412: 제강업": "2412",
                "0511: 무연탄": "0511",
                "0512: 유연탄": "0512",
                "1011: 도축업": "1011",
                "1330: 섬유제품 제조업": "1330"
            }
            sectors = common_sectors
            
        return sectors
    except Exception as e:
        st.error(f"Error loading sectors: {str(e)}")
        return {}

def create_impact_chart(impacts_dict, title, chart_type="bar", demand_change=None):
    """Create interactive chart for impact analysis with intelligent sorting."""
    if not impacts_dict:
        return go.Figure().add_annotation(text="No data available", 
                                        xref="paper", yref="paper", 
                                        x=0.5, y=0.5, showarrow=False)
    
    # Filter out accounting totals (not real sectors)
    accounting_totals = ['9590', '9519', '9520', '중간투입계', '소계']
    filtered_impacts = {}
    for sector, impact in impacts_dict.items():
        # Check if sector contains any accounting total codes
        is_accounting_total = False
        for total_code in accounting_totals:
            if total_code in sector:
                is_accounting_total = True
                break
        if not is_accounting_total:
            filtered_impacts[sector] = impact
    
    if not filtered_impacts:
        return go.Figure().add_annotation(text="No sector data available (only totals found)", 
                                        xref="paper", yref="paper", 
                                        x=0.5, y=0.5, showarrow=False)
    
    # Sort impacts based on demand change direction
    if demand_change is not None and demand_change < 0:
        # For negative demand change: show most negative impacts first (ascending order)
        sorted_impacts = sorted(filtered_impacts.items(), key=lambda x: x[1], reverse=False)
        sort_order = 'total ascending'
    else:
        # For positive demand change: show most positive impacts first (descending order)  
        sorted_impacts = sorted(filtered_impacts.items(), key=lambda x: x[1], reverse=True)
        sort_order = 'total descending'
    
    # Prepare data (top 20 for readability)
    sectors = [item[0] for item in sorted_impacts[:20]]
    values = [item[1] for item in sorted_impacts[:20]]
    
    # Clean sector names for display
    clean_sectors = [sector.split(':')[1].strip() if ':' in sector else sector for sector in sectors]
    
    if chart_type == "bar":
        fig = px.bar(
            x=values, 
            y=clean_sectors,
            orientation='h',
            title=title,
            labels={'x': 'Impact (Billion Won)', 'y': 'Sectors'},
            color=values,
            color_continuous_scale='RdYlBu_r'
        )
        fig.update_layout(height=600, yaxis={'categoryorder': sort_order})
    
    elif chart_type == "treemap":
        abs_values = [abs(v) for v in values]
        fig = px.treemap(
            names=clean_sectors,
            values=abs_values,
            title=title
        )
        fig.update_layout(height=600)
    
    return fig

def create_comparison_chart(results):
    """Create comparison chart for different analysis types."""
    supply_analysis = results.get('supply_chain_analysis', {})
    analysis_type = supply_analysis.get('analysis_type', 'full')
    
    # Create data for comparison
    data = []
    
    direct_impacts = supply_analysis.get('direct_impacts', {})
    if direct_impacts:
        total_direct = sum(abs(v) for v in direct_impacts.values())
        data.append({'Type': 'Direct Effects', 'Impact': total_direct})
    
    if analysis_type == 'full':
        indirect_impacts = supply_analysis.get('indirect_impacts', {})
        if indirect_impacts:
            total_indirect = sum(abs(v) for v in indirect_impacts.values())
            data.append({'Type': 'Indirect Effects', 'Impact': total_indirect})
    
    elif analysis_type == 'leontief':
        leontief_impacts = supply_analysis.get('leontief_only_impacts', {})
        if leontief_impacts:
            total_leontief = sum(abs(v) for v in leontief_impacts.values())
            data.append({'Type': 'Leontief Effects', 'Impact': total_leontief})
    
    if data:
        df = pd.DataFrame(data)
        fig = px.pie(df, values='Impact', names='Type', 
                    title='Supply Chain Impact Breakdown')
        return fig
    
    return go.Figure()

def create_employment_chart(employment_results, demand_change=None):
    """Create employment impact visualization with intelligent sorting."""
    sectoral_employment = employment_results.get('sectoral_employment', {})
    
    if not sectoral_employment:
        return go.Figure().add_annotation(text="No employment data available", 
                                        xref="paper", yref="paper", 
                                        x=0.5, y=0.5, showarrow=False)
    
    # Filter out accounting totals (not real sectors)
    accounting_totals = ['9590', '9519', '9520', '중간투입계', '소계']
    filtered_employment = {}
    for sector, employment_change in sectoral_employment.items():
        is_accounting_total = False
        for total_code in accounting_totals:
            if total_code in sector:
                is_accounting_total = True
                break
        if not is_accounting_total:
            filtered_employment[sector] = employment_change
    
    if not filtered_employment:
        return go.Figure().add_annotation(text="No employment data available (after filtering)", 
                                        xref="paper", yref="paper", 
                                        x=0.5, y=0.5, showarrow=False)
    
    # Sort employment impacts based on demand change direction
    if demand_change is not None and demand_change < 0:
        # For negative demand change: show most negative employment impacts first (ascending order)
        sorted_employment = sorted(filtered_employment.items(), key=lambda x: x[1], reverse=False)
        sort_order = 'total ascending'
    else:
        # For positive demand change: show most positive employment impacts first (descending order)
        sorted_employment = sorted(filtered_employment.items(), key=lambda x: x[1], reverse=True)
        sort_order = 'total descending'
    
    # Take top 15 for readability
    sectors = [item[0] for item in sorted_employment[:15]]
    employment_changes = [item[1] for item in sorted_employment[:15]]
    
    colors = ['red' if x < 0 else 'green' for x in employment_changes]
    
    fig = go.Figure(data=[
        go.Bar(x=employment_changes, y=sectors, orientation='h', 
               marker_color=colors, text=[f"{x:.0f}" for x in employment_changes], 
               textposition='auto')
    ])
    
    fig.update_layout(
        title="Employment Impact by Sector",
        xaxis_title="Employment Change (Jobs)",
        yaxis_title="Sectors",
        height=500,
        yaxis={'categoryorder': sort_order}
    )
    
    return fig

def generate_pdf_report(results, analysis_options):
    """Generate PDF report (placeholder for now - would use reportlab)."""
    # For now, return formatted text
    report_content = f"""
    STEEL-COAL I-O ANALYSIS REPORT
    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    ANALYSIS SUMMARY:
    Sector: {results['target_sector']} - {results['target_sector_name']}
    Demand Change: {results['demand_change']:,} billion won
    Analysis Type: {results.get('supply_chain_type', 'full')}
    
    ECONOMIC IMPACTS:
    """
    
    integrated = results.get('integrated_summary', {})
    econ = integrated.get('economic_impact', {})
    
    report_content += f"""
    Total Output Impact: {econ.get('total_output_impact', 0):,.1f} billion won
    GDP Impact: {econ.get('gdp_impact', 0):,.1f} billion won
    Production Multiplier: {econ.get('production_multiplier', 0):.2f}
    """
    
    return report_content

def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<h1 class="main-header">🏭 Steel-Coal I-O Analysis Dashboard</h1>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    **Korean Input-Output Table Analysis System**  
    Comprehensive analysis of economic impacts and employment changes from sector demand changes
    using Korean I-O tables at basic prices (기초가격).
    """)
    
    # Load analyzer
    analyzer = load_analyzer()
    if analyzer is None:
        st.error("Failed to load the analysis system. Please check data files.")
        return
    
    # Sidebar - Analysis Controls
    st.sidebar.header("📊 Analysis Controls")
    
    # Analysis type selection
    analysis_mode = st.sidebar.selectbox(
        "Select Analysis Mode",
        ["Single Sector Analysis", "Steel-Coal Supply Chain", "Sector Comparison"],
        help="Choose the type of analysis to perform"
    )
    
    if analysis_mode == "Single Sector Analysis":
        single_sector_analysis(analyzer)
    elif analysis_mode == "Steel-Coal Supply Chain":
        steel_coal_analysis(analyzer)
    else:
        sector_comparison_analysis(analyzer)

def single_sector_analysis(analyzer):
    """Single sector analysis interface."""
    st.header("🎯 Single Sector Analysis")
    
    # Get all available sectors
    all_sectors = get_all_sectors()
    if not all_sectors:
        st.error("Could not load sector data. Please check your data files.")
        return
    
    # Input controls
    col1, col2 = st.columns(2)
    
    with col1:
        # Sector selection dropdown
        sector_options = list(all_sectors.keys())
        selected_sector_label = st.selectbox(
            "Select Sector",
            sector_options,
            index=0 if sector_options else 0,
            help="Choose a sector from the available I-O data"
        )
        sector_input = all_sectors[selected_sector_label]
        
        demand_change = st.number_input(
            "Demand Change (Billion Won)", 
            value=-1000.0,
            step=100.0,
            help="Enter the change in final demand (negative for reduction)"
        )
    
    with col2:
        # Enhanced analysis type selection
        analysis_type_options = {
            "Direct Effects Only": "direct",
            "Indirect/Leontief Effects Only": "leontief", 
            "Full Effects (Direct + Indirect)": "full"
        }
        
        selected_analysis_label = st.selectbox(
            "Supply Chain Analysis Type",
            list(analysis_type_options.keys()),
            index=2,  # Default to "Full Effects"
            help="Choose the type of supply chain effects to analyze"
        )
        supply_chain_type = analysis_type_options[selected_analysis_label]
        
        analysis_options = st.multiselect(
            "Additional Analysis Options",
            ["Employment Analysis", "Import/Domestic Analysis", "Environmental Analysis"],
            default=["Employment Analysis"],
            help="Select additional analysis components"
        )
    
    # Show analysis description and selected sector
    st.info(f"""
    **Selected Analysis**: {selected_analysis_label}
    **Selected Sector**: {selected_sector_label} (Code: {sector_input})
    
    - **Direct Effects**: Immediate impact on suppliers (first-tier relationships)
    - **Indirect Effects**: Economy-wide ripple effects through Leontief multipliers
    - **Full Effects**: Combined direct and indirect impacts for comprehensive analysis
    """)
    
    # Run Analysis Button
    if st.button("🚀 Run Analysis", type="primary"):
        if not sector_input:
            st.error("Please select a sector")
            return
        
        if demand_change == 0:
            st.error("Please enter a non-zero demand change")
            return
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Run analysis
            status_text.text("Running analysis...")
            progress_bar.progress(25)
            
            options_dict = {
                'supply_chain': True,
                'employment': 'Employment Analysis' in analysis_options,
                'import_domestic': 'Import/Domestic Analysis' in analysis_options,
                'comprehensive': 'Environmental Analysis' in analysis_options,
                'target_region': '전지역'
            }
            
            progress_bar.progress(50)
            
            # Debug info
            print(f"Debug: Running analysis for sector {sector_input} with demand change {demand_change}")
            print(f"Debug: Analysis type: {supply_chain_type}")
            
            results = analyzer.comprehensive_sector_analysis(
                sector_input, 
                demand_change, 
                analysis_options=options_dict,
                supply_chain_type=supply_chain_type
            )
            
            progress_bar.progress(100)
            status_text.text("Analysis complete!")
            
            # Display results
            display_single_sector_results(results, analysis_options)
            
        except Exception as e:
            st.error(f"Analysis error: {str(e)}")
            progress_bar.empty()
            status_text.empty()

def display_single_sector_results(results, analysis_options):
    """Display single sector analysis results."""
    
    # Get demand change for sorting logic
    demand_change = results.get('demand_change', 0)
    
    # Key Metrics
    st.subheader("📈 Key Impact Metrics")
    
    integrated = results.get('integrated_summary', {})
    econ = integrated.get('economic_impact', {})
    emp = integrated.get('employment_impact', {})
    env = integrated.get('environmental_impact', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Output Impact", 
            f"{econ.get('total_output_impact', 0):,.1f}B₩",
            help="Total impact on economic output"
        )
    
    with col2:
        st.metric(
            "Employment Impact", 
            f"{emp.get('total_jobs_affected', 0):,.0f} jobs",
            help="Total employment change"
        )
    
    with col3:
        st.metric(
            "Sectors Affected", 
            f"{econ.get('sectors_affected', 0)}",
            help="Number of sectors with significant impact"
        )
    
    with col4:
        st.metric(
            "CO₂ Impact", 
            f"{env.get('co2_impact_tons', 0):,.0f} tons",
            help="Environmental impact in CO2 equivalent"
        )
    
    # Supply Chain Analysis
    st.subheader("🔗 Supply Chain Analysis")
    
    supply_analysis = results.get('supply_chain_analysis', {})
    total_impacts = supply_analysis.get('total_impacts', {})
    
    if total_impacts:
        col1, col2 = st.columns(2)
        
        with col1:
            # Impact chart
            fig = create_impact_chart(total_impacts, "Supply Chain Impacts", "bar", demand_change)
            st.plotly_chart(fig, width='stretch')
        
        with col2:
            # Comparison pie chart
            fig_pie = create_comparison_chart(results)
            if fig_pie.data:
                st.plotly_chart(fig_pie, width='stretch')
            else:
                st.info("Comparison chart not available for this analysis type")
    
    # Employment Analysis
    if 'Employment Analysis' in analysis_options:
        st.subheader("👥 Employment Analysis")
        
        employment_results = results.get('employment_analysis', {})
        sectoral_employment = employment_results.get('sectoral_employment', {})
        total_employment = employment_results.get('total_employment_change', 0)
        
        if sectoral_employment and len(sectoral_employment) > 0:
            fig_emp = create_employment_chart(employment_results, demand_change)
            st.plotly_chart(fig_emp, width='stretch')
            
            # Show employment summary
            st.info(f"""
            **Employment Analysis Summary:**
            - Total employment change: {total_employment:,.0f} jobs
            - Sectors with employment impact: {len(sectoral_employment)}
            - Analysis region: {employment_results.get('target_region', 'All regions')}
            """)
        else:
            st.warning(f"""
            **No Significant Employment Impacts Found**
            
            This could be due to:
            - Total employment change: {total_employment:,.2f} jobs (very small impact)
            - Employment threshold settings (impacts below {0.1} jobs per sector are filtered out)
            - Data availability issues for employment coefficients
            
            Try:
            - Using a larger demand change value
            - Selecting a different sector with higher employment intensity
            - Using "Full Effects" analysis type for broader impact calculation
            """)
    
    # Data Tables
    st.subheader("📋 Detailed Impact Tables")
    
    # Supply chain impacts table
    if total_impacts:
        # Show all impacts, not just top 20
        df_impacts = pd.DataFrame([
            {'Sector': sector, 'Impact (B₩)': impact, 'Absolute Impact': abs(impact)} 
            for sector, impact in total_impacts.items()
        ])
        
        # Sort by absolute impact for better visibility
        df_impacts = df_impacts.sort_values('Absolute Impact', ascending=False)
        
        # Calculate proper impact statistics
        net_total_impact = df_impacts['Impact (B₩)'].sum()
        total_absolute_impact = df_impacts['Absolute Impact'].sum()
        positive_impacts = df_impacts[df_impacts['Impact (B₩)'] > 0]['Impact (B₩)'].sum()
        negative_impacts = df_impacts[df_impacts['Impact (B₩)'] < 0]['Impact (B₩)'].sum()
        positive_count = len(df_impacts[df_impacts['Impact (B₩)'] > 0])
        negative_count = len(df_impacts[df_impacts['Impact (B₩)'] < 0])
        
        # Show statistics
        st.info(f"""
        **Supply Chain Impact Summary:**
        - Total sectors affected: {len(df_impacts)}
        - **Net total impact**: {net_total_impact:,.2f} billion won
        - Total absolute impact: {total_absolute_impact:,.2f} billion won
        - Positive impacts: {positive_impacts:,.2f} billion won ({positive_count} sectors)
        - Negative impacts: {negative_impacts:,.2f} billion won ({negative_count} sectors)
        - Largest single impact: {df_impacts['Impact (B₩)'].loc[df_impacts['Absolute Impact'].idxmax()]:,.2f} billion won
        - Analysis type: {results.get('supply_chain_type', 'full')}
        """)
        
        # Display table with pagination if many results
        if len(df_impacts) > 50:
            st.write("Showing top 50 impacts (sorted by absolute value):")
            display_df = df_impacts.head(50)
        else:
            display_df = df_impacts
            
        st.dataframe(
            display_df[['Sector', 'Impact (B₩)']].style.format({'Impact (B₩)': '{:,.3f}'}),
            width='stretch',
            hide_index=True
        )
        
        if len(df_impacts) > 50:
            with st.expander(f"View all {len(df_impacts)} sectors"):
                st.dataframe(
                    df_impacts[['Sector', 'Impact (B₩)']].style.format({'Impact (B₩)': '{:,.3f}'}),
                    width='stretch',
                    hide_index=True
                )
    else:
        st.warning("""
        **No Supply Chain Impacts Found**
        
        This could indicate:
        - Analysis configuration issues
        - Data loading problems  
        - Selected sector may not have significant linkages
        
        Please check your data files and try a different sector.
        """)
    
    # Download Reports
    st.subheader("📥 Download Reports")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Excel download
        if st.button("📊 Download Excel Report"):
            try:
                analyzer.display_results_as_tables(results, export_excel=True)
                st.success("Excel report generated! Check your files.")
            except Exception as e:
                st.error(f"Error generating Excel report: {str(e)}")
    
    with col2:
        # CSV download
        if total_impacts:
            csv = df_impacts.to_csv(index=False)
            st.download_button(
                label="📄 Download CSV Data",
                data=csv,
                file_name=f"impact_analysis_{results['target_sector']}.csv",
                mime="text/csv"
            )
    
    with col3:
        # Summary report
        report_text = generate_pdf_report(results, analysis_options)
        st.download_button(
            label="📋 Download Summary",
            data=report_text,
            file_name=f"analysis_summary_{results['target_sector']}.txt",
            mime="text/plain"
        )

def steel_coal_analysis(analyzer):
    """Steel-coal supply chain analysis interface."""
    st.header("⛏️ Steel-Coal Supply Chain Analysis")
    
    # Input controls
    col1, col2 = st.columns(2)
    
    with col1:
        reduction_amount = st.number_input(
            "Coal Reduction Amount (Billion Won)", 
            value=1000.0,
            step=100.0,
            help="Amount of coal demand reduction in steel sector"
        )
        
        max_sectors = st.number_input(
            "Maximum Steel Sectors to Analyze", 
            value=5,
            min_value=1,
            max_value=20,
            help="Limit analysis to top N steel sectors"
        )
    
    with col2:
        export_tables = st.checkbox(
            "Generate Detailed Tables", 
            value=True,
            help="Include detailed I-O tables in results"
        )
        
        chart_type = st.selectbox(
            "Visualization Type",
            ["Bar Chart", "Treemap", "Network Graph"],
            help="Choose how to display the results"
        )
    
    # Run Analysis
    if st.button("🔍 Analyze Steel-Coal Supply Chain", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("Analyzing steel-coal supply chain...")
            progress_bar.progress(30)
            
            results = analyzer.analyze_steel_coal_comprehensive(
                reduction_amount=reduction_amount,
                max_sectors=max_sectors
            )
            
            progress_bar.progress(100)
            status_text.text("Analysis complete!")
            
            # Display results
            display_steel_coal_results(results, chart_type, export_tables, analyzer)
            
        except Exception as e:
            st.error(f"Analysis error: {str(e)}")
            progress_bar.empty()
            status_text.empty()

def display_steel_coal_results(results, chart_type, export_tables, analyzer):
    """Display steel-coal analysis results."""
    
    # Aggregate Impacts
    st.subheader("📊 Aggregate Steel-Coal Impacts")
    
    agg_impacts = results['aggregate_impacts']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Supply Chain Impact", f"{agg_impacts['total_supply_chain_impact']:,.1f}B₩")
        st.metric("Employment Change", f"{agg_impacts['total_employment_change']:,.0f} jobs")
    
    with col2:
        st.metric("Import Impact", f"{agg_impacts['total_import_impact']:,.1f}B₩")
        st.metric("Domestic Impact", f"{agg_impacts['total_domestic_impact']:,.1f}B₩")
    
    with col3:
        st.metric("CO₂ Impact", f"{agg_impacts['total_co2_impact']:,.1f}K tons")
        st.metric("Tax Impact", f"{agg_impacts['total_tax_impact']:,.1f}B₩")
    
    # Coal-Specific Impacts Visualization
    st.subheader("⛏️ Coal-Specific Supply Chain Impacts")
    
    coal_impacts = results.get('coal_specific_impacts', {})
    if coal_impacts:
        # Flatten coal impacts for visualization
        flat_coal_data = []
        for steel_sector, coal_dict in coal_impacts.items():
            for coal_sector, impact in coal_dict.items():
                flat_coal_data.append({
                    'Steel_Sector': steel_sector.split(':')[0],
                    'Coal_Sector': coal_sector.split(':')[1] if ':' in coal_sector else coal_sector,
                    'Impact': abs(impact)
                })
        
        if flat_coal_data:
            df_coal = pd.DataFrame(flat_coal_data)
            
            if chart_type == "Bar Chart":
                fig = px.bar(df_coal, x='Impact', y='Coal_Sector', 
                           color='Steel_Sector', orientation='h',
                           title="Coal Sector Impacts by Steel Sector")
                st.plotly_chart(fig, width='stretch')
            
            elif chart_type == "Treemap":
                fig = px.treemap(df_coal, path=['Steel_Sector', 'Coal_Sector'], 
                               values='Impact', title="Coal Impact Hierarchy")
                st.plotly_chart(fig, width='stretch')
    
    # Detailed Tables
    if export_tables:
        st.subheader("📋 Detailed Analysis Tables")
        
        # Display tables for each steel sector
        sector_analyses = results.get('sector_analyses', {})
        for steel_sector, analysis in list(sector_analyses.items())[:3]:  # Show top 3
            with st.expander(f"📈 {steel_sector}"):
                
                # Supply chain impacts for this sector
                total_impacts = analysis.get('supply_chain_analysis', {}).get('total_impacts', {})
                if total_impacts:
                    df = pd.DataFrame([
                        {'Supplier': sector, 'Impact': impact}
                        for sector, impact in list(total_impacts.items())[:10]
                    ])
                    st.dataframe(df.style.format({'Impact': '{:,.2f}'}))
    
    # Download Options
    st.subheader("📥 Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Generate Excel Report"):
            try:
                analyzer.display_steel_coal_tables(results, export_excel=True)
                st.success("Steel-coal Excel report generated!")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    with col2:
        # Summary data download
        summary_data = {
            'Metric': list(agg_impacts.keys()),
            'Value': list(agg_impacts.values())
        }
        df_summary = pd.DataFrame(summary_data)
        csv = df_summary.to_csv(index=False)
        
        st.download_button(
            "📄 Download Summary CSV",
            data=csv,
            file_name="steel_coal_summary.csv",
            mime="text/csv"
        )

def sector_comparison_analysis(analyzer):
    """Sector comparison analysis interface."""
    st.header("🔄 Sector Comparison Analysis")
    
    # Get all available sectors
    all_sectors = get_all_sectors()
    if not all_sectors:
        st.error("Could not load sector data. Please check your data files.")
        return
    
    # Input controls
    col1, col2 = st.columns(2)
    
    with col1:
        # Sector selection
        sectors_to_compare = st.multiselect(
            "Select Sectors to Compare (2-10 sectors)",
            list(all_sectors.keys()),
            help="Choose multiple sectors for side-by-side comparison",
            max_selections=10
        )
        
        demand_change = st.number_input(
            "Demand Change (Billion Won)", 
            value=-1000.0,
            step=100.0,
            help="Same demand change applied to all selected sectors"
        )
    
    with col2:
        # Analysis options
        analysis_type_options = {
            "Direct Effects Only": "direct",
            "Indirect/Leontief Effects Only": "leontief", 
            "Full Effects (Direct + Indirect)": "full"
        }
        
        selected_analysis_label = st.selectbox(
            "Analysis Type",
            list(analysis_type_options.keys()),
            index=2,
            help="Type of supply chain analysis to perform"
        )
        supply_chain_type = analysis_type_options[selected_analysis_label]
        
        comparison_metric = st.selectbox(
            "Primary Comparison Metric",
            ["Total Output Impact", "Employment Impact", "GDP Impact", "Environmental Impact"],
            help="Main metric for sector comparison"
        )
    
    # Run comparison analysis
    if st.button("🔍 Compare Sectors", type="primary"):
        if len(sectors_to_compare) < 2:
            st.error("Please select at least 2 sectors for comparison")
            return
        
        if demand_change == 0:
            st.error("Please enter a non-zero demand change")
            return
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            comparison_results = {}
            
            for i, sector_label in enumerate(sectors_to_compare):
                sector_code = all_sectors[sector_label]
                status_text.text(f"Analyzing {sector_label}...")
                progress = (i + 1) / len(sectors_to_compare)
                progress_bar.progress(progress)
                
                # Run analysis for each sector
                result = analyzer.comprehensive_sector_analysis(
                    sector_code,
                    demand_change,
                    analysis_options={
                        'supply_chain': True,
                        'employment': True,
                        'import_domestic': True,
                        'comprehensive': True,
                        'target_region': '전지역'
                    },
                    supply_chain_type=supply_chain_type
                )
                
                comparison_results[sector_label] = result
            
            status_text.text("Analysis complete!")
            progress_bar.empty()
            
            # Display comparison results
            display_sector_comparison_results(comparison_results, comparison_metric, selected_analysis_label)
            
        except Exception as e:
            st.error(f"Analysis error: {str(e)}")
            progress_bar.empty()
            status_text.empty()

def display_sector_comparison_results(comparison_results, comparison_metric, analysis_type):
    """Display sector comparison results."""
    
    st.subheader("📊 Sector Comparison Results")
    st.info(f"Comparison based on: **{comparison_metric}** using **{analysis_type}**")
    
    # Create comparison data
    comparison_data = []
    for sector_label, results in comparison_results.items():
        integrated = results.get('integrated_summary', {})
        econ = integrated.get('economic_impact', {})
        emp = integrated.get('employment_impact', {})
        env = integrated.get('environmental_impact', {})
        
        comparison_data.append({
            'Sector': sector_label,
            'Total_Output_Impact': econ.get('total_output_impact', 0),
            'Employment_Impact': emp.get('total_jobs_affected', 0), 
            'GDP_Impact': econ.get('gdp_impact', 0),
            'Environmental_Impact': env.get('co2_impact_tons', 0),
            'Production_Multiplier': econ.get('production_multiplier', 0),
            'Sectors_Affected': econ.get('sectors_affected', 0)
        })
    
    df_comparison = pd.DataFrame(comparison_data)
    
    # Sort by selected metric
    metric_map = {
        "Total Output Impact": "Total_Output_Impact",
        "Employment Impact": "Employment_Impact", 
        "GDP Impact": "GDP_Impact",
        "Environmental Impact": "Environmental_Impact"
    }
    sort_column = metric_map.get(comparison_metric, "Total_Output_Impact")
    df_comparison = df_comparison.sort_values(sort_column, key=abs, ascending=False)
    
    # Display comparison table
    st.subheader("📋 Comparison Summary Table")
    
    # Format the dataframe for display
    display_df = df_comparison.copy()
    display_df['Total Output Impact (B₩)'] = display_df['Total_Output_Impact'].apply(lambda x: f"{x:,.1f}")
    display_df['Employment Impact (Jobs)'] = display_df['Employment_Impact'].apply(lambda x: f"{x:,.0f}")
    display_df['GDP Impact (B₩)'] = display_df['GDP_Impact'].apply(lambda x: f"{x:,.1f}")
    display_df['CO2 Impact (Tons)'] = display_df['Environmental_Impact'].apply(lambda x: f"{x:,.0f}")
    display_df['Production Multiplier'] = display_df['Production_Multiplier'].apply(lambda x: f"{x:.2f}")
    display_df['Sectors Affected'] = display_df['Sectors_Affected']
    
    # Select columns to display
    columns_to_show = ['Sector', 'Total Output Impact (B₩)', 'Employment Impact (Jobs)', 
                       'GDP Impact (B₩)', 'CO2 Impact (Tons)', 'Production Multiplier', 'Sectors Affected']
    
    st.dataframe(
        display_df[columns_to_show],
        width='stretch',
        hide_index=True
    )
    
    # Create comparison visualizations
    st.subheader("📈 Visual Comparisons")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Bar chart for selected metric
        fig_bar = px.bar(
            df_comparison,
            x='Sector',
            y=sort_column,
            title=f"{comparison_metric} by Sector",
            labels={'Sector': 'Sectors', sort_column: comparison_metric},
            color=sort_column,
            color_continuous_scale='viridis'
        )
        fig_bar.update_xaxis(tickangle=45)
        fig_bar.update_layout(height=500)
        st.plotly_chart(fig_bar, width='stretch')
    
    with col2:
        # Radar chart for multiple metrics
        fig_radar = go.Figure()
        
        # Normalize values for radar chart
        metrics = ['Total_Output_Impact', 'Employment_Impact', 'GDP_Impact', 'Environmental_Impact']
        metric_labels = ['Output Impact', 'Employment', 'GDP Impact', 'Environmental']
        
        for _, row in df_comparison.iterrows():
            values = []
            for metric in metrics:
                # Normalize to 0-100 scale
                max_val = df_comparison[metric].abs().max()
                if max_val > 0:
                    normalized = (abs(row[metric]) / max_val) * 100
                else:
                    normalized = 0
                values.append(normalized)
            
            # Close the radar chart
            values.append(values[0])
            labels = metric_labels + [metric_labels[0]]
            
            fig_radar.add_trace(go.Scatterpolar(
                r=values,
                theta=labels,
                fill='toself',
                name=row['Sector'].split(':')[0]  # Show only sector code
            ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            title="Multi-Metric Comparison (Normalized)",
            height=500
        )
        st.plotly_chart(fig_radar, width='stretch')
    
    # Detailed breakdown
    with st.expander("📊 Detailed Sector Breakdown"):
        for sector_label, results in comparison_results.items():
            st.write(f"**{sector_label}**")
            
            # Key metrics for this sector
            integrated = results.get('integrated_summary', {})
            econ = integrated.get('economic_impact', {})
            emp = integrated.get('employment_impact', {})
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Output Impact", f"{econ.get('total_output_impact', 0):,.1f}B₩")
            with col2:
                st.metric("Employment", f"{emp.get('total_jobs_affected', 0):,.0f} jobs")
            with col3:
                st.metric("Multiplier", f"{econ.get('production_multiplier', 0):.2f}")
            
            st.divider()
    
    # Download comparison data
    st.subheader("📥 Download Comparison Results")
    
    csv = df_comparison.to_csv(index=False)
    st.download_button(
        "📄 Download Comparison CSV",
        data=csv,
        file_name=f"sector_comparison_{len(comparison_results)}_sectors.csv",
        mime="text/csv"
    )

# Run the app
if __name__ == "__main__":
    main()