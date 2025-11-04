"""
Optimized Streamlit GUI for Hydrogen-reduced Steel Input-Output Analysis
Streamlined code with reduced duplication and better organization
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from libs.io_analyzer import IOTableAnalyzer
from libs.hydrogen_analyzer import HydrogenTableAnalyzer
from libs.scenario_analyzer import ScenarioAnalyzer

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

TARGET_YEARS = [2026, 2030, 2040, 2050]

EFFECT_TYPE_LABELS = {
    'indirect_prod': '💰 Indirect Production',
    'indirect_import': '🌐 Indirect Import',
    'value_added': '💎 Value Added',
    'jobcoeff': '👥 Job Creation',
    'directemploycoeff': '👔 Direct Employment',
    'productioncoeff': '⚡ Production Coeff (H2)',
    'valueaddedcoeff': '💎 Value Added Coeff (H2)'
}

IO_EFFECTS = ['indirect_prod', 'indirect_import', 'value_added', 'jobcoeff', 'directemploycoeff']
H2_EFFECTS = ['productioncoeff', 'valueaddedcoeff', 'jobcoeff', 'directemploycoeff']

st.set_page_config(
    page_title="Hydrogen-reduced steel Input-Output Analysis",
    page_icon="🏭",
    layout="wide"
)

# ============================================================================
# CACHED DATA LOADERS
# ============================================================================

@st.cache_data
def load_analyzer():
    """Load the IO analyzer with caching."""
    return IOTableAnalyzer()

@st.cache_data
def load_hydrogen_analyzer():
    """Load the hydrogen analyzer with caching."""
    return HydrogenTableAnalyzer()

@st.cache_data
def load_scenario_analyzer():
    """Load the scenario analyzer with caching."""
    return ScenarioAnalyzer()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_scenario_results():
    """Check if scenario analysis has been run and return analyzer."""
    if not st.session_state.get('scenario_results') or not st.session_state.get('scenario_analyzer'):
        st.warning("⚠️ No scenario analysis results available. Please run scenario analysis first.")
        st.info("👈 Go to the 'Run Analysis' tab to generate data.")
        return None, None
    return st.session_state.scenario_analyzer, st.session_state.scenario_results

def get_scenario_files():
    """Get all scenario files from data folder."""
    data_folder = Path("data")
    return sorted([f for f in data_folder.glob("scenarios_*.xlsx")])

def format_effect_label(effect_type):
    """Format effect type for display."""
    return EFFECT_TYPE_LABELS.get(effect_type, effect_type)

def create_summary_dataframe(results, effect_types, years):
    """Create consolidated summary dataframe for given effect types and years."""
    summary_data = []
    for year in years:
        row = {'Year': year}
        for effect in effect_types:
            if effect in results and year in results[effect]:
                row[format_effect_label(effect)] = f"{results[effect][year]['total_aggregate_impact']:,.0f}"
            else:
                row[format_effect_label(effect)] = 'N/A'
        summary_data.append(row)
    return pd.DataFrame(summary_data)

def create_sector_impact_table(results, effect_types, years, top_n=20):
    """Create sector impact table across years for given effect types."""
    all_sectors = set()
    for effect in effect_types:
        if effect in results:
            for year in years:
                if year in results[effect]:
                    for impact in results[effect][year]['sector_impacts']:
                        all_sectors.add(str(impact['sector_code']))
    
    if not all_sectors:
        return None
    
    sector_matrix = []
    for sector_code in sorted(all_sectors):
        row = {'Sector Code': sector_code, 'Sector Name': ''}
        
        for year in years:
            total_impact = 0
            sector_name = ''
            
            for effect in effect_types:
                if effect in results and year in results[effect]:
                    for impact in results[effect][year]['sector_impacts']:
                        if str(impact['sector_code']) == sector_code:
                            total_impact += impact['total_impact']
                            if not sector_name:
                                sector_name = impact['sector_name']
            
            row[str(year)] = total_impact
            if not row['Sector Name']:
                row['Sector Name'] = sector_name
        
        sector_matrix.append(row)
    
    df = pd.DataFrame(sector_matrix)
    year_cols = [str(y) for y in years]
    df['total'] = df[year_cols].sum(axis=1)
    df = df.sort_values('total', ascending=False).head(top_n)
    return df.drop(columns=['total'])

# ============================================================================
# MAIN PAGE FUNCTIONS
# ============================================================================

def show_scenarios():
    """Display scenario file selection and preview."""
    st.title("🎯 Scenarios")
    st.markdown("---")
    
    scenario_files = get_scenario_files()
    if not scenario_files:
        st.warning("No scenario files found in the 'data' directory.")
        return
    
    st.info(f"Found {len(scenario_files)} scenario files in the data folder.")
    
    # File selector and preview
    selected_file = st.selectbox(
        "Select a scenario file to preview",
        [f.name for f in scenario_files]
    )
    
    if st.checkbox("Preview selected scenario file"):
        try:
            df = pd.read_excel(Path("data") / selected_file)
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to load scenario file: {e}")

def run_scenario_analysis():
    """Run scenario analysis and store results in session state."""
    st.title("🚀 Run Scenario Analysis")
    st.markdown("---")
    
    scenario_files = get_scenario_files()
    if not scenario_files:
        st.error("No scenario files found in the 'data' directory.")
        return
    
    selected_file = st.selectbox(
        "Select a scenario file to analyze",
        [f.name for f in scenario_files],
        key="scenario_file_selector"
    )
    
    if st.button("🚀 Run Complete Analysis", type="primary"):
        with st.spinner("Running comprehensive scenario analysis..."):
            try:
                analyzer = ScenarioAnalyzer()
                analyzer.run_all_scenarios()
                
                st.session_state.scenario_analyzer = analyzer
                st.session_state.scenario_results = analyzer.aggregated_results
                
                st.success("✅ Analysis complete! Navigate to other tabs to view results.")
                
                # Show summary
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Effect Types Analyzed", len(analyzer.aggregated_results))
                with col2:
                    years = list(next(iter(analyzer.aggregated_results.values())).keys()) if analyzer.aggregated_results else []
                    st.metric("Years Covered", len(years))
                with col3:
                    st.metric("Status", "Ready ✓")
                    
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                st.exception(e)

def show_integrated_tables():
    """Display integrated analysis tables."""
    st.subheader("🔗 Integrated Table Analysis")
    
    analyzer, results = check_scenario_results()
    if not analyzer:
        return
    
    st.markdown("### 📊 Summary Tables by Effect Type")
    
    available_effects = [effect for effect in results.keys() if results[effect]]
    if not available_effects:
        st.error("No effect types available in results.")
        return
    
    # Create tabs for each effect type
    tab_names = [format_effect_label(effect) for effect in available_effects]
    effect_tabs = st.tabs(tab_names)
    
    for i, effect_type in enumerate(available_effects):
        with effect_tabs[i]:
            st.subheader(f"{format_effect_label(effect_type)}")
            
            # Summary by year
            st.markdown("#### 📊 Summary by Year")
            summary_df = create_summary_dataframe(results, [effect_type], TARGET_YEARS)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
            # Download button
            csv = summary_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label=f"📥 Download Summary",
                data=csv,
                file_name=f"integrated_summary_{effect_type}.csv",
                mime="text/csv",
                key=f"download_summary_{effect_type}"
            )
            
            # Sector impact matrix
            st.markdown("#### 🎯 Sector Impacts by Year")
            sector_df = create_sector_impact_table(results, [effect_type], TARGET_YEARS, top_n=20)
            
            if sector_df is not None:
                st.dataframe(sector_df, use_container_width=True, hide_index=True, height=400)
                
                csv_detailed = sector_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label=f"📥 Download Detailed Data",
                    data=csv_detailed,
                    file_name=f"integrated_sectors_{effect_type}.csv",
                    mime="text/csv",
                    key=f"download_detailed_{effect_type}"
                )

def show_total_tables():
    """Display total/summary tables."""
    st.subheader("📊 Total Tables Summary")
    
    analyzer, results = check_scenario_results()
    if not analyzer:
        return
    
    st.markdown("### Consolidated Impact Summary")
    
    # Summary table for all effect types
    all_effects = [e for e in results.keys() if results[e]]
    if all_effects:
        summary_df = create_summary_dataframe(results, all_effects, TARGET_YEARS)
        st.dataframe(summary_df, use_container_width=True)
        
        # Download
        csv = summary_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            "📥 Download Complete Summary",
            csv,
            "total_summary.csv",
            "text/csv"
        )

def show_individual_tables():
    """Display individual sector analysis."""
    st.subheader("👤 Individual Sector Analysis")
    st.info("Select specific sectors for detailed analysis.")
    
    analyzer, results = check_scenario_results()
    if not analyzer:
        return
    
    # Sector selector
    all_sectors = set()
    for effect in results.values():
        for year_data in effect.values():
            for impact in year_data['sector_impacts']:
                all_sectors.add((impact['sector_code'], impact['sector_name']))
    
    if all_sectors:
        sector_options = {f"{code}: {name}": code for code, name in sorted(all_sectors)}
        selected_sector = st.selectbox("Select Sector", list(sector_options.keys()))
        
        st.markdown(f"### Analysis for {selected_sector}")
        st.info("Individual sector detailed analysis coming soon...")

def show_io_analysis():
    """Display IO table analysis results."""
    st.subheader("🏭 IO Table Analysis")
    
    analyzer, results = check_scenario_results()
    if not analyzer:
        return
    
    available_io_effects = [e for e in IO_EFFECTS if e in results and results[e]]
    
    if not available_io_effects:
        st.warning("No IO table analysis results available.")
        return
    
    # Summary table
    st.markdown("### 📋 Summary Tables")
    summary_df = create_summary_dataframe(results, available_io_effects, TARGET_YEARS)
    st.dataframe(summary_df, use_container_width=True)
    
    # Full table
    st.markdown("### 📊 Full Table (All Years)")
    sector_df = create_sector_impact_table(results, available_io_effects, TARGET_YEARS, top_n=50)
    if sector_df is not None:
        st.dataframe(sector_df, use_container_width=True, height=600)

def show_hydrogen_analysis():
    """Display hydrogen table analysis results."""
    st.subheader("⚡ Hydrogen Table Analysis")
    
    analyzer, results = check_scenario_results()
    if not analyzer:
        return
    
    available_h2_effects = [e for e in H2_EFFECTS if e in results and results[e]]
    
    if not available_h2_effects:
        st.warning("No hydrogen table analysis results available.")
        return
    
    # Summary table
    st.markdown("### 📋 Summary Tables")
    summary_df = create_summary_dataframe(results, available_h2_effects, TARGET_YEARS)
    st.dataframe(summary_df, use_container_width=True)
    
    # Full table
    st.markdown("### 📊 Full Table (All Years)")
    sector_df = create_sector_impact_table(results, available_h2_effects, TARGET_YEARS, top_n=50)
    if sector_df is not None:
        st.dataframe(sector_df, use_container_width=True, height=600)

def show_summary_visualizations():
    """Display summary visualizations and charts."""
    st.title("📊 Summary Visualizations")
    
    analyzer, results = check_scenario_results()
    if not analyzer:
        return
    
    try:
        from libs.visualisation import Visualization
        viz = Visualization(analyzer)
    except Exception as e:
        st.error(f"Error loading visualization module: {e}")
        return
    
    # Create tabs
    viz_tabs = st.tabs(["📈 Yearly Trends", "🗺️ Sector Maps", "🔥 Code_H Heatmap"])
    
    # TAB 1: Yearly Trends
    with viz_tabs[0]:
        show_yearly_trends(viz)
    
    # TAB 2: Sector Maps
    with viz_tabs[1]:
        show_sector_maps(viz)
    
    # TAB 3: Heatmap
    with viz_tabs[2]:
        show_code_h_heatmap(viz, analyzer)

def show_yearly_trends(viz):
    """Display yearly trends visualizations."""
    st.markdown("### 📈 Yearly Trends")
    
    trend_type = st.radio("Select Table Type", ["IO Table", "Hydrogen Table"], horizontal=True)
    
    if trend_type == "IO Table":
        effect = st.selectbox("Effect Type", IO_EFFECTS, format_func=format_effect_label, key="io_trend")
        scenarios = st.multiselect("Scenarios", ['1610', '4506', '1610&4506'], default=['1610&4506'], key="io_scenarios")
        
        if st.button("Generate", key="btn_io_trend"):
            try:
                fig = viz.create_io_yearly_trends(effect, scenarios=scenarios, show_fig=False)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        effect = st.selectbox("Effect Type", H2_EFFECTS, format_func=format_effect_label, key="h2_trend")
        scenarios = st.multiselect("Scenarios", ['H2S', 'H2T', 'H2S&H2T'], default=['H2S&H2T'], key="h2_scenarios")
        
        if st.button("Generate", key="btn_h2_trend"):
            try:
                fig = viz.create_hydrogen_yearly_trends(effect, scenarios=scenarios, show_fig=False)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error: {e}")

def show_sector_maps(viz):
    """Display sector maps visualizations."""
    st.markdown("### 🗺️ Top Sectors Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        scenario = st.selectbox("Scenario", 
            ['1610', '4506', '1610&4506', 'H2S', 'H2T', 'H2S&H2T'],
            key="sector_scenario")
    
    with col2:
        year = st.selectbox("Year", TARGET_YEARS, index=3, key="sector_year")
    
    with col3:
        effect_list = H2_EFFECTS if 'H2' in scenario else IO_EFFECTS
        effect = st.selectbox("Effect", effect_list, format_func=format_effect_label, key="sector_effect")
    
    if st.button("Generate Top 10", key="btn_top10"):
        try:
            fig = viz.plot_top_10_sectors(scenario, effect, year, show_fig=False)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No data available.")
        except Exception as e:
            st.error(f"Error: {e}")

def show_code_h_heatmap(viz, analyzer):
    """Display Code_H heatmap visualization."""
    st.markdown("### 🔥 Code_H Sector Heatmap")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        effect = st.selectbox("Effect Type", 
            list(EFFECT_TYPE_LABELS.keys()),
            format_func=format_effect_label,
            key="heatmap_effect")
    
    with col2:
        year = st.selectbox("Year", TARGET_YEARS, index=1, key="heatmap_year")
    
    with col3:
        top_n = st.slider("Top N per Category", 5, 20, 10, 5, key="heatmap_topn")
    
    if st.button("🎨 Generate Heatmap", type="primary", key="btn_heatmap"):
        with st.spinner("Creating heatmap..."):
            try:
                if effect not in analyzer.aggregated_results:
                    st.error(f"No data for: {effect}")
                elif year not in analyzer.aggregated_results[effect]:
                    st.error(f"No data for year: {year}")
                else:
                    fig = viz.create_code_h_heatmap(
                        effect_type=effect,
                        year=year,
                        top_n=top_n,
                        use_plotly=True,
                        show_fig=False
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.success("✅ Heatmap generated!")
                    
                    with st.expander("ℹ️ How to read"):
                        st.markdown("""
                        - **X-axis**: Product categories
                        - **Y-axis**: Rank (#1 = highest impact)
                        - **Colors**: 🔴 Red = positive, 🔵 Blue = negative
                        - **Ranking**: By absolute values (magnitude)
                        - **Hover**: See full details
                        """)
            except Exception as e:
                st.error(f"Error: {e}")

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point."""
    # Auto-run scenario analysis on startup if not done
    if 'startup_analysis_done' not in st.session_state:
        st.session_state.startup_analysis_done = False
    
    if not st.session_state.startup_analysis_done:
        scenario_files = get_scenario_files()
        if scenario_files:
            with st.spinner("Running initial scenario analysis..."):
                try:
                    analyzer = ScenarioAnalyzer()
                    analyzer.run_all_scenarios()
                    st.session_state.scenario_analyzer = analyzer
                    st.session_state.scenario_results = analyzer.aggregated_results
                    st.session_state.startup_analysis_done = True
                except:
                    pass
    
    # Sidebar navigation
    st.sidebar.title("🏭 IO Analysis")
    main_option = st.sidebar.radio(
        "Main Menu",
        ["Scenarios", "Tables", "Visualisation"],
        index=1
    )
    
    # Route to appropriate page
    if main_option == "Scenarios":
        show_scenarios()
    elif main_option == "Tables":
        st.title("📊 Analysis Results")
        tabs = st.tabs(["🚀 Run Analysis", "🔗 Integrated", "⚡ H2", "📊 Total", "🏭 IO Tables", "👤 Individual"])
        
        with tabs[0]:
            run_scenario_analysis()
        with tabs[1]:
            show_integrated_tables()
        with tabs[2]:
            show_hydrogen_analysis()
        with tabs[3]:
            show_total_tables()
        with tabs[4]:
            show_io_analysis()
        with tabs[5]:
            show_individual_tables()
    else:
        show_summary_visualizations()

if __name__ == "__main__":
    main()

