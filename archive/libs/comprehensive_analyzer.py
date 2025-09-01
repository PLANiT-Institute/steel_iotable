import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from .io_data_loader import IODataLoader

class ComprehensiveAnalyzer:
    """
    Comprehensive economic impact analyzer that includes:
    - Value-added impacts
    - Production multipliers 
    - Environmental impact proxies
    - Fiscal impact estimates
    - Regional spillover effects
    """
    
    def __init__(self, io_loader: IODataLoader, basic_io_file: str):
        """
        Initialize the Comprehensive Analyzer.
        
        Args:
            io_loader: IODataLoader instance
            basic_io_file: Path to basic IO file
        """
        self.io_loader = io_loader
        self.basic_io_file = basic_io_file
        
        # Additional multiplier matrices
        self.production_multipliers = None
        self.value_added_multipliers = None
        self.import_multipliers = None
        
        # Environmental and fiscal proxies
        self.co2_intensities = {}
        self.tax_rates = {}
        
        self._load_additional_data()
        self._initialize_proxies()
    
    def _load_additional_data(self):
        """Load production, value-added, and import multipliers."""
        try:
            # Load production multipliers (생산유발계수)
            self.production_multipliers = pd.read_excel(
                self.basic_io_file,
                sheet_name='생산유발계수',
                skiprows=6,
                index_col=[0, 1],
                header=[0, 1]
            )
            print(f"Loaded production multipliers: {self.production_multipliers.shape}")
            
            # Load value-added multipliers (부가가치유발계수)
            self.value_added_multipliers = pd.read_excel(
                self.basic_io_file,
                sheet_name='부가가치유발계수',
                skiprows=6,
                index_col=[0, 1],
                header=[0, 1]
            )
            print(f"Loaded value-added multipliers: {self.value_added_multipliers.shape}")
            
            # Load import multipliers (수입유발계수)
            self.import_multipliers = pd.read_excel(
                self.basic_io_file,
                sheet_name='수입유발계수',
                skiprows=6,
                index_col=[0, 1],
                header=[0, 1]
            )
            print(f"Loaded import multipliers: {self.import_multipliers.shape}")
            
        except Exception as e:
            print(f"Warning: Could not load additional multipliers: {str(e)}")
    
    def _initialize_proxies(self):
        """Initialize environmental and fiscal impact proxies."""
        # CO2 intensity estimates (tons CO2 per billion won of output)
        # These are rough estimates based on sector characteristics
        self.co2_intensities = {
            # Energy sectors
            '1610': 2500,  # Coal products - high intensity
            '1920': 800,   # Petroleum products
            '3510': 1200,  # Electric power
            
            # Heavy industry
            '2410': 1800,  # Basic chemicals
            '2711': 3000,  # Pig iron - very high
            '2721': 2200,  # Steel products
            '2610': 1500,  # Cement
            
            # Light industry
            '1110': 200,   # Food products
            '1310': 150,   # Textiles
            '1810': 100,   # Paper products
            
            # Services
            '4610': 50,    # Wholesale trade
            '4910': 300,   # Transportation
            '6410': 20,    # Financial services
        }
        
        # Tax rates (effective tax rate as % of value added)
        self.tax_rates = {
            # Manufacturing generally has moderate tax rates
            'manufacturing': 0.15,
            # Services typically lower
            'services': 0.12,
            # Mining and energy often have higher rates
            'mining_energy': 0.20,
            # Default rate
            'default': 0.13
        }
    
    def analyze_value_added_impact(
        self,
        target_sector: str,
        demand_change: float
    ) -> Dict:
        """
        Analyze value-added impacts from demand change.
        
        Args:
            target_sector: Target sector code
            demand_change: Demand change amount (10억원)
            
        Returns:
            Dictionary with value-added impact analysis
        """
        results = {
            'target_sector': target_sector,
            'demand_change': demand_change,
            'sectoral_value_added': {},
            'total_value_added_impact': 0,
            'value_added_multiplier': 0,
            'gdp_impact': 0
        }
        
        if self.value_added_multipliers is None:
            return results
        
        try:
            # Find sector in value-added multipliers
            target_found = False
            for i, idx in enumerate(self.value_added_multipliers.index):
                if isinstance(idx, tuple) and str(idx[0]) == str(target_sector):
                    # Get value-added coefficients for this sector
                    va_coefficients = self.value_added_multipliers.iloc[i, :]
                    
                    for j, col in enumerate(self.value_added_multipliers.columns):
                        if isinstance(col, tuple):
                            affected_sector_code = str(col[0])
                            coefficient = float(va_coefficients.iloc[j])
                            
                            if abs(coefficient) > 0.001:  # Threshold for significance
                                va_impact = demand_change * coefficient
                                sector_name = self.io_loader.get_sector_name(affected_sector_code)
                                sector_label = f"{affected_sector_code}: {sector_name}"
                                results['sectoral_value_added'][sector_label] = va_impact
                                results['total_value_added_impact'] += va_impact
                    
                    target_found = True
                    break
            
            if not target_found:
                print(f"Warning: Sector {target_sector} not found in value-added multipliers")
            
            # Calculate multiplier and GDP impact
            if demand_change != 0:
                results['value_added_multiplier'] = results['total_value_added_impact'] / demand_change
            
            # GDP impact is approximately equal to value-added impact
            results['gdp_impact'] = results['total_value_added_impact']
            
        except Exception as e:
            print(f"Warning: Error calculating value-added impact: {str(e)}")
        
        return results
    
    def analyze_production_impact(
        self,
        target_sector: str,
        demand_change: float
    ) -> Dict:
        """
        Analyze production impacts using production multipliers.
        
        Args:
            target_sector: Target sector code
            demand_change: Demand change amount (10억원)
            
        Returns:
            Dictionary with production impact analysis
        """
        results = {
            'target_sector': target_sector,
            'demand_change': demand_change,
            'sectoral_production': {},
            'total_production_impact': 0,
            'production_multiplier': 0
        }
        
        if self.production_multipliers is None:
            return results
        
        try:
            # Find sector in production multipliers
            for i, idx in enumerate(self.production_multipliers.index):
                if isinstance(idx, tuple) and str(idx[0]) == str(target_sector):
                    prod_coefficients = self.production_multipliers.iloc[i, :]
                    
                    for j, col in enumerate(self.production_multipliers.columns):
                        if isinstance(col, tuple):
                            affected_sector_code = str(col[0])
                            coefficient = float(prod_coefficients.iloc[j])
                            
                            if abs(coefficient) > 0.001:
                                prod_impact = demand_change * coefficient
                                sector_name = self.io_loader.get_sector_name(affected_sector_code)
                                sector_label = f"{affected_sector_code}: {sector_name}"
                                results['sectoral_production'][sector_label] = prod_impact
                                results['total_production_impact'] += abs(prod_impact)
                    break
            
            if demand_change != 0:
                results['production_multiplier'] = results['total_production_impact'] / abs(demand_change)
            
        except Exception as e:
            print(f"Warning: Error calculating production impact: {str(e)}")
        
        return results
    
    def analyze_environmental_impact(
        self,
        sectoral_production: Dict[str, float]
    ) -> Dict:
        """
        Estimate environmental impacts using CO2 intensity proxies.
        
        Args:
            sectoral_production: Production impacts by sector
            
        Returns:
            Dictionary with environmental impact estimates
        """
        results = {
            'sectoral_co2_impact': {},
            'total_co2_impact': 0,
            'high_carbon_sectors': [],
            'environmental_summary': {}
        }
        
        total_co2 = 0
        
        for sector_label, production_change in sectoral_production.items():
            # Extract sector code
            sector_code = sector_label.split(':')[0].strip()
            
            # Get CO2 intensity (use default if not found)
            co2_intensity = self.co2_intensities.get(sector_code, 300)  # Default 300 tons/billion won
            
            # Calculate CO2 impact
            co2_impact = abs(production_change) * co2_intensity / 1000  # Convert to thousand tons
            
            if co2_impact > 0.1:  # Threshold for significance
                results['sectoral_co2_impact'][sector_label] = co2_impact
                total_co2 += co2_impact
                
                # Identify high-carbon sectors
                if co2_intensity > 1000:
                    results['high_carbon_sectors'].append(sector_label)
        
        results['total_co2_impact'] = total_co2
        
        # Environmental summary
        results['environmental_summary'] = {
            'total_co2_thousand_tons': total_co2,
            'equivalent_car_years': total_co2 * 1000 / 4.6,  # Avg car emits 4.6 tons CO2/year
            'high_impact_sectors': len(results['high_carbon_sectors']),
            'sectors_analyzed': len(results['sectoral_co2_impact'])
        }
        
        return results
    
    def analyze_fiscal_impact(
        self,
        sectoral_value_added: Dict[str, float]
    ) -> Dict:
        """
        Estimate fiscal impacts (tax revenue changes).
        
        Args:
            sectoral_value_added: Value-added impacts by sector
            
        Returns:
            Dictionary with fiscal impact estimates
        """
        results = {
            'sectoral_tax_impact': {},
            'total_tax_impact': 0,
            'income_tax_impact': 0,
            'corporate_tax_impact': 0,
            'indirect_tax_impact': 0
        }
        
        total_tax = 0
        
        for sector_label, va_change in sectoral_value_added.items():
            # Extract sector code for tax rate determination
            sector_code = sector_label.split(':')[0].strip()
            
            # Determine tax rate based on sector
            if sector_code.startswith('1') or sector_code.startswith('2'):
                tax_rate = self.tax_rates['manufacturing']
            elif sector_code.startswith('0'):
                tax_rate = self.tax_rates['mining_energy']
            elif int(sector_code[0]) >= 4:
                tax_rate = self.tax_rates['services']
            else:
                tax_rate = self.tax_rates['default']
            
            # Calculate tax impact
            tax_impact = va_change * tax_rate
            
            if abs(tax_impact) > 0.1:  # Threshold for significance
                results['sectoral_tax_impact'][sector_label] = tax_impact
                total_tax += tax_impact
        
        results['total_tax_impact'] = total_tax
        
        # Breakdown by tax type (rough estimates)
        results['income_tax_impact'] = total_tax * 0.4  # ~40% from income taxes
        results['corporate_tax_impact'] = total_tax * 0.3  # ~30% from corporate taxes
        results['indirect_tax_impact'] = total_tax * 0.3  # ~30% from indirect taxes
        
        return results
    
    def analyze_regional_spillovers(
        self,
        target_sector: str,
        demand_change: float
    ) -> Dict:
        """
        Estimate regional spillover effects.
        This is a simplified approach using sector characteristics.
        
        Args:
            target_sector: Target sector code
            demand_change: Demand change amount
            
        Returns:
            Dictionary with regional spillover estimates
        """
        results = {
            'target_sector': target_sector,
            'demand_change': demand_change,
            'regional_effects': {},
            'concentration_index': 0,
            'spillover_potential': 'medium'
        }
        
        # Sector characteristics for regional analysis
        sector_characteristics = {
            # High concentration sectors (few regions)
            'high_concentration': ['2711', '2721', '1610', '2610'],  # Steel, coal, cement
            # Medium concentration
            'medium_concentration': ['2410', '1920', '1810'],  # Chemicals, petroleum, paper
            # Low concentration (dispersed)
            'low_concentration': ['1110', '4610', '6410']  # Food, trade, finance
        }
        
        # Determine concentration level
        concentration_level = 'medium'  # default
        for level, sectors in sector_characteristics.items():
            if target_sector in sectors:
                concentration_level = level.split('_')[0]
                break
        
        # Estimate regional distribution based on concentration
        if concentration_level == 'high':
            # Highly concentrated sectors affect few regions strongly
            regional_distribution = {
                '수도권': 0.3,
                '충청권': 0.25,
                '경상권': 0.3,
                '전라권': 0.1,
                '기타': 0.05
            }
            results['concentration_index'] = 0.8
            results['spillover_potential'] = 'low'
            
        elif concentration_level == 'low':
            # Dispersed sectors affect many regions moderately
            regional_distribution = {
                '수도권': 0.4,
                '충청권': 0.15,
                '경상권': 0.25,
                '전라권': 0.15,
                '기타': 0.05
            }
            results['concentration_index'] = 0.3
            results['spillover_potential'] = 'high'
            
        else:  # medium
            regional_distribution = {
                '수도권': 0.35,
                '충청권': 0.2,
                '경상권': 0.25,
                '전라권': 0.15,
                '기타': 0.05
            }
            results['concentration_index'] = 0.5
            results['spillover_potential'] = 'medium'
        
        # Calculate regional effects
        for region, share in regional_distribution.items():
            regional_impact = demand_change * share
            if abs(regional_impact) > 1:  # Threshold
                results['regional_effects'][region] = regional_impact
        
        return results
    
    def comprehensive_analysis(
        self,
        target_sector: str,
        demand_change: float
    ) -> Dict:
        """
        Run comprehensive analysis including all impact types.
        
        Args:
            target_sector: Target sector code
            demand_change: Demand change amount (10억원)
            
        Returns:
            Dictionary with comprehensive analysis results
        """
        results = {
            'target_sector': target_sector,
            'target_sector_name': self.io_loader.get_sector_name(target_sector),
            'demand_change': demand_change,
            'value_added_analysis': {},
            'production_analysis': {},
            'environmental_analysis': {},
            'fiscal_analysis': {},
            'regional_analysis': {},
            'comprehensive_summary': {}
        }
        
        print(f"Running comprehensive analysis for sector {target_sector}...")
        
        # 1. Value-added impact
        print("1. Analyzing value-added impacts...")
        va_analysis = self.analyze_value_added_impact(target_sector, demand_change)
        results['value_added_analysis'] = va_analysis
        
        # 2. Production impact
        print("2. Analyzing production impacts...")
        prod_analysis = self.analyze_production_impact(target_sector, demand_change)
        results['production_analysis'] = prod_analysis
        
        # 3. Environmental impact
        print("3. Estimating environmental impacts...")
        env_analysis = self.analyze_environmental_impact(
            prod_analysis.get('sectoral_production', {})
        )
        results['environmental_analysis'] = env_analysis
        
        # 4. Fiscal impact
        print("4. Estimating fiscal impacts...")
        fiscal_analysis = self.analyze_fiscal_impact(
            va_analysis.get('sectoral_value_added', {})
        )
        results['fiscal_analysis'] = fiscal_analysis
        
        # 5. Regional spillovers
        print("5. Analyzing regional spillovers...")
        regional_analysis = self.analyze_regional_spillovers(target_sector, demand_change)
        results['regional_analysis'] = regional_analysis
        
        # 6. Comprehensive summary
        results['comprehensive_summary'] = self._create_comprehensive_summary(results)
        
        return results
    
    def _create_comprehensive_summary(self, analysis_results: Dict) -> Dict:
        """Create comprehensive summary of all analyses."""
        summary = {
            'economic_multipliers': {},
            'environmental_impact': {},
            'fiscal_impact': {},
            'regional_distribution': {},
            'overall_assessment': {}
        }
        
        # Economic multipliers
        va_analysis = analysis_results.get('value_added_analysis', {})
        prod_analysis = analysis_results.get('production_analysis', {})
        
        summary['economic_multipliers'] = {
            'value_added_multiplier': va_analysis.get('value_added_multiplier', 0),
            'production_multiplier': prod_analysis.get('production_multiplier', 0),
            'gdp_impact': va_analysis.get('gdp_impact', 0)
        }
        
        # Environmental summary
        env_analysis = analysis_results.get('environmental_analysis', {})
        env_summary = env_analysis.get('environmental_summary', {})
        
        summary['environmental_impact'] = {
            'total_co2_impact': env_summary.get('total_co2_thousand_tons', 0),
            'car_equivalent_years': env_summary.get('equivalent_car_years', 0),
            'high_carbon_sectors': env_summary.get('high_impact_sectors', 0)
        }
        
        # Fiscal summary
        fiscal_analysis = analysis_results.get('fiscal_analysis', {})
        summary['fiscal_impact'] = {
            'total_tax_impact': fiscal_analysis.get('total_tax_impact', 0),
            'income_tax': fiscal_analysis.get('income_tax_impact', 0),
            'corporate_tax': fiscal_analysis.get('corporate_tax_impact', 0)
        }
        
        # Regional summary
        regional_analysis = analysis_results.get('regional_analysis', {})
        summary['regional_distribution'] = {
            'concentration_index': regional_analysis.get('concentration_index', 0),
            'spillover_potential': regional_analysis.get('spillover_potential', 'medium'),
            'regions_affected': len(regional_analysis.get('regional_effects', {}))
        }
        
        # Overall assessment
        demand_change = analysis_results.get('demand_change', 1)
        summary['overall_assessment'] = {
            'impact_magnitude': 'high' if abs(summary['economic_multipliers']['gdp_impact']) > abs(demand_change) * 1.5 else 'medium',
            'environmental_concern': 'high' if summary['environmental_impact']['total_co2_impact'] > 100 else 'low',
            'fiscal_significance': 'high' if abs(summary['fiscal_impact']['total_tax_impact']) > abs(demand_change) * 0.1 else 'low'
        }
        
        return summary
    
    def is_data_available(self) -> bool:
        """Check if comprehensive analysis data is available."""
        return (self.production_multipliers is not None and 
                self.value_added_multipliers is not None)
    
    def get_data_info(self) -> Dict:
        """Get information about available data for comprehensive analysis."""
        return {
            'production_multipliers_loaded': self.production_multipliers is not None,
            'value_added_multipliers_loaded': self.value_added_multipliers is not None,
            'import_multipliers_loaded': self.import_multipliers is not None,
            'co2_intensities_available': len(self.co2_intensities),
            'tax_rates_available': len(self.tax_rates),
            'production_multipliers_shape': self.production_multipliers.shape if self.production_multipliers is not None else None,
            'value_added_multipliers_shape': self.value_added_multipliers.shape if self.value_added_multipliers is not None else None
        }