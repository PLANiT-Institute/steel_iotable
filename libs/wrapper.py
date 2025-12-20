
def get_sector_code(prompt="Enter sector code: "):
    """Helper to convert sector input to proper format."""
    sector_input = input(prompt).strip()
    try:
        sector_int = int(sector_input)
        return f"0{sector_int}" if sector_int < 1000 else str(sector_int)
    except ValueError:
        return sector_input

def handle_list_sectors(analyzer):
    """Option 1: List all sectors."""
    print("\nAvailable sectors:")
    sectors = analyzer.get_sector_options()
    for display in sorted(sectors.values()):
        print(display)

def handle_single_effect(analyzer):
    """Option 2: Analyze single effect."""
    print("\nCoefficient types:")
    print("indirect_prod     - Indirect Production")
    print("indirect_import   - Indirect Import")
    print("value_added       - Value-Added")
    print("jobcoeff          - Job Creation")
    print("directemploycoeff - Direct Employment")

    coeff_type = input("\nSelect type: ").strip()
    valid_types = ['indirect_prod', 'indirect_import', 'value_added', 'jobcoeff', 'directemploycoeff']
    if coeff_type not in valid_types:
        coeff_type = 'indirect_prod'

    sector_code = get_sector_code()
    demand_change = float(input("Enter demand change (million won): ").strip())

    results = analyzer.calculate_direct_effects(sector_code, demand_change, coeff_type)
    analyzer.display_results(results)

def handle_all_effects(analyzer):
    """Option 3: Analyze all effects."""
    sector_code = get_sector_code()
    demand_change = float(input("Enter demand change (million won): ").strip())

    all_results, coefficient_types, _ = analyzer.calculate_all_effects(
        sector_code, demand_change, quiet=False
    )

    for coeff_type in coefficient_types:
        if all_results[coeff_type]:
            analyzer.display_results(all_results[coeff_type])

def handle_aggregate_by_category(analyzer):
    """Option 4: Aggregate by category (code_h)."""
    print("\nCoefficient types:")
    print("indirect_prod     - Indirect Production")
    print("indirect_import   - Indirect Import")
    print("value_added       - Value-Added")

    coeff_type = input("\nSelect type: ").strip()
    valid_types = ['indirect_prod', 'indirect_import', 'value_added']
    if coeff_type not in valid_types:
        coeff_type = 'indirect_prod'

    sector_code = get_sector_code()
    demand_change = float(input("Enter demand change (million won): ").strip())

    results = analyzer.calculate_effects_by_code_h(sector_code, demand_change, coeff_type)
    analyzer.display_code_h_results(results)

def handle_linkages(analyzer):
    """Option 5: Calculate linkages."""
    sector_input = input("Enter sector code (or press Enter for all sectors): ").strip()

    if sector_input:
        sector_code = get_sector_code("") if not sector_input else sector_input
        try:
            sector_int = int(sector_code)
            sector_code = f"0{sector_int}" if sector_int < 1000 else str(sector_int)
        except ValueError:
            pass

        linkages = analyzer.calculate_linkages(sector_code)

        print(f"\n{'='*60}")
        print(f"LINKAGE ANALYSIS")
        print(f"{'='*60}")
        print(f"Sector: {linkages['sector_code']} - {linkages['sector_name']}")
        print(f"\nBackward Linkage: {linkages['backward_linkage']:.4f}")
        print(f"  Normalized: {linkages['backward_normalized']:.4f} ({'Above' if linkages['backward_normalized'] > 1.0 else 'Below'} average)")
        print(f"\nForward Linkage: {linkages['forward_linkage']:.4f}")
        print(f"  Normalized: {linkages['forward_normalized']:.4f} ({'Above' if linkages['forward_normalized'] > 1.0 else 'Below'} average)")
        print(f"\nKey Sector: {'Yes' if linkages['is_key_sector'] else 'No'}")
    else:
        linkages = analyzer.calculate_linkages()

        print(f"\n{'='*60}")
        print(f"LINKAGE ANALYSIS - ALL SECTORS")
        print(f"{'='*60}")
        print(f"Average Backward Linkage: {linkages['avg_backward']:.4f}")
        print(f"Average Forward Linkage: {linkages['avg_forward']:.4f}")

        sorted_sectors = sorted(linkages['sectors'],
                              key=lambda x: x['backward_normalized'] + x['forward_normalized'],
                              reverse=True)

        print(f"\nTop 10 Sectors by Combined Linkage:")
        print(f"{'Code':<6} {'Sector':<30} {'Back':>8} {'Fwd':>8} {'Key':>5}")
        print("-" * 60)
        for sector in sorted_sectors[:10]:
            print(f"{sector['sector_code']:<6} {sector['sector_name']:<30} "
                  f"{sector['backward_normalized']:>8.2f} {sector['forward_normalized']:>8.2f} "
                  f"{'Yes' if sector['is_key_sector'] else 'No':>5}")

