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
                print("A                 - Direct Total coefficients")
                print("Am                - Direct Import coefficients") 
                print("Ad                - Direct Domestic coefficients")
                print("indirect_prod     - Indirect Production (I-Ad)⁻¹")
                print("indirect_import   - Indirect Import coefficients")
                print("value_added       - Value-Added coefficients")
                print("jobcoeff          - Total Job Creation coefficients")
                print("directemploycoeff - Direct Employment coefficients")
                
                coeff_type = input("Select coefficient type: ").strip()
                valid_types = ['A', 'Am', 'Ad', 'indirect_prod', 'indirect_import', 'value_added', 'jobcoeff', 'directemploycoeff']
                if coeff_type not in valid_types:
                    print("Invalid coefficient type. Using 'A' as default.")
                    coeff_type = 'A'
                
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
                print("This will multiply production coefficients by hydrogen demand scenarios.")

                # Load hydrogen coefficient data
                analyzer.load_hydrogen_coefficient()

                # Get available sectors and categories
                hydrogen_sectors = analyzer.get_hydrogen_sectors()
                print(f"\nAvailable hydrogen sectors: {len(hydrogen_sectors)} sectors")

                # Get demand change amount
                demand_change = float(input("Enter hydrogen demand change amount: "))

                # Get impact matrix (rows=sectors, columns=categories, values=impact)
                impact_matrix = analyzer.get_hydrogen_impact_matrix(demand_change)

                # Display matrix results
                print(f"\n{'='*80}")
                print(f"HYDROGEN IMPACT MATRIX - COEFFICIENTS × DEMAND")
                print(f"{'='*80}")
                print(f"Demand Change: {demand_change:,.0f}")
                print(f"Matrix Format: Rows=Sectors, Columns=Hydrogen Categories (백만원), Values=Impact")
                print(f"\n{impact_matrix.to_string(index=False, float_format='%.2f')}")
                print(f"\nTotal Sectors: {len(impact_matrix)}")

                # Calculate column totals
                print(f"\nColumn Totals:")
                for col in ['Production (백만원)', 'Storage (백만원)', 'Transportation (백만원)', 'Utilization (백만원)', 'Total (백만원)']:
                    total = impact_matrix[col].sum()
                    print(f"  {col}: {total:,.2f}")

                # Ask if user wants to export to Excel
                export_choice = input("\nExport impact matrix to Excel? (y/n): ").strip().lower()
                if export_choice == 'y':
                    # Create a results dict for export compatibility
                    results_dict = {
                        'demand_change': demand_change,
                        'category_percentages': {
                            'production': 0.341,
                            'storage': 0.104,
                            'transportation': 0.112,
                            'utilization': 0.444
                        }
                    }
                    analyzer.export_hydrogen_results_to_excel(results_dict)
                    print("Impact matrix exported to Excel!")

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