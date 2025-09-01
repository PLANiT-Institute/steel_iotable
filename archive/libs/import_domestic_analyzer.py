import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from .io_data_loader import IODataLoader

class ImportDomesticAnalyzer:
    """
    Separate analysis of import and domestic impacts.
    Uses import input coefficients (Am) and domestic input coefficients (Ad) 
    to analyze how demand changes affect imports vs domestic production.
    """
    
    def __init__(self, io_loader: IODataLoader, basic_io_file: str):
        """
        Initialize the Import-Domestic Analyzer.
        
        Args:
            io_loader: IODataLoader instance
            basic_io_file: Path to basic IO file with import/domestic coefficients
        """
        self.io_loader = io_loader
        self.basic_io_file = basic_io_file
        
        # Import and domestic coefficient matrices
        self.import_coefficients = None  # Am matrix
        self.domestic_coefficients = None  # Ad matrix
        
        # Leontief inverses
        self.import_leontief = None
        self.domestic_leontief = None
        
        self._load_import_domestic_data()
        self._calculate_leontief_inverses()
    
    def _load_import_domestic_data(self):
        """Load import and domestic input coefficient matrices."""
        try:
            # Load import input coefficients (Am)
            self.import_coefficients = pd.read_excel(
                self.basic_io_file,
                sheet_name='수입투입계수(Am)',
                skiprows=6,
                index_col=[0, 1],
                header=[0, 1]
            )
            print(f"Loaded import coefficients (Am): {self.import_coefficients.shape}")
            
            # Load domestic input coefficients (Ad)
            self.domestic_coefficients = pd.read_excel(
                self.basic_io_file,
                sheet_name='국산투입계수(Ad)',
                skiprows=6,
                index_col=[0, 1],
                header=[0, 1]
            )
            print(f"Loaded domestic coefficients (Ad): {self.domestic_coefficients.shape}")
            
        except Exception as e:
            print(f"Warning: Could not load import/domestic coefficients: {str(e)}")
            self.import_coefficients = None
            self.domestic_coefficients = None
    
    def _calculate_leontief_inverses(self):
        """Calculate Leontief inverses for import and domestic coefficients."""
        try:
            # Import Leontief inverse: (I - Am)^(-1)
            if self.import_coefficients is not None:
                Am_matrix = self.import_coefficients.fillna(0).values
                n_rows, n_cols = Am_matrix.shape
                matrix_size = min(n_rows, n_cols)
                Am_square = Am_matrix[:matrix_size, :matrix_size]
                
                I_minus_Am = np.eye(matrix_size) - Am_square
                try:
                    self.import_leontief = np.linalg.inv(I_minus_Am)
                    print(f"Calculated import Leontief inverse: {matrix_size}x{matrix_size}")
                except np.linalg.LinAlgError:
                    self.import_leontief = np.linalg.pinv(I_minus_Am)
                    print(f"Calculated import Leontief pseudo-inverse: {matrix_size}x{matrix_size}")
            
            # Domestic Leontief inverse: (I - Ad)^(-1)
            if self.domestic_coefficients is not None:
                Ad_matrix = self.domestic_coefficients.fillna(0).values
                n_rows, n_cols = Ad_matrix.shape
                matrix_size = min(n_rows, n_cols)
                Ad_square = Ad_matrix[:matrix_size, :matrix_size]
                
                I_minus_Ad = np.eye(matrix_size) - Ad_square
                try:
                    self.domestic_leontief = np.linalg.inv(I_minus_Ad)
                    print(f"Calculated domestic Leontief inverse: {matrix_size}x{matrix_size}")
                except np.linalg.LinAlgError:
                    self.domestic_leontief = np.linalg.pinv(I_minus_Ad)
                    print(f"Calculated domestic Leontief pseudo-inverse: {matrix_size}x{matrix_size}")
                    
        except Exception as e:
            print(f"Warning: Could not calculate import/domestic Leontief inverses: {str(e)}")
    
    def analyze_import_domestic_impacts(
        self,
        target_sector: str,
        demand_change: float
    ) -> Dict:
        """
        Analyze separate import and domestic impacts from demand change.
        
        Args:
            target_sector: Target sector code
            demand_change: Demand change amount (10억원)
            
        Returns:
            Dictionary with separate import and domestic impacts
        """
        results = {
            'target_sector': target_sector,
            'target_sector_name': self.io_loader.get_sector_name(target_sector),
            'demand_change': demand_change,
            'import_impacts': {},
            'domestic_impacts': {},
            'total_import_effect': 0,
            'total_domestic_effect': 0,
            'import_share': 0,
            'domestic_share': 0,
            'import_multiplier': 0,
            'domestic_multiplier': 0
        }
        
        # Calculate import impacts
        if self.import_leontief is not None:
            import_impacts = self._calculate_sectoral_impacts(
                target_sector, demand_change, self.import_leontief, 'import'
            )
            results['import_impacts'] = import_impacts
            results['total_import_effect'] = sum(abs(v) for v in import_impacts.values())
        
        # Calculate domestic impacts
        if self.domestic_leontief is not None:
            domestic_impacts = self._calculate_sectoral_impacts(
                target_sector, demand_change, self.domestic_leontief, 'domestic'
            )
            results['domestic_impacts'] = domestic_impacts
            results['total_domestic_effect'] = sum(abs(v) for v in domestic_impacts.values())
        
        # Calculate shares and multipliers
        total_effect = results['total_import_effect'] + results['total_domestic_effect']
        if total_effect > 0:
            results['import_share'] = results['total_import_effect'] / total_effect
            results['domestic_share'] = results['total_domestic_effect'] / total_effect
        
        if demand_change != 0:
            results['import_multiplier'] = results['total_import_effect'] / abs(demand_change)
            results['domestic_multiplier'] = results['total_domestic_effect'] / abs(demand_change)
        
        return results
    
    def _calculate_sectoral_impacts(
        self,
        target_sector: str,
        demand_change: float,
        leontief_matrix: np.ndarray,
        impact_type: str
    ) -> Dict[str, float]:
        """Calculate sectoral impacts using specified Leontief matrix."""
        impacts = {}
        
        try:
            # Find sector index
            sector_idx = None
            for i, code in enumerate(self.io_loader.sector_codes):
                if code == target_sector and i < leontief_matrix.shape[0]:
                    sector_idx = i
                    break
            
            if sector_idx is None:
                return impacts
            
            # Create demand shock vector
            demand_shock = np.zeros(leontief_matrix.shape[0])
            demand_shock[sector_idx] = demand_change
            
            # Calculate impacts
            output_changes = leontief_matrix @ demand_shock
            
            # Convert to dictionary
            for i, change in enumerate(output_changes):
                if abs(change) > 0.01 and i < len(self.io_loader.sector_codes):
                    sector_code = self.io_loader.sector_codes[i]
                    sector_name = self.io_loader.get_sector_name(sector_code)
                    sector_label = f"{sector_code}: {sector_name}"
                    impacts[sector_label] = change
            
            return impacts
            
        except Exception as e:
            print(f"Warning: Could not calculate {impact_type} impacts: {str(e)}")
            return impacts
    
    def get_import_domestic_linkages(self, target_sector: str) -> Dict:
        """
        Get import vs domestic linkages for a target sector.
        
        Args:
            target_sector: Target sector code
            
        Returns:
            Dictionary with import and domestic linkage structure
        """
        linkages = {
            'import_linkages': {},
            'domestic_linkages': {},
            'import_dependency': {},
            'domestic_dependency': {}
        }
        
        try:
            # Get import linkages (backward)
            if self.import_coefficients is not None:
                import_links = self._get_coefficient_linkages(
                    target_sector, self.import_coefficients
                )
                linkages['import_linkages'] = import_links
            
            # Get domestic linkages (backward)
            if self.domestic_coefficients is not None:
                domestic_links = self._get_coefficient_linkages(
                    target_sector, self.domestic_coefficients
                )
                linkages['domestic_linkages'] = domestic_links
            
            # Calculate dependency ratios
            linkages['import_dependency'] = self._calculate_dependency_ratios(
                linkages['import_linkages'], linkages['domestic_linkages']
            )
            
        except Exception as e:
            print(f"Warning: Could not calculate linkages: {str(e)}")
        
        return linkages
    
    def _get_coefficient_linkages(
        self, 
        target_sector: str, 
        coefficient_matrix: pd.DataFrame,
        threshold: float = 0.001
    ) -> Dict[str, float]:
        """Get linkages from coefficient matrix."""
        linkages = {}
        
        try:
            # Find column index for target sector
            target_col_idx = None
            for j, col in enumerate(coefficient_matrix.columns):
                if isinstance(col, tuple) and str(col[0]) == str(target_sector):
                    target_col_idx = j
                    break
            
            if target_col_idx is None:
                return linkages
            
            # Get coefficients for this sector
            for i, idx in enumerate(coefficient_matrix.index):
                if isinstance(idx, tuple):
                    supplier_code = str(idx[0])
                    coefficient = float(coefficient_matrix.iloc[i, target_col_idx])
                    
                    if coefficient > threshold:
                        supplier_name = self.io_loader.get_sector_name(supplier_code)
                        linkages[f"{supplier_code}: {supplier_name}"] = coefficient
            
            return linkages
            
        except Exception as e:
            print(f"Warning: Error getting coefficient linkages: {str(e)}")
            return linkages
    
    def _calculate_dependency_ratios(
        self, 
        import_links: Dict[str, float], 
        domestic_links: Dict[str, float]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate import vs domestic dependency ratios."""
        dependency = {}
        
        # Get all sectors that appear in either import or domestic links
        all_sectors = set()
        for sector in import_links.keys():
            all_sectors.add(sector)
        for sector in domestic_links.keys():
            all_sectors.add(sector)
        
        for sector in all_sectors:
            import_coeff = import_links.get(sector, 0)
            domestic_coeff = domestic_links.get(sector, 0)
            total_coeff = import_coeff + domestic_coeff
            
            if total_coeff > 0:
                dependency[sector] = {
                    'import_share': import_coeff / total_coeff,
                    'domestic_share': domestic_coeff / total_coeff,
                    'import_coefficient': import_coeff,
                    'domestic_coefficient': domestic_coeff,
                    'total_coefficient': total_coeff
                }
        
        return dependency
    
    def analyze_import_substitution_potential(
        self,
        target_sector: str,
        substitution_rate: float = 0.1
    ) -> Dict:
        """
        Analyze potential for import substitution.
        
        Args:
            target_sector: Target sector code
            substitution_rate: Rate of import substitution (0.1 = 10%)
            
        Returns:
            Analysis of import substitution effects
        """
        results = {
            'target_sector': target_sector,
            'substitution_rate': substitution_rate,
            'import_reduction': {},
            'domestic_increase': {},
            'net_domestic_effect': 0,
            'sectors_affected': 0
        }
        
        # Get import-domestic linkages
        linkages = self.get_import_domestic_linkages(target_sector)
        dependency = linkages.get('import_dependency', {})
        
        for sector, deps in dependency.items():
            import_coeff = deps['import_coefficient']
            domestic_coeff = deps['domestic_coefficient']
            
            # Calculate import reduction and domestic increase
            import_reduction = import_coeff * substitution_rate
            domestic_increase = import_reduction  # Assuming 1:1 substitution
            
            if import_reduction > 0.001:  # Threshold for significance
                results['import_reduction'][sector] = -import_reduction
                results['domestic_increase'][sector] = domestic_increase
                results['net_domestic_effect'] += domestic_increase
                results['sectors_affected'] += 1
        
        return results
    
    def compare_import_domestic_multipliers(self) -> Dict:
        """
        Compare import and domestic multipliers across sectors.
        
        Returns:
            Comparison of multiplier effects
        """
        comparison = {
            'sector_multipliers': {},
            'average_import_multiplier': 0,
            'average_domestic_multiplier': 0,
            'high_import_dependency_sectors': [],
            'high_domestic_dependency_sectors': []
        }
        
        # Analyze first 10 sectors for demonstration
        sample_sectors = self.io_loader.sector_codes[:10]
        
        import_multipliers = []
        domestic_multipliers = []
        
        for sector in sample_sectors:
            analysis = self.analyze_import_domestic_impacts(sector, 1000)
            
            import_mult = analysis.get('import_multiplier', 0)
            domestic_mult = analysis.get('domestic_multiplier', 0)
            
            comparison['sector_multipliers'][sector] = {
                'import_multiplier': import_mult,
                'domestic_multiplier': domestic_mult,
                'import_share': analysis.get('import_share', 0),
                'domestic_share': analysis.get('domestic_share', 0)
            }
            
            if import_mult > 0:
                import_multipliers.append(import_mult)
            if domestic_mult > 0:
                domestic_multipliers.append(domestic_mult)
            
            # Classify sectors by dependency
            if analysis.get('import_share', 0) > 0.6:
                comparison['high_import_dependency_sectors'].append(sector)
            elif analysis.get('domestic_share', 0) > 0.6:
                comparison['high_domestic_dependency_sectors'].append(sector)
        
        # Calculate averages
        if import_multipliers:
            comparison['average_import_multiplier'] = sum(import_multipliers) / len(import_multipliers)
        if domestic_multipliers:
            comparison['average_domestic_multiplier'] = sum(domestic_multipliers) / len(domestic_multipliers)
        
        return comparison
    
    def is_data_available(self) -> bool:
        """Check if import/domestic data is available."""
        return (self.import_coefficients is not None and 
                self.domestic_coefficients is not None)
    
    def get_data_info(self) -> Dict:
        """Get information about loaded import/domestic data."""
        return {
            'import_coefficients_loaded': self.import_coefficients is not None,
            'domestic_coefficients_loaded': self.domestic_coefficients is not None,
            'import_leontief_calculated': self.import_leontief is not None,
            'domestic_leontief_calculated': self.domestic_leontief is not None,
            'import_coefficients_shape': self.import_coefficients.shape if self.import_coefficients is not None else None,
            'domestic_coefficients_shape': self.domestic_coefficients.shape if self.domestic_coefficients is not None else None
        }