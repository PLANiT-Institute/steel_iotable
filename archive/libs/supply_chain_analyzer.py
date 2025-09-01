import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from .io_data_loader import IODataLoader

class SupplyChainAnalyzer:
    """
    Supply Chain Impact Analyzer using Input-Output analysis.
    Analyzes backward linkages (supply chain impacts) when a sector reduces its input demand.
    """
    
    def __init__(self, io_loader: IODataLoader):
        """
        Initialize the Supply Chain Analyzer.
        
        Args:
            io_loader: IODataLoader instance with loaded IO data
        """
        self.io_loader = io_loader
        self.leontief_inverse = None
        self._calculate_leontief_inverse()
    
    def _calculate_leontief_inverse(self):
        """Calculate the Leontief inverse matrix (I - A)^(-1)."""
        try:
            if self.io_loader.input_coefficients is None:
                print("Warning: Input coefficients not available")
                return
            
            # Get the coefficient matrix as numpy array
            A_matrix = self.io_loader.input_coefficients.fillna(0).values
            
            # Diagnostic checks for input coefficient matrix
            print(f"Input coefficient matrix shape: {A_matrix.shape}")
            print(f"A matrix min: {np.min(A_matrix):.6f}, max: {np.max(A_matrix):.6f}")
            print(f"A matrix mean: {np.mean(A_matrix):.6f}")
            
            # Check for negative coefficients (should be rare/zero in input coefficients)
            negative_count = np.sum(A_matrix < 0)
            if negative_count > 0:
                print(f"WARNING: {negative_count} negative input coefficients found")
            
            # Check diagonal elements of A (should be small, typically < 0.5)
            diagonal_A = np.diag(A_matrix)
            max_diag_A = np.max(diagonal_A)
            if max_diag_A > 0.8:
                print(f"WARNING: Large diagonal coefficient in A matrix: {max_diag_A:.3f}")
                print("This could cause Leontief inverse instability")
            
            # Ensure square matrix
            n_rows, n_cols = A_matrix.shape
            matrix_size = min(n_rows, n_cols)
            A_square = A_matrix[:matrix_size, :matrix_size]
            
            # Calculate (I - A)
            I_minus_A = np.eye(matrix_size) - A_square
            
            # Calculate Leontief inverse: (I - A)^(-1)
            try:
                self.leontief_inverse = np.linalg.inv(I_minus_A)
                print(f"Calculated Leontief inverse: {matrix_size}x{matrix_size}")
                
                # Diagnostic checks for economic validity
                diagonal_elements = np.diag(self.leontief_inverse)
                min_diagonal = np.min(diagonal_elements)
                max_diagonal = np.max(diagonal_elements)
                print(f"Leontief diagonal range: {min_diagonal:.3f} to {max_diagonal:.3f}")
                
                # Check if diagonal elements are >= 1 (economic requirement)
                if min_diagonal < 1.0:
                    print(f"WARNING: Diagonal elements below 1.0 detected (min: {min_diagonal:.3f})")
                    print("This suggests issues with the input coefficient matrix")
                
                # Check for negative diagonal elements (major red flag)
                negative_diag_count = sum(1 for x in diagonal_elements if x < 0)
                if negative_diag_count > 0:
                    print(f"CRITICAL ERROR: {negative_diag_count} negative diagonal elements in Leontief inverse!")
                    print("This indicates fundamental problems with input coefficients")
                
            except np.linalg.LinAlgError:
                # Use pseudo-inverse if singular
                self.leontief_inverse = np.linalg.pinv(I_minus_A)
                print(f"Calculated Leontief pseudo-inverse: {matrix_size}x{matrix_size}")
                print("WARNING: Matrix was singular - using pseudo-inverse may cause economic inconsistencies")
                
        except Exception as e:
            print(f"Warning: Could not calculate Leontief inverse: {str(e)}")
            self.leontief_inverse = None
    
    def analyze_demand_reduction_impact(
        self, 
        target_sector: str, 
        reduction_amount: float,
        analysis_type: str = "full"
    ) -> Dict:
        """
        Analyze the impact of demand reduction in a target sector.
        
        Args:
            target_sector: Sector code that reduces its demand
            reduction_amount: Amount of demand reduction (10억원)
            analysis_type: Type of analysis - "direct", "leontief", or "full"
                         - "direct": Direct effects only (immediate suppliers)
                         - "leontief": Indirect/multiplier effects only 
                         - "full": Both direct and indirect effects
            
        Returns:
            Dictionary containing impact analysis results
        """
        results = {
            'target_sector': target_sector,
            'reduction_amount': reduction_amount,
            'analysis_type': analysis_type,
            'target_sector_name': self.io_loader.get_sector_name(target_sector),
            'direct_impacts': {},
            'indirect_impacts': {},
            'leontief_only_impacts': {},
            'total_impacts': {},
            'supply_chain_effects': {}
        }
        
        # Calculate impacts based on analysis type
        if analysis_type == "direct":
            # Direct effects only
            direct_impacts = self._calculate_direct_supply_impacts(target_sector, reduction_amount)
            results['direct_impacts'] = direct_impacts
            results['total_impacts'] = direct_impacts
            
        elif analysis_type == "leontief":
            # Leontief/indirect effects only
            if self.leontief_inverse is not None:
                leontief_only_impacts = self._calculate_leontief_only_impacts(target_sector, reduction_amount)
                results['leontief_only_impacts'] = leontief_only_impacts
                results['total_impacts'] = leontief_only_impacts
            else:
                print("Warning: Leontief inverse not available for indirect analysis")
                results['total_impacts'] = {}
                
        else:  # analysis_type == "full" or default
            # Calculate both direct and indirect impacts
            direct_impacts = self._calculate_direct_supply_impacts(target_sector, reduction_amount)
            results['direct_impacts'] = direct_impacts
            
            if self.leontief_inverse is not None:
                indirect_impacts = self._calculate_indirect_impacts(target_sector, reduction_amount)
                results['indirect_impacts'] = indirect_impacts
                
                # Calculate total impacts (direct + indirect)
                total_impacts = self._combine_impacts(direct_impacts, indirect_impacts)
                results['total_impacts'] = total_impacts
            else:
                print("Warning: Leontief inverse not available, using direct impacts only")
                results['total_impacts'] = direct_impacts
        
        # Analyze supply chain structure
        results['supply_chain_effects'] = self._analyze_supply_chain_structure(target_sector)
        
        return results
    
    def _calculate_direct_supply_impacts(self, target_sector: str, reduction_amount: float) -> Dict[str, float]:
        """
        Calculate direct impacts on suppliers when target sector reduces demand.
        
        Args:
            target_sector: Sector reducing demand
            reduction_amount: Amount of reduction (10억원)
            
        Returns:
            Dictionary of {supplier_sector: impact_amount}
        """
        direct_impacts = {}
        
        # Get backward linkages (what the target sector purchases)
        backward_linkages = self.io_loader.get_backward_linkages(target_sector)
        
        # Filter out accounting totals
        accounting_totals = ['9590', '9519', '9520', '중간투입계', '소계']
        
        for supplier, coefficient in backward_linkages.items():
            # Skip accounting totals
            if any(total in supplier for total in accounting_totals):
                continue
                
            # Calculate reduction in purchases from this supplier
            impact = coefficient * reduction_amount
            direct_impacts[supplier] = -impact  # Negative because it's a reduction
        
        return direct_impacts
    
    def _calculate_indirect_impacts(self, target_sector: str, reduction_amount: float) -> Dict[str, float]:
        """
        Calculate indirect impacts using Leontief multipliers.
        
        Args:
            target_sector: Target sector code
            reduction_amount: Demand change amount
            
        Returns:
            Dictionary of indirect impacts
        """
        indirect_impacts = {}
        
        try:
            # Find sector index
            sector_idx = None
            for i, code in enumerate(self.io_loader.sector_codes):
                if code == target_sector:
                    sector_idx = i
                    break
            
            if sector_idx is None or sector_idx >= self.leontief_inverse.shape[0]:
                return indirect_impacts
            
            # Create demand shock vector
            demand_shock = np.zeros(self.leontief_inverse.shape[0])
            demand_shock[sector_idx] = reduction_amount
            
            # Calculate total output changes
            output_changes = self.leontief_inverse @ demand_shock
            
            # Filter out accounting totals and value-added components
            accounting_totals = ['9590', '9519', '9520', '9790', '중간투입계', '소계', '총투입계']
            value_added_codes = ['9610', '9620', '9621', '9622', '9630', '9640', '9650']  # Value-added components
            
            # Convert to dictionary
            for i, change in enumerate(output_changes):
                if abs(change) > 0.01 and i < len(self.io_loader.sector_codes):  # Threshold for significance
                    sector_code = self.io_loader.sector_codes[i]
                    sector_name = self.io_loader.get_sector_name(sector_code)
                    
                    # Skip accounting totals and value-added components
                    is_accounting_total = (
                        sector_code in accounting_totals or 
                        sector_code in value_added_codes or
                        any(total in sector_code for total in accounting_totals) or
                        any(total in sector_name for total in accounting_totals) or
                        sector_code.startswith('96') or  # All 96xx value-added codes
                        sector_code.startswith('97') or  # All 97xx accounting totals
                        sector_code.startswith('99')     # All 99xx final demand codes
                    )
                    if is_accounting_total:
                        # print(f"DEBUG: Filtering out accounting total: {sector_code}: {sector_name}")
                        continue
                    
                    sector_label = f"{sector_code}: {sector_name}"
                    indirect_impacts[sector_label] = change
                    
            # Check if results make economic sense
            if reduction_amount < 0 and sum(output_changes) > 0:
                print("WARNING: Economic inconsistency detected!")
                print("Negative demand shock producing net positive output changes")
                print("This suggests an error in the Leontief inverse or input coefficients")
            
            return indirect_impacts
            
        except Exception as e:
            print(f"Warning: Could not calculate indirect impacts: {str(e)}")
            return indirect_impacts
    
    def _calculate_leontief_only_impacts(self, target_sector: str, reduction_amount: float) -> Dict[str, float]:
        """
        Calculate only the indirect/multiplier effects from Leontief inverse, excluding direct effects.
        
        Args:
            target_sector: Target sector code
            reduction_amount: Demand change amount
            
        Returns:
            Dictionary of Leontief-only impacts (total - direct)
        """
        leontief_only_impacts = {}
        
        try:
            # Get total impacts from Leontief inverse
            total_impacts = self._calculate_indirect_impacts(target_sector, reduction_amount)
            
            # Get direct impacts
            direct_impacts = self._calculate_direct_supply_impacts(target_sector, reduction_amount)
            
            # Calculate Leontief-only by subtracting direct from total
            for sector, total_impact in total_impacts.items():
                # Extract sector code from "code: name" format
                sector_code = sector.split(':')[0].strip() if ':' in sector else sector
                
                # Find corresponding direct impact using sector code
                direct_impact = direct_impacts.get(sector_code, 0)
                
                # Leontief-only = total - direct
                leontief_impact = total_impact - direct_impact
                if abs(leontief_impact) > 0.01:  # Threshold for significance
                    leontief_only_impacts[sector] = leontief_impact
            
            return leontief_only_impacts
            
        except Exception as e:
            print(f"Warning: Could not calculate Leontief-only impacts: {str(e)}")
            return leontief_only_impacts
    
    def _combine_impacts(self, direct: Dict[str, float], indirect: Dict[str, float]) -> Dict[str, float]:
        """Combine direct and indirect impacts."""
        total_impacts = direct.copy()
        
        for sector, impact in indirect.items():
            if sector in total_impacts:
                total_impacts[sector] += impact
            else:
                total_impacts[sector] = impact
        
        return total_impacts
    
    def _analyze_supply_chain_structure(self, target_sector: str) -> Dict:
        """
        Analyze the supply chain structure of the target sector.
        
        Args:
            target_sector: Target sector code
            
        Returns:
            Dictionary with supply chain analysis
        """
        supply_chain_info = {
            'major_suppliers': {},
            'supplier_concentration': 0.0,
            'import_dependency': {},
            'critical_suppliers': []
        }
        
        # Get backward linkages
        backward_linkages = self.io_loader.get_backward_linkages(target_sector)
        
        if backward_linkages:
            # Sort suppliers by importance
            sorted_suppliers = sorted(backward_linkages.items(), key=lambda x: x[1], reverse=True)
            
            # Top 10 suppliers
            supply_chain_info['major_suppliers'] = dict(sorted_suppliers[:10])
            
            # Calculate concentration (Herfindahl index)
            total_coefficient = sum(backward_linkages.values())
            if total_coefficient > 0:
                concentration = sum((coef / total_coefficient) ** 2 for coef in backward_linkages.values())
                supply_chain_info['supplier_concentration'] = concentration
            
            # Identify critical suppliers (top 20% of coefficients)
            threshold = 0.8 * max(backward_linkages.values()) if backward_linkages.values() else 0
            critical_suppliers = [sector for sector, coef in backward_linkages.items() if coef >= threshold]
            supply_chain_info['critical_suppliers'] = critical_suppliers
        
        return supply_chain_info
    
    def find_affected_supply_chains(
        self, 
        sector_keywords: List[str], 
        reduction_amount: float = 1000
    ) -> Dict[str, Dict]:
        """
        Find and analyze supply chains that would be affected by demand reductions.
        
        Args:
            sector_keywords: List of keywords to search for sectors
            reduction_amount: Hypothetical reduction amount for analysis
            
        Returns:
            Dictionary of sector analyses
        """
        affected_chains = {}
        
        for keyword in sector_keywords:
            matching_sectors = self.io_loader.find_sectors_by_keyword(keyword)
            
            for sector_code, sector_name in matching_sectors:
                analysis = self.analyze_demand_reduction_impact(
                    sector_code, 
                    reduction_amount, 
                    analysis_type="full"
                )
                
                sector_label = f"{sector_code}: {sector_name}"
                affected_chains[sector_label] = analysis
        
        return affected_chains
    
    def analyze_coal_steel_supply_chain(self) -> Dict:
        """
        Specific analysis for coal-steel supply chain impacts.
        Analyzes what happens when steel sector reduces coal consumption.
        
        Returns:
            Dictionary with coal-steel supply chain analysis
        """
        results = {
            'steel_sectors': [],
            'coal_sectors': [],
            'analysis_results': {}
        }
        
        # Find steel-related sectors
        steel_keywords = ['철강', '제철', '선철', '강재', 'steel', 'iron']
        steel_sectors = []
        for keyword in steel_keywords:
            steel_sectors.extend(self.io_loader.find_sectors_by_keyword(keyword))
        
        results['steel_sectors'] = steel_sectors
        
        # Find coal-related sectors
        coal_keywords = ['석탄', '무연탄', '유연탄', 'coal', '코크스', 'coke']
        coal_sectors = []
        for keyword in coal_keywords:
            coal_sectors.extend(self.io_loader.find_sectors_by_keyword(keyword))
        
        results['coal_sectors'] = coal_sectors
        
        # Analyze each steel sector's impact on coal supply chain
        for steel_code, steel_name in steel_sectors:
            steel_analysis = self.analyze_demand_reduction_impact(
                steel_code, 
                1000,  # 1000 billion won reduction
                analysis_type="full"
            )
            
            # Focus on coal-related impacts
            coal_impacts = {}
            for sector, impact in steel_analysis['total_impacts'].items():
                for coal_code, coal_name in coal_sectors:
                    if coal_code in sector:
                        coal_impacts[sector] = impact
                        break
            
            steel_analysis['coal_specific_impacts'] = coal_impacts
            results['analysis_results'][f"{steel_code}: {steel_name}"] = steel_analysis
        
        return results
    
    def get_supply_chain_summary(self, analysis_results: Dict) -> Dict:
        """
        Generate a summary of supply chain analysis results.
        
        Args:
            analysis_results: Results from analyze_demand_reduction_impact
            
        Returns:
            Dictionary with summary statistics
        """
        summary = {
            'target_sector': analysis_results['target_sector'],
            'target_sector_name': analysis_results['target_sector_name'],
            'reduction_amount': analysis_results['reduction_amount'],
            'total_affected_sectors': 0,
            'total_supply_chain_impact': 0,
            'top_affected_suppliers': [],
            'supply_chain_concentration': 0
        }
        
        # Count affected sectors and total impact
        total_impacts = analysis_results.get('total_impacts', {})
        if total_impacts:
            summary['total_affected_sectors'] = len([s for s, impact in total_impacts.items() if abs(impact) > 0.1])
            summary['total_supply_chain_impact'] = sum(abs(impact) for impact in total_impacts.values())
            
            # Top 5 affected suppliers
            sorted_impacts = sorted(total_impacts.items(), key=lambda x: abs(x[1]), reverse=True)
            summary['top_affected_suppliers'] = sorted_impacts[:5]
        
        # Supply chain concentration
        supply_chain_effects = analysis_results.get('supply_chain_effects', {})
        summary['supply_chain_concentration'] = supply_chain_effects.get('supplier_concentration', 0)
        
        return summary