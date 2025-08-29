#!/usr/bin/env python3
"""
Demonstration of Sector Impact Analyzer

This script shows how to use the tool to analyze supply chain impacts
when sectors reduce their input consumption.
"""

from sector_impact_analyzer import SectorImpactAnalyzer

def demo_basic_usage():
    """Demonstrate basic usage of the analyzer."""
    print("="*80)
    print("SECTOR IMPACT ANALYZER DEMONSTRATION")
    print("="*80)
    print()
    print("This tool analyzes:")
    print("- Economic impacts of sector demand changes")
    print("- Supply chain effects (backward linkages)")
    print("- Employment changes")
    print("- Uses Korean I-O tables at basic prices (기초가격)")
    print("- National-level analysis using basic sectors (기본부문)")
    print()
    
    # Initialize analyzer
    print("Initializing analyzer...")
    analyzer = SectorImpactAnalyzer()
    
    print("\n" + "="*60)
    print("EXAMPLE 1: FINDING RELEVANT SECTORS")
    print("="*60)
    
    # Find steel-related sectors
    steel_sectors = analyzer.io_loader.find_sectors_by_keyword('철강')
    print(f"\nSteel-related sectors found: {len(steel_sectors)}")
    for i, (code, name) in enumerate(steel_sectors[:5]):
        print(f"  {i+1}. {code}: {name}")
    
    # Find coal-related sectors
    coal_sectors = analyzer.io_loader.find_sectors_by_keyword('석탄')
    if not coal_sectors:
        coal_sectors = analyzer.io_loader.find_sectors_by_keyword('연료')
    
    print(f"\nCoal/fuel-related sectors found: {len(coal_sectors)}")
    for i, (code, name) in enumerate(coal_sectors[:5]):
        print(f"  {i+1}. {code}: {name}")
    
    # Find energy-related sectors
    energy_sectors = analyzer.io_loader.find_sectors_by_keyword('전력')
    print(f"\nEnergy-related sectors found: {len(energy_sectors)}")
    for i, (code, name) in enumerate(energy_sectors[:5]):
        print(f"  {i+1}. {code}: {name}")
    
    print("\n" + "="*60)
    print("EXAMPLE 2: SECTOR IMPACT ANALYSIS")
    print("="*60)
    
    # Choose a sector for analysis
    if steel_sectors:
        target_sector = steel_sectors[0][0]  # First steel sector
        print(f"\nAnalyzing impact of 1000 billion won reduction in sector {target_sector}")
        print(f"Sector name: {steel_sectors[0][1]}")
        
        # Run analysis
        results = analyzer.analyze_sector_reduction_impact(
            target_sector=target_sector,
            reduction_amount=1000,
            include_employment=True
        )
        
        # Display results
        analyzer.display_results(results)
    
    print("\n" + "="*60)
    print("EXAMPLE 3: SUPPLY CHAIN STRUCTURE")
    print("="*60)
    
    if steel_sectors:
        target_sector = steel_sectors[0][0]
        print(f"\nSupply chain structure for sector {target_sector}:")
        
        supply_chain_results = analyzer.supply_chain_analyzer.analyze_demand_reduction_impact(
            target_sector, 1000, include_indirect=True
        )
        
        supply_chain_info = supply_chain_results.get('supply_chain_effects', {})
        
        print("\nMajor suppliers:")
        major_suppliers = supply_chain_info.get('major_suppliers', {})
        for i, (supplier, coeff) in enumerate(list(major_suppliers.items())[:5]):
            print(f"  {i+1}. {supplier}: {coeff:.4f}")
        
        print(f"\nSupplier concentration index: {supply_chain_info.get('supplier_concentration', 0):.4f}")
        
        critical_suppliers = supply_chain_info.get('critical_suppliers', [])
        print(f"Critical suppliers: {len(critical_suppliers)}")
    
    print("\n" + "="*60)
    print("HOW TO USE THE INTERACTIVE MODE")
    print("="*60)
    print("To run the interactive analyzer, execute:")
    print("  python sector_impact_analyzer.py")
    print()
    print("Or import and use programmatically:")
    print("  from sector_impact_analyzer import SectorImpactAnalyzer")
    print("  analyzer = SectorImpactAnalyzer()")
    print("  results = analyzer.analyze_sector_reduction_impact('2727', 1000)")
    print()
    print("For steel-coal supply chain analysis:")
    print("  results = analyzer.analyze_steel_coal_supply_chain(1000)")
    print()

if __name__ == "__main__":
    demo_basic_usage()