#!/usr/bin/env python3
"""Test just Excel file loading"""

import pandas as pd

try:
    print("Testing basic Excel file access...")
    
    file_path = 'iotable/(표)(2020실측)투입산출표_기초가격_기본부문.xlsx'
    
    print("1. Reading Excel file info...")
    xl_file = pd.ExcelFile(file_path)
    print(f"   Available sheets: {len(xl_file.sheet_names)}")
    
    print("2. Reading first sheet...")
    df = pd.read_excel(file_path, sheet_name=xl_file.sheet_names[0], nrows=5)
    print(f"   Shape: {df.shape}")
    print("   ✓ Basic Excel read successful")
    
    print("3. Reading with complex parameters (like IO loader)...")
    # This is what the IODataLoader does
    df2 = pd.read_excel(
        file_path,
        sheet_name='A표_총거래표(기초)',
        skiprows=6,
        index_col=[0, 1],
        header=[0, 1],
        nrows=10  # Limit rows for test
    )
    print(f"   Complex read shape: {df2.shape}")
    print("   ✓ Complex Excel read successful")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()