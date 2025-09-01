#!/usr/bin/env python3
"""
Demo version of the Streamlit GUI with mock data
Use this if the full I-O data files are not available
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import random

# Page configuration
st.set_page_config(
    page_title="Steel-Coal I-O Analysis Demo",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .demo-badge {
        background-color: #ff6b6b;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def generate_mock_data(sector_code, demand_change, supply_chain_type):
    """Generate realistic mock data for demonstration."""
    
    # Mock sector names
    sector_names = {
        "2411": "철강 1차 제품 제조업",
        "2412": "철강관 제조업", 
        "2413": "기타 1차 철강 제조업",
        "0511": "무연탄 광업",
        "0512": "유연탄 광업"
    }
    
    # Generate supply chain impacts
    np.random.seed(42)  # For reproducible results
    n_sectors = random.randint(15, 25)
    
    sectors = [f"Sector_{i:04d}: Mock Industry {i}" for i in range(1000, 1000 + n_sectors)]
    base_impacts = np.random.exponential(50, n_sectors) * (demand_change / 1000)
    
    # Add some noise and make some negative
    impacts = base_impacts * np.random.normal(1, 0.3, n_sectors)
    impacts *= np.random.choice([-1, 1], n_sectors, p=[0.3, 0.7])  # 30% negative impacts
    
    supply_chain_impacts = dict(zip(sectors, impacts))
    
    # Employment impacts
    employment_sectors = random.sample(sectors, random.randint(8, 12))
    employment_impacts = {
        sector: impact * random.uniform(0.5, 2.0) * 10  # Convert to jobs
        for sector, impact in supply_chain_impacts.items() 
        if sector in employment_sectors
    }
    
    # Environmental data
    co2_impact = abs(demand_change) * random.uniform(0.3, 0.8)
    
    # Results structure
    results = {
        'target_sector': sector_code,
        'target_sector_name': sector_names.get(sector_code, f"Sector {sector_code}"),
        'demand_change': demand_change,
        'supply_chain_type': supply_chain_type,
        'supply_chain_analysis': {
            'total_impacts': supply_chain_impacts,
            'analysis_type': supply_chain_type
        },
        'employment_analysis': {
            'sectoral_employment': employment_impacts,
            'total_employment_change': sum(employment_impacts.values())
        },
        'integrated_summary': {
            'economic_impact': {
                'total_output_impact': sum(abs(v) for v in supply_chain_impacts.values()),
                'sectors_affected': len([v for v in supply_chain_impacts.values() if abs(v) > 1]),
                'gdp_impact': abs(demand_change) * random.uniform(0.6, 1.2),
                'production_multiplier': random.uniform(1.3, 2.1)
            },
            'employment_impact': {
                'total_jobs_affected': sum(employment_impacts.values()),
                'sectors_with_job_impact': len(employment_impacts)
            },
            'environmental_impact': {
                'co2_impact_tons': co2_impact * 1000,
                'car_equivalent_years': co2_impact * random.uniform(200, 400)
            }
        }
    }
    
    return results

def main():
    """Main demo application."""
    
    # Header with demo badge
    st.markdown('<div class="demo-badge">🧪 DEMO VERSION</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-header">🏭 Steel-Coal I-O Analysis Dashboard</h1>', 
                unsafe_allow_html=True)
    
    st.warning("""
    **Demo Mode**: This is a demonstration version with mock data.  
    The real application uses actual Korean I-O table data for analysis.
    """)
    
    st.markdown("""
    **Korean Input-Output Table Analysis System**  
    Comprehensive analysis of economic impacts and employment changes from sector demand changes.
    """)
    
    # Sidebar
    st.sidebar.header("📊 Analysis Controls")
    st.sidebar.info("Demo version - using mock data")
    
    # Input controls
    col1, col2 = st.columns(2)
    
    with col1:
        sector_code = st.selectbox(
            "Select Sector",
            ["2411", "2412", "2413", "0511", "0512"],
            help="Choose a sector for analysis"
        )
        
        demand_change = st.number_input(
            "Demand Change (Billion Won)", 
            value=-1000.0,
            step=100.0,
            help="Enter the change in final demand"
        )
    
    with col2:
        supply_chain_type = st.selectbox(
            "Supply Chain Analysis Type",
            ["full", "direct", "leontief"],
            help="Choose the type of supply chain effects"
        )
        
        show_charts = st.checkbox("Show Interactive Charts", value=True)
    
    # Analysis button
    if st.button("🚀 Run Demo Analysis", type="primary"):
        
        # Progress simulation
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        import time
        for i in range(100):
            progress_bar.progress(i + 1)
            if i < 30:
                status_text.text("Loading mock data...")
            elif i < 70:
                status_text.text("Running analysis...")
            else:
                status_text.text("Generating results...")
            time.sleep(0.02)
        
        # Generate and display results
        results = generate_mock_data(sector_code, demand_change, supply_chain_type)
        display_results(results, show_charts)
        
        progress_bar.empty()
        status_text.empty()

def display_results(results, show_charts):
    """Display analysis results."""
    
    # Key metrics
    st.subheader("📈 Key Impact Metrics")
    
    integrated = results['integrated_summary']
    econ = integrated['economic_impact']
    emp = integrated['employment_impact']
    env = integrated['environmental_impact']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Output Impact", f"{econ['total_output_impact']:,.1f}B₩")
    
    with col2:
        st.metric("Employment Impact", f"{emp['total_jobs_affected']:,.0f} jobs")
    
    with col3:
        st.metric("Sectors Affected", f"{econ['sectors_affected']}")
    
    with col4:
        st.metric("CO₂ Impact", f"{env['co2_impact_tons']:,.0f} tons")
    
    # Charts
    if show_charts:
        st.subheader("📊 Impact Visualizations")
        
        # Supply chain impacts
        impacts = results['supply_chain_analysis']['total_impacts']
        top_impacts = dict(sorted(impacts.items(), key=lambda x: abs(x[1]), reverse=True)[:15])
        
        sectors = [s.split(':')[1].strip() if ':' in s else s for s in top_impacts.keys()]
        values = list(top_impacts.values())
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_bar = px.bar(
                x=values, 
                y=sectors,
                orientation='h',
                title="Top Supply Chain Impacts",
                labels={'x': 'Impact (Billion Won)', 'y': 'Sectors'},
                color=values,
                color_continuous_scale='RdYlBu_r'
            )
            fig_bar.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            # Employment chart
            emp_data = results['employment_analysis']['sectoral_employment']
            if emp_data:
                emp_sectors = list(emp_data.keys())[:10]
                emp_values = list(emp_data.values())[:10]
                emp_clean = [s.split(':')[1].strip() if ':' in s else s for s in emp_sectors]
                
                colors = ['red' if x < 0 else 'green' for x in emp_values]
                
                fig_emp = go.Figure(data=[
                    go.Bar(x=emp_values, y=emp_clean, orientation='h', 
                           marker_color=colors, text=[f"{v:.0f}" for v in emp_values], 
                           textposition='auto')
                ])
                
                fig_emp.update_layout(
                    title="Employment Impact by Sector",
                    xaxis_title="Employment Change (Jobs)",
                    yaxis_title="Sectors",
                    height=500,
                    yaxis={'categoryorder': 'total ascending'}
                )
                st.plotly_chart(fig_emp, use_container_width=True)
    
    # Data table
    st.subheader("📋 Detailed Impact Data")
    
    impacts = results['supply_chain_analysis']['total_impacts']
    df = pd.DataFrame([
        {
            'Rank': i+1,
            'Sector': sector.split(':')[1].strip() if ':' in sector else sector,
            'Impact (B₩)': impact,
            'Absolute Impact': abs(impact)
        }
        for i, (sector, impact) in enumerate(
            sorted(impacts.items(), key=lambda x: abs(x[1]), reverse=True)[:20]
        )
    ])
    
    st.dataframe(
        df[['Rank', 'Sector', 'Impact (B₩)']].style.format({'Impact (B₩)': '{:,.2f}'}),
        use_container_width=True,
        hide_index=True
    )
    
    # Download section
    st.subheader("📥 Download Demo Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv_data = df.to_csv(index=False)
        st.download_button(
            "📄 Download CSV",
            data=csv_data,
            file_name="demo_analysis_results.csv",
            mime="text/csv"
        )
    
    with col2:
        summary = f"""
Demo Analysis Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Sector: {results['target_sector']} - {results['target_sector_name']}
Demand Change: {results['demand_change']:,} billion won
Analysis Type: {results['supply_chain_type']}

Total Output Impact: {econ['total_output_impact']:,.1f} billion won
Employment Impact: {emp['total_jobs_affected']:,.0f} jobs
Environmental Impact: {env['co2_impact_tons']:,.0f} tons CO2

Note: This is demo data for illustration purposes.
        """
        
        st.download_button(
            "📋 Download Summary",
            data=summary,
            file_name="demo_summary.txt",
            mime="text/plain"
        )

if __name__ == "__main__":
    main()