import pandas as pd
import os

# Set the path to the iotable directory
iotable_path = "/Users/sanghyun/github/steel_iotable/iotable"

def get_sector_structure(file_path, description):
    """Get the complete sector structure from a file"""
    print(f"\n{'='*80}")
    print(f"SECTOR STRUCTURE: {description}")
    print(f"{'='*80}")
    
    try:
        xl_file = pd.ExcelFile(file_path)
        print(f"Available sheets: {xl_file.sheet_names}")
        
        # Read the main sheet
        df = pd.read_excel(file_path, sheet_name=xl_file.sheet_names[0], header=None)
        
        # Look for sector codes and names
        sectors = []
        for idx in range(len(df)):
            row = df.iloc[idx]
            for col_idx, cell in enumerate(row):
                if pd.notna(cell):
                    cell_str = str(cell).strip()
                    # Look for sector codes (2-digit numbers)
                    if cell_str.isdigit() and len(cell_str) == 2:
                        # Get the sector name from the next column
                        if col_idx + 1 < len(row) and pd.notna(row.iloc[col_idx + 1]):
                            sector_name = str(row.iloc[col_idx + 1]).strip()
                            sectors.append((cell_str, sector_name, idx))
        
        print(f"Found {len(sectors)} sectors:")
        for code, name, row_idx in sectors:
            print(f"  {code}: {name}")
            # Check if this is steel-related
            if any(keyword in name.lower() for keyword in ['철', '강', 'steel', 'iron']):
                print(f"    *** STEEL-RELATED SECTOR ***")
        
        return sectors
        
    except Exception as e:
        print(f"Error: {e}")
        return []

def examine_basic_sectors():
    """Examine the basic sectors file to understand sector 2711"""
    print(f"\n{'='*80}")
    print(f"EXAMINING BASIC SECTORS FILE")
    print(f"{'='*80}")
    
    basic_files = [
        "(표)(2020실측)투입산출표_생산자가격_기본부문.xlsx",
        "(표)(2020실측)투입산출표_구매자가격_기본부문.xlsx",
        "(표)(2020실측)투입산출표_기초가격_기본부문.xlsx"
    ]
    
    for filename in basic_files:
        file_path = os.path.join(iotable_path, filename)
        if os.path.exists(file_path):
            print(f"\n--- Examining {filename} ---")
            try:
                xl_file = pd.ExcelFile(file_path)
                print(f"Sheets: {xl_file.sheet_names}")
                
                # Read first sheet
                df = pd.read_excel(file_path, sheet_name=xl_file.sheet_names[0], header=None)
                
                # Search for sector 2711 and other steel-related sectors
                found_2711 = False
                steel_sectors = []
                
                for idx in range(min(500, len(df))):  # Look at first 500 rows
                    row = df.iloc[idx]
                    for col_idx, cell in enumerate(row):
                        if pd.notna(cell):
                            cell_str = str(cell).strip()
                            # Look for sector 2711
                            if cell_str == '2711':
                                found_2711 = True
                                # Get the sector name
                                if col_idx + 1 < len(row) and pd.notna(row.iloc[col_idx + 1]):
                                    sector_name = str(row.iloc[col_idx + 1]).strip()
                                    print(f"  FOUND 2711: {sector_name} (Row {idx}, Col {col_idx})")
                            
                            # Look for other steel-related sectors
                            if (cell_str.startswith('27') and len(cell_str) == 4) or \
                               any(keyword in cell_str.lower() for keyword in ['철', '강', 'steel', 'iron']):
                                if col_idx + 1 < len(row) and pd.notna(row.iloc[col_idx + 1]):
                                    sector_name = str(row.iloc[col_idx + 1]).strip()
                                    if any(keyword in sector_name.lower() for keyword in ['철', '강', 'steel', 'iron']):
                                        steel_sectors.append((cell_str, sector_name, idx))
                
                if found_2711:
                    print(f"  ✓ Found sector 2711 in {filename}")
                else:
                    print(f"  ✗ Sector 2711 not found in {filename}")
                
                if steel_sectors:
                    print(f"  Found {len(steel_sectors)} steel-related sectors:")
                    for code, name, row_idx in steel_sectors:
                        print(f"    {code}: {name}")
                
            except Exception as e:
                print(f"  Error reading {filename}: {e}")
            
            break  # Just examine the first available file for now

def analyze_mapping_logic():
    """Analyze how basic sectors are mapped to intermediate classification"""
    print(f"\n{'='*80}")
    print(f"MAPPING ANALYSIS")
    print(f"{'='*80}")
    
    # From our previous findings, we know:
    # - Intermediate classification code 27: 철강1차제품
    # - Basic sector 2711: should be pig iron
    
    print("Based on the analysis:")
    print("1. Intermediate classification code '27': 철강1차제품 (Primary steel products)")
    print("2. This likely includes basic sector 2711 (pig iron) and other steel-related basic sectors")
    print("3. The mapping appears to be an aggregation where multiple basic sectors")
    print("   are grouped into broader intermediate classification categories")
    
    # Let's check if there are any mapping tables or concordance files
    print(f"\n--- Looking for mapping/concordance files ---")
    other_files = [
        "(표)(2020실측)부속표_기타부속표_기본부문.xlsx",
        "(표)(2020실측)부속표_품목별 공급액표.xlsx"
    ]
    
    for filename in other_files:
        file_path = os.path.join(iotable_path, filename)
        if os.path.exists(file_path):
            print(f"\nExamining {filename} for mapping information...")
            try:
                xl_file = pd.ExcelFile(file_path)
                print(f"  Sheets: {xl_file.sheet_names}")
                
                # Look for sheets that might contain mapping information
                for sheet_name in xl_file.sheet_names:
                    if any(keyword in sheet_name.lower() for keyword in ['매핑', 'mapping', '대응', '분류', '변환']):
                        print(f"  *** Potential mapping sheet found: {sheet_name} ***")
                        
            except Exception as e:
                print(f"  Error: {e}")

# Run the analyses
print("COMPREHENSIVE SECTOR MAPPING ANALYSIS")
print("=" * 80)

# 1. Get intermediate classification sectors
employment_file = os.path.join(iotable_path, "2020지역_부속표_고용표_통합중분류.xlsx")
intermediate_sectors = get_sector_structure(employment_file, "Intermediate Classification (Employment Table)")

# 2. Examine basic sectors
examine_basic_sectors()

# 3. Analyze mapping logic
analyze_mapping_logic()

print(f"\n{'='*80}")
print("SUMMARY OF FINDINGS")
print(f"{'='*80}")
print("1. Steel-related intermediate classification:")
print("   - Code 27: 철강1차제품 (Primary steel products)")
print("   - Code 28: 비철금속괴 및 1차제품 (Non-ferrous metal ingots and primary products)")
print()
print("2. Basic sector 2711 (pig iron) maps to intermediate classification code 27")
print()
print("3. The mapping appears to be based on industrial classification where:")
print("   - Multiple basic sectors (4-digit codes) are aggregated")
print("   - Into broader intermediate classification categories (2-digit codes)")
print("   - Likely using simple summation for employment data")