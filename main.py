from libs.io_analyzer import IOTableAnalyzer

def main():
    """Main function to run the I-O analysis."""
    analyzer = IOTableAnalyzer()
    
    print("\n" + "="*60)
    print("STEEL-COAL I-O TABLE DIRECT EFFECTS ANALYZER")
    print("="*60)
    
    while True:
        print("\nAvailable options:")
        print("1. List all sectors")
        print("2. Analyze direct effects")
        print("3. Hydrogen production impact analysis (coefficients × demand)")
        print("4. Exit")

        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == '1':
            print("\nAll available sectors:")
            sectors = analyzer.get_sector_options()
            for display in sorted(sectors.values()):
                print(display)
        
        elif choice == '2':
            try:
                print("\nCoefficient types:")
                print("indirect_prod     - Domestic Production-Inducing Effect")
                print("indirect_import   - Import-Inducing Effect")
                print("value_added       - Value-Added Creation Effect")
                print("jobcoeff          - Job Creating Effect")
                print("directemploycoeff - Direct Employment Effect")

                coeff_type = input("Select coefficient type: ").strip()
                valid_types = ['indirect_prod', 'indirect_import', 'value_added', 'jobcoeff', 'directemploycoeff']
                if coeff_type not in valid_types:
                    print("Invalid coefficient type. Using 'indirect_prod' as default.")
                    coeff_type = 'indirect_prod'
                
                sector_input = input("Enter sector code (e.g., 111, 0111, or 2711): ").strip()
                
                # Convert input to proper format
                try:
                    sector_int = int(sector_input)
                    if sector_int < 1000:
                        sector_code = f"0{sector_int}"
                    else:
                        sector_code = str(sector_int)
                except ValueError:
                    # Already a string, use as is
                    sector_code = sector_input
                
                demand_change = float(input("Enter demand change amount: "))
                
                results = analyzer.calculate_direct_effects(sector_code, demand_change, coeff_type)
                analyzer.display_results(results)
                
            except ValueError as e:
                print(f"Error: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")

        elif choice == '3':
            try:
                print("\nHydrogen Production Impact Analysis")
                print("This will use all coefficient sheets ending with '계수' to calculate year-wise impacts.")

                # Get demand change amount
                demand_change = float(input("Enter hydrogen demand change amount: "))

                # Calculate hydrogen effects using all coefficient sheets
                results = analyzer.calculate_hydrogen_effects(demand_change, quiet=False)

                # Display results
                print(f"\n{'='*80}")
                print(f"HYDROGEN IMPACT ANALYSIS - YEAR-WISE EFFECTS")
                print(f"{'='*80}")
                print(f"Demand Change: {demand_change:,.0f}")
                print(f"Coefficient Sheets Used: {results['sheets_used']}")
                print(f"Sheet Names: {', '.join(results['sheet_names'])}")

                # Display the impact matrix
                impact_df = results['impact_matrix']
                print(f"\nImpact Matrix (Rows=Sectors, Columns=Years, Values=Impact in 백만원):")
                print(f"\n{impact_df.to_string(index=False, float_format='%.2f')}")

                # Display totals
                print(f"\nYear Totals:")
                year_columns = [col for col in impact_df.columns if col not in ['Number', 'Code', 'Sector']]
                for col in year_columns:
                    total = impact_df[col].sum()
                    print(f"  {col}: {total:,.2f}")

                total_impact = sum(impact_df[col].sum() for col in year_columns)
                print(f"\nGrand Total Impact: {total_impact:,.2f}")

                # Ask if user wants to export to Excel
                export_choice = input("\nExport results to Excel? (y/n): ").strip().lower()
                if export_choice == 'y':
                    analyzer.export_hydrogen_results_to_excel(results)
                    print("Hydrogen analysis results exported to Excel!")

            except ValueError as e:
                print(f"Error: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")

        elif choice == '4':
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Please select 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()