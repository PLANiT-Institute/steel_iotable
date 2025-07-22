import pandas as pd
import os

# Set the path to the iotable directory
iotable_path = "/Users/sanghyun/github/steel_iotable/iotable"

def examine_excel_file(file_path, file_description):
    """Examine an Excel file and return basic information about its structure"""
    print(f"\n{'='*60}")
    print(f"Examining: {file_description}")
    print(f"File: {os.path.basename(file_path)}")
    print(f"{'='*60}")
    
    try:
        # Get sheet names
        xl_file = pd.ExcelFile(file_path)
        print(f"Sheet names: {xl_file.sheet_names}")
        
        # Read the first sheet to understand structure
        df = pd.read_excel(file_path, sheet_name=xl_file.sheet_names[0], header=None)
        print(f"Shape: {df.shape}")
        print(f"First few rows:")
        print(df.head(10))
        
        return xl_file.sheet_names, df
    except Exception as e:
        print(f"Error reading file: {e}")
        return None, None

def search_for_steel_sectors(df, description):
    """Search for steel-related keywords in the dataframe"""
    print(f"\n--- Searching for steel-related sectors in {description} ---")
    steel_keywords = ['철', '강', '선철', 'steel', 'iron', '2711']
    
    found_sectors = []
    for idx, row in df.iterrows():
        for col_idx, cell in enumerate(row):
            if pd.notna(cell) and isinstance(cell, str):
                cell_lower = cell.lower()
                for keyword in steel_keywords:
                    if keyword in cell_lower:
                        found_sectors.append((idx, col_idx, cell))
                        break
    
    if found_sectors:
        print("Found steel-related entries:")
        for row_idx, col_idx, content in found_sectors:
            print(f"  Row {row_idx}, Col {col_idx}: {content}")
    else:
        print("No steel-related entries found with keywords")

# 1. Examine employment table (intermediate classification)
employment_file = os.path.join(iotable_path, "2020지역_부속표_고용표_통합중분류.xlsx")
employment_sheets, employment_df = examine_excel_file(employment_file, "Employment Table - Intermediate Classification")
if employment_df is not None:
    search_for_steel_sectors(employment_df, "Employment Table")

# 2. Examine supply table (intermediate classification)
supply_file = os.path.join(iotable_path, "2020_공급표_기초가격_통합중분류.xlsx")
supply_sheets, supply_df = examine_excel_file(supply_file, "Supply Table - Intermediate Classification")
if supply_df is not None:
    search_for_steel_sectors(supply_df, "Supply Table")

# 3. Examine use table (intermediate classification)
use_file = os.path.join(iotable_path, "2020_사용표_구매자가격_통합중분류.xlsx")
use_sheets, use_df = examine_excel_file(use_file, "Use Table - Intermediate Classification")
if use_df is not None:
    search_for_steel_sectors(use_df, "Use Table")

# 4. Look for sector codes and names in a more structured way
print(f"\n{'='*60}")
print("DETAILED SECTOR ANALYSIS")
print(f"{'='*60}")

# Try to find the sector listing in the employment table
if employment_df is not None:
    print("\n--- Looking for sector codes and names in employment table ---")
    # Look for patterns that might indicate sector codes (like numbers) and names
    for idx in range(min(50, len(employment_df))):  # Look at first 50 rows
        row = employment_df.iloc[idx]
        # Look for cells that might contain sector codes
        for col_idx, cell in enumerate(row):
            if pd.notna(cell):
                cell_str = str(cell)
                # Check if it looks like a sector code (starts with digit, contains certain patterns)
                if (cell_str.isdigit() and len(cell_str) >= 2) or '중분류' in cell_str or '기본부문' in cell_str:
                    print(f"  Row {idx}, Col {col_idx}: {cell}")
                    # Show the next few columns which might contain sector names
                    for next_col in range(col_idx + 1, min(col_idx + 3, len(row))):
                        if pd.notna(row.iloc[next_col]):
                            print(f"    -> Col {next_col}: {row.iloc[next_col]}")