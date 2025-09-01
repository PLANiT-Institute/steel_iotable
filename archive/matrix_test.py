#!/usr/bin/env python3
"""Test just the matrix loading"""

import sys
sys.path.append('.')

try:
    print("Testing matrix loading...")
    from libs.io_data_loader import IODataLoader
    
    print("Creating loader...")
    loader = IODataLoader('iotable/(표)(2020실측)투입산출표_기초가격_기본부문.xlsx')
    
    print("Matrix shapes:")
    if loader.transaction_table is not None:
        print(f"  Transaction table: {loader.transaction_table.shape}")
    if loader.input_coefficients is not None:
        print(f"  Input coefficients: {loader.input_coefficients.shape}")
        print(f"  Input coeff min/max: {loader.input_coefficients.min().min():.6f} / {loader.input_coefficients.max().max():.6f}")
    
    print(f"Sectors loaded: {len(loader.sector_codes)}")
    print(f"Sample sectors: {loader.sector_codes[:10]}")
    
    print("✓ Matrix loading completed successfully")
    
except Exception as e:
    print(f"Error during matrix loading: {e}")
    import traceback
    traceback.print_exc()