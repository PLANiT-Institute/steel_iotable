import numpy as np
import sys

def ras_algorithm(A_0,u_1,v_1,tolerance=1e-6,max_iterations=1000)
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

    