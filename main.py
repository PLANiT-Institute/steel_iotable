from libs.io_analyzer import IOTableAnalyzer
import libs.wrapper as wr
import os


def main():
    """Main function to run the I-O analysis."""
    # Let user select I-O table file
    default_file = 'data/iotable_2020.xlsx'
    print(f"Default I-O table: {default_file}")
    file_choice = input("Press Enter to use default, or enter path to I-O table file: ").strip()

    if file_choice:
        if os.path.exists(file_choice):
            iotable_file = file_choice
        else:
            print(f"File not found. Using default: {default_file}")
            iotable_file = default_file
    else:
        iotable_file = default_file

    print(f"Loading: {iotable_file}\n")
    analyzer = IOTableAnalyzer(data_file=iotable_file)

    # Menu handlers mapping
    handlers = {
        '1': wr.handle_list_sectors,
        '2': wr.handle_single_effect,
        '3': wr.handle_all_effects,
        '4': wr.handle_aggregate_by_category,
        '5': wr.handle_linkages,
        '6': wr.handle_multipliers,
        '7': wr.handle_compare_sectors,
        '8': wr.handle_key_sectors,
        '9': wr.handle_sensitivity_analysis,
        '10': wr.handle_export_results,
    }

    while True:
        print("="*60)
        print("I-O TABLE ANALYZER - OPTIONS:")
        print("="*60)
        print("BASIC ANALYSIS:")
        print("  1. List all sectors")
        print("  2. Analyze single effect")
        print("  3. Analyze all effects")
        print("  4. Aggregate by category (code_h)")
        print("\nADVANCED ANALYSIS:")
        print("  5. Calculate linkages")
        print("  6. Calculate multipliers")
        print("  7. Compare sectors")
        print("  8. Identify key sectors")
        print("  9. Sensitivity analysis")
        print("\nUTILITIES:")
        print(" 10. Export results to file")
        print(" 11. Exit")
        print("="*60)

        choice = input("Select option (1-11): ").strip()

        if choice == '11':
            break
        elif choice in handlers:
            try:
                handlers[choice](analyzer)
            except ValueError as e:
                print(f"Error: {e}")
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
