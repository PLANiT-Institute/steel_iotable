#!/usr/bin/env python3
"""
IO Table Format Output Demo

This demo shows how to display analysis results in Input-Output table format,
similar to traditional IO tables with sectors in rows and impacts in columns.
"""

from enhanced_sector_analyzer import EnhancedSectorAnalyzer

def demo_io_table_output():
    """Demonstrate IO table format output capabilities."""
    print("=" * 100)
    print("IO TABLE FORMAT OUTPUT DEMONSTRATION")
    print("=" * 100)
    print()
    print("This demo shows how analysis results are displayed in IO table format:")
    print("✓ Traditional matrix format with sectors as rows")
    print("✓ Multiple impact types as columns") 
    print("✓ Separate tables for different analysis types")
    print("✓ Export to Excel with multiple sheets")
    print("✓ Professional presentation suitable for reports")
    print()
    
    # Initialize analyzer
    print("Initializing Enhanced Analyzer...")
    analyzer = EnhancedSectorAnalyzer()
    
    # Find a demonstration sector
    steel_sectors = analyzer.io_loader.find_sectors_by_keyword('철강')
    if not steel_sectors:
        steel_sectors = analyzer.io_loader.find_sectors_by_keyword('27')
    
    if not steel_sectors:
        print("No suitable demonstration sector found.")
        return
    
    demo_sector = steel_sectors[0][0] 
    demo_sector_name = steel_sectors[0][1]
    
    print(f"\nDemonstration Sector: {demo_sector} - {demo_sector_name}")
    print(f"Scenario: 500 billion won reduction in sector demand")
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION 1: COMPREHENSIVE ANALYSIS IN IO TABLE FORMAT")
    print("=" * 80)
    
    # Run comprehensive analysis
    results = analyzer.comprehensive_sector_analysis(demo_sector, -500)
    
    # Display as IO tables
    analyzer.display_results_as_tables(results, export_excel=False)
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION 2: STEEL-COAL ANALYSIS IN IO TABLE FORMAT")  
    print("=" * 80)
    
    # Run steel-coal analysis
    steel_coal_results = analyzer.analyze_steel_coal_comprehensive(300)
    
    # Display steel-coal as IO tables
    analyzer.display_steel_coal_tables(steel_coal_results, export_excel=False)
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION 3: INDIVIDUAL TABLE COMPONENTS")
    print("=" * 80)
    
    # Demonstrate individual table creation
    print("\n1. SUPPLY CHAIN IMPACT MATRIX")
    print("-" * 50)
    
    supply_chain_results = results.get('supply_chain_analysis', {})
    if supply_chain_results:
        supply_matrices = analyzer.table_formatter.create_supply_chain_matrix(
            supply_chain_results, show_top_n=10
        )
        
        for matrix_name, matrix in supply_matrices.items():
            if not matrix.empty:
                analyzer.table_formatter.display_matrix_table(
                    matrix, f"Supply Chain: {matrix_name}", max_rows=8
                )
    
    print("\n2. IMPORT vs DOMESTIC COMPARISON MATRIX")
    print("-" * 50)
    
    import_domestic_results = results.get('import_domestic_analysis', {})
    if import_domestic_results:
        import_matrices = analyzer.table_formatter.create_import_domestic_matrix(
            import_domestic_results, show_top_n=8
        )
        
        comparison_matrix = import_matrices.get('Import_Domestic_Comparison')
        if comparison_matrix is not None and not comparison_matrix.empty:
            analyzer.table_formatter.display_matrix_table(
                comparison_matrix, "Import vs Domestic Comparison", max_rows=8
            )
    
    print("\n3. EMPLOYMENT IMPACT MATRIX")
    print("-" * 50)
    
    employment_results = results.get('employment_analysis', {})
    if employment_results:
        employment_matrix = analyzer.table_formatter.create_employment_matrix(
            employment_results, show_top_n=8
        )
        
        if not employment_matrix.empty:
            analyzer.table_formatter.display_matrix_table(
                employment_matrix, "Employment Impacts", max_rows=8
            )
    
    print("\n4. COMPREHENSIVE SUMMARY MATRIX")
    print("-" * 50)
    
    comprehensive_analysis = results.get('comprehensive_analysis', {})
    if comprehensive_analysis:
        summary_matrix = analyzer.table_formatter.create_comprehensive_summary_matrix(
            comprehensive_analysis
        )
        
        if not summary_matrix.empty:
            analyzer.table_formatter.display_matrix_table(
                summary_matrix, "Comprehensive Economic Summary", max_rows=8
            )
    
    print("\n" + "=" * 80)
    print("IO TABLE FORMAT FEATURES")
    print("=" * 80)
    
    print("""
KEY FEATURES OF IO TABLE FORMAT OUTPUT:

1. MATRIX STRUCTURE:
   - Rows: Affected sectors (with codes and names)
   - Columns: Different types of impacts
   - Values: Quantified impacts in appropriate units
   - Index: Sector codes for easy reference

2. MULTIPLE IMPACT TABLES:
   - Supply Chain Impacts (Direct, Indirect, Total)
   - Import vs Domestic Impacts (Separate and Comparison)
   - Employment Impacts (Jobs by sector)
   - Comprehensive Summary (All impact types)

3. PROFESSIONAL FORMATTING:
   - Aligned columns with proper spacing
   - Numbered rankings by impact magnitude
   - Consistent decimal formatting
   - Truncated names for readability

4. EXPORT CAPABILITIES:
   - Excel export with multiple sheets
   - Metadata sheet with analysis parameters
   - Summary sheet with aggregate statistics
   - Individual sheets for each impact type

5. CUSTOMIZATION OPTIONS:
   - Adjustable number of sectors to display
   - Flexible number formatting
   - Sortable by different criteria
   - Threshold filtering for significance

TYPICAL IO TABLE STRUCTURE EXAMPLE:
================================================================================
                        Supply Chain Impacts (billion won)
================================================================================
Sector_Code  Sector_Name                Direct    Indirect    Total     Rank
2711         Pig iron                   -45.2     -12.3      -57.5      1
1610         Coal products              -23.1     -8.9       -32.0      2  
4910         Transportation             -5.6      -15.2      -20.8      3
2610         Cement                     -8.4      -9.1       -17.5      4
================================================================================

IMPORT vs DOMESTIC COMPARISON EXAMPLE:
================================================================================
                        Import vs Domestic Impacts (billion won)
================================================================================
Sector_Code  Import_Impact  Domestic_Impact  Import_Share  Domestic_Share
2711         -12.3          -45.2           21.5%         78.5%
1610         -18.7          -13.3           58.4%         41.6%
4910         -3.2           -17.6           15.4%         84.6%
================================================================================
    """)
    
    print("\n" + "=" * 80)
    print("HOW TO USE IO TABLE OUTPUT")
    print("=" * 80)
    
    print("""
INTERACTIVE USAGE:
1. Run: python enhanced_sector_analyzer.py
2. Select option 5 or 6 for IO table format
3. Choose whether to export to Excel

PROGRAMMATIC USAGE:
from enhanced_sector_analyzer import EnhancedSectorAnalyzer
analyzer = EnhancedSectorAnalyzer()

# Run analysis
results = analyzer.comprehensive_sector_analysis('2711', -1000)

# Display as IO tables
analyzer.display_results_as_tables(results, export_excel=True)

# For steel-coal specific
steel_results = analyzer.analyze_steel_coal_comprehensive(500)
analyzer.display_steel_coal_tables(steel_results, export_excel=True)

EXCEL EXPORT FEATURES:
- Multiple sheets for different impact types
- Summary sheet with aggregate statistics  
- Metadata sheet with analysis parameters
- Professional formatting suitable for reports
- Easy integration with other Excel analyses

USE CASES:
- Academic research presentations
- Policy analysis reports
- Industry impact assessments
- Stakeholder briefings
- Economic modeling documentation
    """)

if __name__ == "__main__":
    demo_io_table_output()