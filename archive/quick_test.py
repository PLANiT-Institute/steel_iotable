#!/usr/bin/env python3
"""Quick test of fixes without full analysis"""

import sys
import os
sys.path.append('.')

from libs.io_data_loader import IODataLoader
from libs.supply_chain_analyzer import SupplyChainAnalyzer

try:
    print("Loading IO data...")
    loader = IODataLoader('iotable/(표)(2020실측)투입산출표_기초가격_기본부문.xlsx')
    
    print(f"Loaded {len(loader.sector_codes)} sectors")
    print(f"Steel sector 2711: {loader.sector_mapping.get('2711', 'NOT FOUND')}")
    
    print("Initializing supply chain analyzer...")
    analyzer = SupplyChainAnalyzer(loader)
    
    print("Running quick demand reduction test...")
    results = analyzer.analyze_demand_reduction_impact("2711", -1000, "full")
    
    total_impacts = results.get('total_impacts', {})
    print(f"\nQuick Results:")
    print(f"Total impacts: {len(total_impacts)}")
    print(f"Net total: {sum(total_impacts.values()):.2f}")
    
    # Check for accounting totals
    accounting_found = []
    for sector in total_impacts.keys():
        if any(total in sector for total in ['9590', '9519', '9520', '중간투입계', '소계']):
            accounting_found.append(sector)
    
    if accounting_found:
        print(f"WARNING: Found accounting totals: {accounting_found}")
    else:
        print("✓ No accounting totals found")
    
    print(f"Top 5 impacts:")
    sorted_impacts = sorted(total_impacts.items(), key=lambda x: abs(x[1]), reverse=True)
    for i, (sector, impact) in enumerate(sorted_impacts[:5]):
        print(f"  {i+1}. {sector}: {impact:.2f}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()