#!/usr/bin/env python3
"""
Enhanced Sector Impact Analyzer Demo

This demo showcases all the comprehensive analysis capabilities:
1. Import vs Domestic impact separation
2. Value-added and production multipliers
3. Environmental impact estimates (CO2)
4. Fiscal impact analysis (tax effects)
5. Regional spillover effects
6. Steel-coal supply chain comprehensive analysis
"""

from enhanced_sector_analyzer import EnhancedSectorAnalyzer

def demo_enhanced_capabilities():
    """Demonstrate all enhanced capabilities of the analyzer."""
    print("=" * 100)
    print("ENHANCED SECTOR IMPACT ANALYZER - COMPREHENSIVE DEMO")
    print("=" * 100)
    print()
    print("NEW CAPABILITIES DEMONSTRATED:")
    print("✓ Import vs Domestic impact separation (using Am and Ad matrices)")
    print("✓ Value-added impact analysis (GDP effects)")
    print("✓ Production multiplier analysis")
    print("✓ Environmental impact estimates (CO2 emissions)")
    print("✓ Fiscal impact analysis (tax revenue effects)")
    print("✓ Regional spillover effects")
    print("✓ Comprehensive steel-coal supply chain analysis")
    print()
    
    # Initialize analyzer
    print("Initializing Enhanced Analyzer...")
    analyzer = EnhancedSectorAnalyzer()
    
    print("\n" + "=" * 80)
    print("DEMO 1: COMPREHENSIVE SINGLE SECTOR ANALYSIS")
    print("=" * 80)
    
    # Find a steel sector for demonstration
    steel_sectors = analyzer.io_loader.find_sectors_by_keyword('철강')
    if not steel_sectors:
        steel_sectors = analyzer.io_loader.find_sectors_by_keyword('27')  # Steel industry codes
    
    if steel_sectors:
        demo_sector = steel_sectors[0][0]
        demo_sector_name = steel_sectors[0][1]
        print(f"Analyzing sector: {demo_sector} - {demo_sector_name}")
        print(f"Scenario: 1000 billion won reduction in steel sector demand")
        
        # Run comprehensive analysis
        results = analyzer.comprehensive_sector_analysis(
            target_sector=demo_sector,
            demand_change=-1000  # 1000 billion won reduction
        )
        
        # Display comprehensive results
        analyzer.display_comprehensive_results(results)
        
        print("\n" + "=" * 80)
        print("DEMO 2: IMPORT vs DOMESTIC IMPACT SEPARATION")
        print("=" * 80)
        
        # Demonstrate import/domestic separation
        if analyzer.import_domestic_analyzer.is_data_available():
            import_domestic_results = analyzer.import_domestic_analyzer.analyze_import_domestic_impacts(
                demo_sector, -1000
            )
            
            print(f"Target Sector: {demo_sector}")
            print(f"Demand Reduction: 1000 billion won")
            print()
            print("SEPARATE IMPORT AND DOMESTIC IMPACTS:")
            print("-" * 50)
            print(f"Total Import Impact: {import_domestic_results.get('total_import_effect', 0):,.1f} billion won")
            print(f"Total Domestic Impact: {import_domestic_results.get('total_domestic_effect', 0):,.1f} billion won")
            print(f"Import Dependency: {import_domestic_results.get('import_share', 0):.1%}")
            print(f"Domestic Dependency: {import_domestic_results.get('domestic_share', 0):.1%}")
            print(f"Import Multiplier: {import_domestic_results.get('import_multiplier', 0):.2f}")
            print(f"Domestic Multiplier: {import_domestic_results.get('domestic_multiplier', 0):.2f}")
            
            print("\nTOP IMPORT IMPACTS:")
            import_impacts = import_domestic_results.get('import_impacts', {})
            sorted_imports = sorted(import_impacts.items(), key=lambda x: abs(x[1]), reverse=True)
            for i, (sector, impact) in enumerate(sorted_imports[:5]):
                print(f"  {i+1}. {sector[:50]}: {impact:.1f} billion won")
            
            print("\nTOP DOMESTIC IMPACTS:")
            domestic_impacts = import_domestic_results.get('domestic_impacts', {})
            sorted_domestic = sorted(domestic_impacts.items(), key=lambda x: abs(x[1]), reverse=True)
            for i, (sector, impact) in enumerate(sorted_domestic[:5]):
                print(f"  {i+1}. {sector[:50]}: {impact:.1f} billion won")
        
        print("\n" + "=" * 80)
        print("DEMO 3: ENVIRONMENTAL AND FISCAL IMPACTS")
        print("=" * 80)
        
        # Environmental and fiscal analysis
        if analyzer.comprehensive_analyzer.is_data_available():
            comp_results = analyzer.comprehensive_analyzer.comprehensive_analysis(
                demo_sector, -1000
            )
            
            # Environmental impacts
            env_analysis = comp_results.get('environmental_analysis', {})
            env_summary = env_analysis.get('environmental_summary', {})
            
            print("ENVIRONMENTAL IMPACT ESTIMATES:")
            print("-" * 40)
            print(f"Total CO2 Impact: {env_summary.get('total_co2_thousand_tons', 0):,.1f} thousand tons")
            print(f"Equivalent to: {env_summary.get('equivalent_car_years', 0):,.0f} car-years of emissions")
            print(f"High-carbon sectors affected: {env_summary.get('high_impact_sectors', 0)}")
            
            # Fiscal impacts
            fiscal_analysis = comp_results.get('fiscal_analysis', {})
            
            print("\nFISCAL IMPACT ESTIMATES:")
            print("-" * 40)
            print(f"Total Tax Revenue Impact: {fiscal_analysis.get('total_tax_impact', 0):,.1f} billion won")
            print(f"Income Tax Impact: {fiscal_analysis.get('income_tax_impact', 0):,.1f} billion won")
            print(f"Corporate Tax Impact: {fiscal_analysis.get('corporate_tax_impact', 0):,.1f} billion won")
            print(f"Indirect Tax Impact: {fiscal_analysis.get('indirect_tax_impact', 0):,.1f} billion won")
            
            # Regional spillovers
            regional_analysis = comp_results.get('regional_analysis', {})
            
            print("\nREGIONAL SPILLOVER EFFECTS:")
            print("-" * 40)
            print(f"Geographic Concentration Index: {regional_analysis.get('concentration_index', 0):.2f}")
            print(f"Spillover Potential: {regional_analysis.get('spillover_potential', 'N/A')}")
            
            regional_effects = regional_analysis.get('regional_effects', {})
            print("Regional Distribution:")
            for region, impact in regional_effects.items():
                print(f"  {region}: {impact:,.1f} billion won")
    
    print("\n" + "=" * 80)
    print("DEMO 4: STEEL-COAL COMPREHENSIVE SUPPLY CHAIN ANALYSIS")
    print("=" * 80)
    
    # Comprehensive steel-coal analysis
    print("Analyzing comprehensive impacts when steel sector reduces coal consumption...")
    print("Scenario: Steel sector reduces coal inputs by 500 billion won")
    
    steel_coal_results = analyzer.analyze_steel_coal_comprehensive(500)
    
    # Display aggregate impacts
    print("\nAGGREGATE SUPPLY CHAIN IMPACTS:")
    print("-" * 50)
    agg_impacts = steel_coal_results['aggregate_impacts']
    
    print(f"Total Supply Chain Impact: {agg_impacts['total_supply_chain_impact']:,.1f} billion won")
    print(f"Total Employment Change: {agg_impacts['total_employment_change']:,.0f} jobs")
    print(f"Total Import Impact: {agg_impacts['total_import_impact']:,.1f} billion won")
    print(f"Total Domestic Impact: {agg_impacts['total_domestic_impact']:,.1f} billion won")
    print(f"Total CO2 Impact: {agg_impacts['total_co2_impact']:,.1f} thousand tons")
    print(f"Total Tax Impact: {agg_impacts['total_tax_impact']:,.1f} billion won")
    
    # Show coal-specific impacts
    print("\nCOAL-SPECIFIC SUPPLY CHAIN IMPACTS:")
    print("-" * 50)
    coal_specific = steel_coal_results['coal_specific_impacts']
    
    for steel_sector, coal_impacts in coal_specific.items():
        if coal_impacts:
            print(f"\n{steel_sector}:")
            for coal_sector, impact in coal_impacts.items():
                print(f"  {coal_sector}: {impact:.1f} billion won")
        else:
            print(f"\n{steel_sector}: No direct coal sector impacts identified")
    
    print("\n" + "=" * 80)
    print("ANALYSIS INTERPRETATION")
    print("=" * 80)
    
    print("""
WHAT THIS ANALYSIS TELLS US:

1. SUPPLY CHAIN EFFECTS:
   - Shows which sectors are affected when steel reduces coal consumption
   - Includes coal mining, transportation, storage, and related services
   - Quantifies both direct and indirect impacts through I-O linkages

2. IMPORT vs DOMESTIC SEPARATION:
   - Distinguishes between impacts on imported vs domestically produced goods
   - Helps understand trade balance implications
   - Shows import dependency levels for different supply chain components

3. EMPLOYMENT IMPACTS:
   - Calculates job losses in affected sectors
   - Maps from basic sectors to employment categories
   - Provides regional employment analysis

4. ENVIRONMENTAL IMPLICATIONS:
   - Estimates CO2 emission reductions from reduced coal use
   - Accounts for indirect environmental effects in supply chain
   - Quantifies environmental benefits in concrete terms

5. FISCAL EFFECTS:
   - Calculates impact on government tax revenues
   - Separates income, corporate, and indirect tax effects
   - Shows fiscal implications of industrial transitions

6. REGIONAL DISTRIBUTION:
   - Estimates which regions are most affected
   - Considers industrial concentration patterns
   - Helps plan regional economic adjustment policies

POLICY IMPLICATIONS:
- Quantifies economic costs of coal reduction in steel sector
- Identifies sectors needing support during energy transition
- Provides basis for designing compensation mechanisms
- Shows trade-offs between environmental and economic goals
    """)
    
    print("\n" + "=" * 80)
    print("HOW TO USE THE ENHANCED ANALYZER")
    print("=" * 80)
    
    print("""
INTERACTIVE MODE:
Run: python enhanced_sector_analyzer.py

OPTIONS AVAILABLE:
1. Comprehensive sector analysis - Full analysis for any sector
2. Steel-coal supply chain - Specific steel-coal transition analysis  
3. Import vs Domestic comparison - Trade impact focus
4. Environmental impact analysis - CO2 and environmental focus
5. Search sectors - Find relevant sectors to analyze

PROGRAMMATIC USE:
from enhanced_sector_analyzer import EnhancedSectorAnalyzer
analyzer = EnhancedSectorAnalyzer()

# Comprehensive analysis
results = analyzer.comprehensive_sector_analysis('2711', -1000)

# Steel-coal specific
steel_coal = analyzer.analyze_steel_coal_comprehensive(500)

# Import/domestic only
import_domestic = analyzer.import_domestic_analyzer.analyze_import_domestic_impacts('2711', -1000)
    """)

if __name__ == "__main__":
    demo_enhanced_capabilities()