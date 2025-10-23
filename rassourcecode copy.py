import numpy as np
import pandas as pd
import sys

class RASAnalyzer:
    def __init__(self, basic)

def ras_algorithm(A_0,u_1,v_1,tolerance=1e-6,max_iterations=1000):
    """
    A_0 (np.ndarray): base(seed) matrix
    u_1 (np.ndarray): target row sums vector
    v_1 (np.ndarray): target column sums vector

    Returns: np.ndarray: the balanced matrix (A_1)
    """

    A = A_0.copy()
    A[A == 0] =1e-10
    print(f"Running RAS for target year... Base matrix shape: {A.shape}")
    for i in range(max_iterations):
        row_sums = A.sum(axis=1)
        row_sums[row_sums == 0] = 1e-10
        r = u_1 / row_sums
        A = A * r[:, np.newaxis]
        col_sums = A.sum(axis=0)
        col_sums[col_sums == 0] = 1e-10
        s = v_1 / col_sums
        A = A * s
        row_error = np.sum(np.abs(A.sum(axis=1) - u_1))
        col_error = np.sum(np.abs(A.sum(axis=0) - v_1))
        total_error = row_error + col_error
        if total_error < tolerance:
            print(f"RAS algorithm converged in {i+1} iterations.")
            break
    else:
        print(f"Warning: RAS did not converge after {max_iterations} iterations. Total error: {total_error}")
    return A

def load_inputs(
    basic_matrix: str = 'data/iotableforcasting_v2.xlsx', 
    target_sum: str = 'data/iotableforcasting_v2.xlsx', 
    target_year=2030, 
    basic_sheet: str = 'producerprice', 
    target_sum_sheet: str = 'integrated'
    ):
    """
    Load input matrices for RAS algorithm from Excel files (optionally with specified sheet names).
    
    Args:
        basic_matrix (str): Path to the base matrix Excel file.
        target_sum (str): Path to the target sums Excel file.
        target_year: The year to load data for (for display or logic).
        basic_sheet (str): Name of the sheet in basic_matrix file to use.
        target_sum_sheet (str): Name of the sheet in target_sum file to use.

    """
    print(f"Preparing data for target year: {target_year}")
    print(f"Loading base matrix from '{basic_matrix}', sheet '{basic_sheet}'")
    df_basic = pd.read_excel(basic_matrix, sheet_name=basic_sheet, header=0, index_col=0)
    
    print(f"Loading target sums from '{target_sum}', sheet '{target_sum_sheet}'")
    df_target_sum = pd.read_excel(target_sum, sheet_name=target_sum_sheet, index_col=0)

    def format_code(code):
        try:
            return f"{int(float(code)):04d}"
        except (ValueError, TypeError):
            return str(code).strip()

    df_target_sum.index = df_target_sum.index.map(format_code)
    if 'code' in df_target_sum.index:
        df_target_sum = df_target_sum.drop('code')

    df_basic.index = df_basic.index.map(format_code)
    df_basic.columns = df_basic.columns.map(format_code)
    basic_rows_cleaned = df_basic.index[df_basic.index.str.isdigit()]
    basic_cols_cleaned = df_basic.columns[df_basic.columns.str.isdigit()]
    target_sum_idx_cleaned = df_target_sum.index[df_target_sum.index.str.isdigit()]

    common_sectors = sorted(list(
        set(target_sum_idx_cleaned)
        .intersection(set(basic_rows_cleaned))
        .intersection(set(basic_cols_cleaned))
    ))
    if not common_sectors:
        raise ValueError("No common sectors found.")
    print(f"Found {len(common_sectors)} common sectors.")


    