def handle_multipliers(analyzer):
    """Option 6: Calculate multipliers."""
    sector_code = get_sector_code()
    multipliers = analyzer.calculate_multipliers(sector_code)

    print(f"\n{'='*60}")
    print(f"MULTIPLIER ANALYSIS")
    print(f"{'='*60}")
    print(f"Sector: {multipliers['sector_code']} - {multipliers['sector_name']}")
    print(f"\nOutput Multiplier: {multipliers['output_multiplier']:.4f}")
    print(f"  {multipliers['interpretation']['output']}")
    print(f"\nValue-Added Multiplier: {multipliers['value_added_multiplier']:.4f}")
    print(f"  {multipliers['interpretation']['value_added']}")
    if multipliers['employment_multiplier']:
        print(f"\nEmployment Multiplier: {multipliers['employment_multiplier']:.4f}")
        print(f"  {multipliers['interpretation']['employment']}")

def handle_compare_sectors(analyzer):
    """Option 7: Compare sectors."""
    print("\nEnter sector codes to compare (comma-separated):")
    sector_inputs = input("Sectors: ").strip().split(',')
    sector_codes = []

    for sector_input in sector_inputs:
        sector_input = sector_input.strip()
        try:
            sector_int = int(sector_input)
            sector_code = f"0{sector_int}" if sector_int < 1000 else str(sector_int)
        except ValueError:
            sector_code = sector_input
        sector_codes.append(sector_code)

    demand_change = float(input("Enter demand change (million won): ").strip())
    coeff_type = input("Coefficient type (default: indirect_prod): ").strip() or 'indirect_prod'

    comparison = analyzer.compare_sectors(sector_codes, demand_change, coeff_type)

    print(f"\n{'='*60}")
    print(f"SECTOR COMPARISON")
    print(f"{'='*60}")
    print(f"Demand Change: {comparison['demand_change']:,.0f} million won")
    print(f"Coefficient Type: {comparison['coeff_type']}")
    print(f"\n{'Rank':<6} {'Code':<6} {'Sector':<30} {'Total Impact':>15}")
    print("-" * 60)

    for i, sector in enumerate(comparison['sectors'], 1):
        if 'error' not in sector:
            print(f"{i:<6} {sector['sector_code']:<6} {sector['sector_name']:<30} "
                  f"{sector['total_impact']:>15,.2f}")

def handle_key_sectors(analyzer):
    """Option 8: Identify key sectors."""
    threshold = input("Enter threshold (default 1.0): ").strip()
    threshold = float(threshold) if threshold else 1.0

    key_sectors_data = analyzer.identify_key_sectors(threshold)

    print(f"\n{'='*60}")
    print(f"KEY SECTOR IDENTIFICATION")
    print(f"{'='*60}")
    print(f"Threshold: {threshold}")
    print(f"\nSummary:")
    print(f"  Key Sectors (high backward & forward): {key_sectors_data['summary']['key_sectors_count']}")
    print(f"  Backward-driven sectors: {key_sectors_data['summary']['backward_only_count']}")
    print(f"  Forward-driven sectors: {key_sectors_data['summary']['forward_only_count']}")
    print(f"  Weak linkage sectors: {key_sectors_data['summary']['weak_linkage_count']}")

    if key_sectors_data['key_sectors']:
        print(f"\nTop 10 Key Sectors:")
        print(f"{'Code':<6} {'Sector':<30} {'Back':>8} {'Fwd':>8}")
        print("-" * 60)
        for sector in key_sectors_data['key_sectors'][:10]:
            print(f"{sector['sector_code']:<6} {sector['sector_name']:<30} "
                  f"{sector['backward_normalized']:>8.2f} {sector['forward_normalized']:>8.2f}")

def handle_sensitivity_analysis(analyzer):
    """Option 9: Sensitivity analysis."""
    sector_code = get_sector_code()

    print("\nEnter demand changes to test (comma-separated):")
    print("Example: 100000,200000,500000,1000000")
    changes_input = input("Values: ").strip().split(',')
    demand_changes = [float(x.strip()) for x in changes_input]

    coeff_type = input("Coefficient type (default: indirect_prod): ").strip() or 'indirect_prod'

    sensitivity = analyzer.sensitivity_analysis(sector_code, demand_changes, coeff_type)

    print(f"\n{'='*60}")
    print(f"SENSITIVITY ANALYSIS")
    print(f"{'='*60}")
    print(f"Sector: {sensitivity['sector_code']} - {sensitivity['sector_name']}")
    print(f"Coefficient Type: {sensitivity['coeff_type']}")
    print(f"\n{'Demand Change':>15} {'Total Impact':>15} {'Impact Ratio':>15}")
    print("-" * 60)

    for scenario in sensitivity['scenarios']:
        print(f"{scenario['demand_change']:>15,.0f} {scenario['total_impact']:>15,.2f} "
              f"{scenario['impact_ratio']:>15.4f}")

def handle_export_results(analyzer):
    """Option 10: Export results to file."""
    print("\nFirst, run an analysis to get results...")

    sector_code = get_sector_code()
    demand_change = float(input("Enter demand change (million won): ").strip())
    coeff_type = input("Coefficient type (default: indirect_prod): ").strip() or 'indirect_prod'

    results = analyzer.calculate_direct_effects(sector_code, demand_change, coeff_type, quiet=True)

    filename = input("Enter output filename (without extension): ").strip()
    format_choice = input("Format (xlsx/csv, default: xlsx): ").strip() or 'xlsx'

    analyzer.export_results(results, filename, format_choice)
    print(f"Exported to {filename}.{format_choice}")