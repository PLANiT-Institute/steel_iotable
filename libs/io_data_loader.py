import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional

class IODataLoader:
    """
    Input-Output Data Loader for Korean IO tables at basic prices (기초가격).
    Loads national-level basic sector data (기본부문) from Excel files.
    """
    
    def __init__(self, basic_io_file: str):
        """
        Initialize the IO Data Loader.
        
        Args:
            basic_io_file: Path to the basic IO table Excel file (기초가격_기본부문)
        """
        self.basic_io_file = basic_io_file
        self.transaction_table = None
        self.input_coefficients = None
        self.sector_mapping = {}
        self.sector_codes = []
        self.sector_names = []
        
        self._load_data()
    
    def _load_data(self):
        """Load all IO table data from Excel file."""
        try:
            # First, check available sheets
            xl_file = pd.ExcelFile(self.basic_io_file)
            print(f"Available sheets: {xl_file.sheet_names}")
            
            # Load transaction table (총거래표)
            self._load_transaction_table()
            
            # Load input coefficients (총투입계수)
            self._load_input_coefficients()
            
            # Extract sector information
            self._extract_sector_info()
            
        except Exception as e:
            raise ValueError(f"Error loading IO data: {str(e)}")
    
    def _load_transaction_table(self):
        """Load the transaction table (총거래표)."""
        try:
            # Try different possible sheet names
            possible_names = ['총거래표', '기본거래표', '거래표', 'Transaction']
            
            xl_file = pd.ExcelFile(self.basic_io_file)
            sheet_name = None
            
            for name in possible_names:
                if name in xl_file.sheet_names:
                    sheet_name = name
                    break
            
            if sheet_name is None:
                # Use the first sheet as fallback
                sheet_name = xl_file.sheet_names[0]
                print(f"Using first sheet: {sheet_name}")
            
            # Load the transaction table
            self.transaction_table = pd.read_excel(
                self.basic_io_file,
                sheet_name=sheet_name,
                skiprows=6,
                index_col=[0, 1],
                header=[0, 1]
            )
            
            print(f"Loaded transaction table from '{sheet_name}': {self.transaction_table.shape}")
            
        except Exception as e:
            print(f"Warning: Could not load transaction table: {str(e)}")
            self.transaction_table = None
    
    def _load_input_coefficients(self):
        """Load input coefficient matrix (총투입계수)."""
        try:
            xl_file = pd.ExcelFile(self.basic_io_file)
            
            # Try different possible sheet names for input coefficients
            possible_names = ['총투입계수(A)', '투입계수', 'A', 'Input_Coefficients']
            sheet_name = None
            
            for name in possible_names:
                if name in xl_file.sheet_names:
                    sheet_name = name
                    break
            
            if sheet_name:
                self.input_coefficients = pd.read_excel(
                    self.basic_io_file,
                    sheet_name=sheet_name,
                    skiprows=6,
                    index_col=[0, 1],
                    header=[0, 1]
                )
                print(f"Loaded input coefficients from '{sheet_name}': {self.input_coefficients.shape}")
            else:
                # Calculate from transaction table if available
                if self.transaction_table is not None:
                    self._calculate_input_coefficients()
                
        except Exception as e:
            print(f"Warning: Could not load input coefficients: {str(e)}")
            if self.transaction_table is not None:
                self._calculate_input_coefficients()
    
    def _calculate_input_coefficients(self):
        """Calculate input coefficients from transaction table."""
        try:
            if self.transaction_table is None:
                return
                
            # Get the intermediate transaction part (exclude final demand columns)
            # Assume final demand starts after intermediate sectors
            n_sectors = min(self.transaction_table.shape[0], self.transaction_table.shape[1])
            intermediate_table = self.transaction_table.iloc[:n_sectors, :n_sectors]
            
            # Calculate total output (row sums)
            total_output = intermediate_table.sum(axis=1)
            
            # Calculate input coefficients: A[i,j] = X[i,j] / X[j]
            self.input_coefficients = intermediate_table.div(total_output, axis=1).fillna(0)
            
            print(f"Calculated input coefficients: {self.input_coefficients.shape}")
            
        except Exception as e:
            print(f"Warning: Could not calculate input coefficients: {str(e)}")
            self.input_coefficients = None
    
    def _extract_sector_info(self):
        """Extract sector codes and names from the loaded data."""
        try:
            if self.transaction_table is not None:
                # Extract from transaction table index
                for idx in self.transaction_table.index:
                    if isinstance(idx, tuple) and len(idx) >= 2:
                        code = str(idx[0]).strip()
                        name = str(idx[1]).strip()
                        if code != 'nan' and name != 'nan':
                            self.sector_codes.append(code)
                            self.sector_names.append(f"{code}: {name}")
                            self.sector_mapping[code] = name
            
            elif self.input_coefficients is not None:
                # Extract from input coefficients index
                for idx in self.input_coefficients.index:
                    if isinstance(idx, tuple) and len(idx) >= 2:
                        code = str(idx[0]).strip()
                        name = str(idx[1]).strip()
                        if code != 'nan' and name != 'nan':
                            self.sector_codes.append(code)
                            self.sector_names.append(f"{code}: {name}")
                            self.sector_mapping[code] = name
            
            print(f"Extracted {len(self.sector_codes)} sectors")
            
        except Exception as e:
            print(f"Warning: Could not extract sector info: {str(e)}")
            # Create fallback sector list
            self.sector_codes = [f"{i:04d}" for i in range(1, 398)]
            self.sector_names = [f"{code}: Sector {code}" for code in self.sector_codes]
            self.sector_mapping = {code: f"Sector {code}" for code in self.sector_codes}
    
    def get_sector_codes(self) -> List[str]:
        """Get list of available sector codes."""
        return self.sector_codes.copy()
    
    def get_sector_names(self) -> List[str]:
        """Get list of sector codes with names."""
        return self.sector_names.copy()
    
    def get_sector_name(self, sector_code: str) -> str:
        """Get sector name for a given code."""
        return self.sector_mapping.get(sector_code, f"Unknown sector {sector_code}")
    
    def get_input_coefficient(self, from_sector: str, to_sector: str) -> float:
        """
        Get input coefficient from one sector to another.
        
        Args:
            from_sector: Source sector code
            to_sector: Destination sector code
            
        Returns:
            Input coefficient value
        """
        if self.input_coefficients is None:
            return 0.0
        
        try:
            # Find the row and column indices
            from_idx = None
            to_idx = None
            
            for i, idx in enumerate(self.input_coefficients.index):
                if isinstance(idx, tuple) and str(idx[0]) == str(from_sector):
                    from_idx = i
                    break
            
            for j, col in enumerate(self.input_coefficients.columns):
                if isinstance(col, tuple) and str(col[0]) == str(to_sector):
                    to_idx = j
                    break
            
            if from_idx is not None and to_idx is not None:
                return float(self.input_coefficients.iloc[from_idx, to_idx])
            else:
                return 0.0
                
        except Exception as e:
            print(f"Warning: Could not get coefficient {from_sector} -> {to_sector}: {str(e)}")
            return 0.0
    
    def get_backward_linkages(self, sector_code: str, threshold: float = 0.001) -> Dict[str, float]:
        """
        Get backward linkages for a sector (what this sector purchases from others).
        
        Args:
            sector_code: Target sector code
            threshold: Minimum coefficient value to include
            
        Returns:
            Dictionary of {supplier_sector: coefficient}
        """
        linkages = {}
        
        if self.input_coefficients is None:
            return linkages
        
        try:
            # Find column index for the target sector
            target_col_idx = None
            for j, col in enumerate(self.input_coefficients.columns):
                if isinstance(col, tuple) and str(col[0]) == str(sector_code):
                    target_col_idx = j
                    break
            
            if target_col_idx is None:
                return linkages
            
            # Get all coefficients for this sector (column)
            for i, idx in enumerate(self.input_coefficients.index):
                if isinstance(idx, tuple):
                    supplier_code = str(idx[0])
                    coefficient = float(self.input_coefficients.iloc[i, target_col_idx])
                    
                    if coefficient > threshold:
                        supplier_name = self.get_sector_name(supplier_code)
                        linkages[f"{supplier_code}: {supplier_name}"] = coefficient
            
            return linkages
            
        except Exception as e:
            print(f"Warning: Could not calculate backward linkages for {sector_code}: {str(e)}")
            return linkages
    
    def get_forward_linkages(self, sector_code: str, threshold: float = 0.001) -> Dict[str, float]:
        """
        Get forward linkages for a sector (what other sectors purchase from this sector).
        
        Args:
            sector_code: Source sector code
            threshold: Minimum coefficient value to include
            
        Returns:
            Dictionary of {customer_sector: coefficient}
        """
        linkages = {}
        
        if self.input_coefficients is None:
            return linkages
        
        try:
            # Find row index for the source sector
            source_row_idx = None
            for i, idx in enumerate(self.input_coefficients.index):
                if isinstance(idx, tuple) and str(idx[0]) == str(sector_code):
                    source_row_idx = i
                    break
            
            if source_row_idx is None:
                return linkages
            
            # Get all coefficients from this sector (row)
            for j, col in enumerate(self.input_coefficients.columns):
                if isinstance(col, tuple):
                    customer_code = str(col[0])
                    coefficient = float(self.input_coefficients.iloc[source_row_idx, j])
                    
                    if coefficient > threshold:
                        customer_name = self.get_sector_name(customer_code)
                        linkages[f"{customer_code}: {customer_name}"] = coefficient
            
            return linkages
            
        except Exception as e:
            print(f"Warning: Could not calculate forward linkages for {sector_code}: {str(e)}")
            return linkages
    
    def find_sectors_by_keyword(self, keyword: str) -> List[Tuple[str, str]]:
        """
        Find sectors that contain a keyword in their name.
        
        Args:
            keyword: Search keyword
            
        Returns:
            List of (sector_code, sector_name) tuples
        """
        matching_sectors = []
        
        for code, name in self.sector_mapping.items():
            if keyword.lower() in name.lower():
                matching_sectors.append((code, name))
        
        return matching_sectors
    
    def is_data_loaded(self) -> bool:
        """Check if IO data is properly loaded."""
        return (self.transaction_table is not None or self.input_coefficients is not None) and len(self.sector_codes) > 0
    
    def get_data_info(self) -> Dict:
        """Get information about loaded data."""
        return {
            'transaction_table_loaded': self.transaction_table is not None,
            'input_coefficients_loaded': self.input_coefficients is not None,
            'num_sectors': len(self.sector_codes),
            'transaction_table_shape': self.transaction_table.shape if self.transaction_table is not None else None,
            'input_coefficients_shape': self.input_coefficients.shape if self.input_coefficients is not None else None
        }