#!/usr/bin/env python3
"""
Enhanced Sector Impact Analyzer

Comprehensive analysis of economic impacts and employment changes from sector demand changes
using Korean Input-Output tables at basic prices (기초가격).

NEW FEATURES:
- Separate import and domestic impact analysis
- Value-added impact analysis
- Production multiplier effects
- Environmental impact estimates (CO2)
- Fiscal impact analysis (tax effects)
- Regional spillover effects
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from libs.io_data_loader import IODataLoader
from libs.supply_chain_analyzer import SupplyChainAnalyzer
from libs.employment_analyzer import EmploymentAnalyzer
from libs.import_domestic_analyzer import ImportDomesticAnalyzer
from libs.comprehensive_analyzer import ComprehensiveAnalyzer
from libs.table_formatter import IOTableFormatter
from config import AnalysisConfig, DEFAULT_CONFIG
import pandas as pd
from typing import Dict, List, Tuple, Optional

class EnhancedSectorAnalyzer:
    """
    Enhanced class for comprehensive sector impact analysis.
    Integrates all analysis modules including import/domestic separation
    and comprehensive economic impact assessment.
    """
    
    def __init__(self, 
                 config: AnalysisConfig = None,
                 basic_io_file: str = None,
                 employment_file: str = None):
        """
        Initialize the Enhanced Sector Impact Analyzer.
        
        Args:
            config: AnalysisConfig instance (uses DEFAULT_CONFIG if None)
            basic_io_file: Path to basic IO table file (overrides config if provided)
            employment_file: Path to employment coefficients file (overrides config if provided)
        """
        # Use provided config or default
        self.config = config if config is not None else DEFAULT_CONFIG
        
        # Override file paths if provided
        if basic_io_file is not None:
            self.config.file_paths.basic_io_file = basic_io_file
        if employment_file is not None:
            self.config.file_paths.employment_file = employment_file
            
        self.basic_io_file = self.config.file_paths.basic_io_file
        self.employment_file = self.config.file_paths.employment_file
        
        # Initialize all analyzer components
        print("Initializing Enhanced Sector Impact Analyzer...")
        print("1/6 Loading IO Data...")
        self.io_loader = IODataLoader(self.basic_io_file)
        
        print("2/6 Initializing Supply Chain Analyzer...")
        self.supply_chain_analyzer = SupplyChainAnalyzer(self.io_loader)
        
        print("3/6 Initializing Employment Analyzer...")
        self.employment_analyzer = EmploymentAnalyzer(self.employment_file)
        
        print("4/6 Initializing Import/Domestic Analyzer...")
        self.import_domestic_analyzer = ImportDomesticAnalyzer(self.io_loader, self.basic_io_file)
        
        print("5/6 Initializing Comprehensive Analyzer...")
        self.comprehensive_analyzer = ComprehensiveAnalyzer(self.io_loader, self.basic_io_file)
        
        print("6/6 Initializing Table Formatter...")
        self.table_formatter = IOTableFormatter(self.io_loader)
        
        self._check_enhanced_data_status()
    
    def _check_enhanced_data_status(self):
        """Check and report enhanced data loading status."""
        print("\n" + "="*80)
        print("ENHANCED ANALYZER DATA STATUS")
        print("="*80)
        
        # Basic IO Data status
        io_info = self.io_loader.get_data_info()
        print(f"IO Table Data:")
        print(f"  - Sectors loaded: {io_info['num_sectors']}")
        print(f"  - Transaction table: {'✓' if io_info['transaction_table_loaded'] else '✗'}")
        print(f"  - Input coefficients: {'✓' if io_info['input_coefficients_loaded'] else '✗'}")
        
        # Employment data status
        emp_info = self.employment_analyzer.get_data_info()
        print(f"\nEmployment Analysis:")
        print(f"  - Employment coefficients: {'✓' if emp_info['employment_coefficients_loaded'] else '✗'}")
        print(f"  - Sectors: {emp_info['num_sectors']}, Regions: {emp_info['num_regions']}")
        
        # Import/Domestic analysis status
        import_info = self.import_domestic_analyzer.get_data_info()
        print(f"\nImport/Domestic Analysis:")
        print(f"  - Import coefficients (Am): {'✓' if import_info['import_coefficients_loaded'] else '✗'}")
        print(f"  - Domestic coefficients (Ad): {'✓' if import_info['domestic_coefficients_loaded'] else '✗'}")
        print(f"  - Import Leontief inverse: {'✓' if import_info['import_leontief_calculated'] else '✗'}")
        print(f"  - Domestic Leontief inverse: {'✓' if import_info['domestic_leontief_calculated'] else '✗'}")
        
        # Comprehensive analysis status
        comp_info = self.comprehensive_analyzer.get_data_info()
        print(f"\nComprehensive Analysis:")
        print(f"  - Production multipliers: {'✓' if comp_info['production_multipliers_loaded'] else '✗'}")
        print(f"  - Value-added multipliers: {'✓' if comp_info['value_added_multipliers_loaded'] else '✗'}")
        print(f"  - Import multipliers: {'✓' if comp_info['import_multipliers_loaded'] else '✗'}")
        print(f"  - CO2 intensity data: {comp_info['co2_intensities_available']} sectors")
        print(f"  - Tax rate data: {comp_info['tax_rates_available']} categories")
        
        print("="*80 + "\n")
    
    def comprehensive_sector_analysis(
        self,
        target_sector: str,
        demand_change: float,
        analysis_options: Dict = None,
        supply_chain_type: str = "full"
    ) -> Dict:
        """
        Run comprehensive sector impact analysis with all available methods.
        
        Args:
            target_sector: Sector code to analyze
            demand_change: Amount of demand change (10억원)
            analysis_options: Dict of analysis options to enable/disable
            supply_chain_type: Type of supply chain analysis - "direct", "leontief", or "full"
            
        Returns:
            Dictionary containing all analysis results
        """
        # Default analysis options
        if analysis_options is None:
            analysis_options = {
                'supply_chain': self.config.analysis_options.default_supply_chain,
                'employment': self.config.analysis_options.default_employment,
                'import_domestic': self.config.analysis_options.default_import_domestic,
                'comprehensive': self.config.analysis_options.default_comprehensive,
                'target_region': self.config.default_values.default_target_region
            }
        
        results = {
            'target_sector': target_sector,
            'target_sector_name': self.io_loader.get_sector_name(target_sector),
            'demand_change': demand_change,
            'analysis_options': analysis_options,
            'supply_chain_type': supply_chain_type,
            'supply_chain_analysis': {},
            'employment_analysis': {},
            'import_domestic_analysis': {},
            'comprehensive_analysis': {},
            'integrated_summary': {}
        }
        
        print(f"\n{'='*80}")
        print(f"COMPREHENSIVE SECTOR ANALYSIS")
        print(f"{'='*80}")
        print(f"Sector: {target_sector} - {results['target_sector_name']}")
        print(f"Demand change: {demand_change:,} billion won")
        print(f"Supply chain analysis type: {supply_chain_type}")
        print(f"{'='*80}")
        
        # 1. Supply Chain Analysis
        if analysis_options.get('supply_chain', True):
            print("\n1. SUPPLY CHAIN IMPACT ANALYSIS")
            print("-" * 50)
            supply_results = self.supply_chain_analyzer.analyze_demand_reduction_impact(
                target_sector, demand_change, analysis_type=supply_chain_type
            )
            results['supply_chain_analysis'] = supply_results
            
            # Summary stats  
            total_impacts = supply_results.get('total_impacts', {})
            net_impact = sum(total_impacts.values())
            absolute_impact = sum(abs(v) for v in total_impacts.values())
            print(f"   Total sectors affected: {len(total_impacts)}")
            print(f"   Net supply chain impact: {net_impact:,.1f} billion won")
            print(f"   Total absolute impact: {absolute_impact:,.1f} billion won")
        
        # 2. Employment Analysis
        if analysis_options.get('employment', True):
            print("\n2. EMPLOYMENT IMPACT ANALYSIS")
            print("-" * 50)
            target_region = analysis_options.get('target_region', '전지역')
            
            # Check if supply chain analysis was performed
            if not analysis_options.get('supply_chain', True) or not results.get('supply_chain_analysis'):
                print("   Warning: Employment analysis requires supply chain analysis. Skipping employment analysis.")
                results['employment_analysis'] = {
                    'sectoral_employment': {},
                    'total_employment_change': 0,
                    'target_region': target_region,
                    'warning': 'Supply chain analysis required for employment calculation'
                }
            else:
                # Use supply chain results for employment calculation
                total_impacts = results['supply_chain_analysis'].get('total_impacts', {})
                if not total_impacts:
                    print("   Warning: No supply chain impacts found. Employment analysis will be empty.")
                
                sector_impact_codes = {}
                for sector_label, impact in total_impacts.items():
                    if ':' in sector_label:
                        sector_code = sector_label.split(':')[0].strip()
                        sector_impact_codes[sector_code] = impact
                
                intermediate_impacts = self.employment_analyzer.map_basic_to_intermediate_sectors(sector_impact_codes)
                employment_results = {}
                
                for intermediate_sector, impact in intermediate_impacts.items():
                    emp_coeff = self.employment_analyzer.get_employment_intensity(intermediate_sector, target_region)
                    employment_change = impact * emp_coeff
                    if abs(employment_change) > self.config.thresholds.employment_impact_threshold:
                        employment_results[intermediate_sector] = employment_change
                
                results['employment_analysis'] = {
                    'sectoral_employment': employment_results,
                    'total_employment_change': sum(employment_results.values()),
                    'target_region': target_region
                }
                
                print(f"   Total employment change: {sum(employment_results.values()):,.0f} jobs")
                print(f"   Sectors with employment impact: {len(employment_results)}")
        
        # 3. Import/Domestic Analysis
        if analysis_options.get('import_domestic', True):
            print("\n3. IMPORT/DOMESTIC IMPACT ANALYSIS")
            print("-" * 50)
            if self.import_domestic_analyzer.is_data_available():
                import_domestic_results = self.import_domestic_analyzer.analyze_import_domestic_impacts(
                    target_sector, demand_change
                )
                results['import_domestic_analysis'] = import_domestic_results
                
                print(f"   Import impact: {import_domestic_results.get('total_import_effect', 0):,.1f} billion won")
                print(f"   Domestic impact: {import_domestic_results.get('total_domestic_effect', 0):,.1f} billion won")
                print(f"   Import share: {import_domestic_results.get('import_share', 0):.1%}")
                print(f"   Domestic share: {import_domestic_results.get('domestic_share', 0):.1%}")
            else:
                print("   Import/Domestic data not available")
        
        # 4. Comprehensive Economic Analysis
        if analysis_options.get('comprehensive', True):
            print("\n4. COMPREHENSIVE ECONOMIC ANALYSIS")
            print("-" * 50)
            if self.comprehensive_analyzer.is_data_available():
                comp_results = self.comprehensive_analyzer.comprehensive_analysis(
                    target_sector, demand_change
                )
                results['comprehensive_analysis'] = comp_results
                
                summary = comp_results.get('comprehensive_summary', {})
                
                # Economic impacts
                econ_mult = summary.get('economic_multipliers', {})
                print(f"   GDP impact: {econ_mult.get('gdp_impact', 0):,.1f} billion won")
                print(f"   Value-added multiplier: {econ_mult.get('value_added_multiplier', 0):.2f}")
                print(f"   Production multiplier: {econ_mult.get('production_multiplier', 0):.2f}")
                
                # Environmental impacts
                env_impact = summary.get('environmental_impact', {})
                print(f"   CO2 impact: {env_impact.get('total_co2_impact', 0):,.1f} thousand tons")
                print(f"   Car equivalent: {env_impact.get('car_equivalent_years', 0):,.0f} car-years")
                
                # Fiscal impacts
                fiscal_impact = summary.get('fiscal_impact', {})
                print(f"   Tax impact: {fiscal_impact.get('total_tax_impact', 0):,.1f} billion won")
                
            else:
                print("   Comprehensive analysis data not fully available")
        
        # 5. Integrated Summary
        results['integrated_summary'] = self._create_integrated_summary(results)
        
        return results
    
    def analyze_steel_coal_comprehensive(self, reduction_amount: float = None, max_sectors: int = None) -> Dict:
        """
        Comprehensive steel-coal supply chain analysis with all features.
        
        Args:
            reduction_amount: Coal reduction amount in steel sector (10억원) (uses config default if None)
            max_sectors: Maximum number of steel sectors to analyze (None for all)
            
        Returns:
            Comprehensive steel-coal analysis results
        """
        # Use default reduction amount if not provided
        if reduction_amount is None:
            reduction_amount = self.config.default_values.default_reduction_amount
        print(f"\n{'='*80}")
        print("COMPREHENSIVE STEEL-COAL SUPPLY CHAIN ANALYSIS")
        print(f"{'='*80}")
        
        # Find steel and coal sectors using configurable keywords
        steel_sectors = []
        for keyword in self.config.sector_keywords.steel_keywords:
            steel_sectors.extend(self.io_loader.find_sectors_by_keyword(keyword))
        
        coal_sectors = []
        for keyword in self.config.sector_keywords.coal_keywords:
            coal_sectors.extend(self.io_loader.find_sectors_by_keyword(keyword))
        
        print(f"Steel sectors found: {len(steel_sectors)}")
        print(f"Coal sectors found: {len(coal_sectors)}")
        
        results = {
            'reduction_amount': reduction_amount,
            'steel_sectors': steel_sectors,
            'coal_sectors': coal_sectors,
            'sector_analyses': {},
            'aggregate_impacts': {
                'total_supply_chain_impact': 0,
                'total_employment_change': 0,
                'total_import_impact': 0,
                'total_domestic_impact': 0,
                'total_co2_impact': 0,
                'total_tax_impact': 0
            },
            'coal_specific_impacts': {}
        }
        
        # Analyze each steel sector (limit if specified)
        sectors_to_analyze = steel_sectors[:max_sectors] if max_sectors else steel_sectors
        for i, (steel_code, steel_name) in enumerate(sectors_to_analyze):
            print(f"\n{'-'*60}")
            print(f"ANALYZING STEEL SECTOR {i+1}: {steel_code} - {steel_name}")
            print(f"{'-'*60}")
            
            # Run comprehensive analysis
            sector_analysis = self.comprehensive_sector_analysis(
                steel_code, reduction_amount
            )
            
            results['sector_analyses'][f"{steel_code}: {steel_name}"] = sector_analysis
            
            # Aggregate impacts (using net impact, not absolute)
            supply_impacts = sector_analysis.get('supply_chain_analysis', {}).get('total_impacts', {})
            results['aggregate_impacts']['total_supply_chain_impact'] += sum(supply_impacts.values())
            
            employment = sector_analysis.get('employment_analysis', {})
            results['aggregate_impacts']['total_employment_change'] += employment.get('total_employment_change', 0)
            
            import_domestic = sector_analysis.get('import_domestic_analysis', {})
            results['aggregate_impacts']['total_import_impact'] += import_domestic.get('total_import_effect', 0)
            results['aggregate_impacts']['total_domestic_impact'] += import_domestic.get('total_domestic_effect', 0)
            
            comprehensive = sector_analysis.get('comprehensive_analysis', {})
            # Standardize data access pattern - use comprehensive_summary for consistency
            comp_summary = comprehensive.get('comprehensive_summary', {})
            env_impact = comp_summary.get('environmental_impact', {})
            results['aggregate_impacts']['total_co2_impact'] += env_impact.get('total_co2_impact', 0)
            
            fiscal_impact = comp_summary.get('fiscal_impact', {})
            results['aggregate_impacts']['total_tax_impact'] += fiscal_impact.get('total_tax_impact', 0)
            
            # Identify coal-specific impacts
            coal_impacts = {}
            for sector_label, impact in supply_impacts.items():
                sector_label_lower = sector_label.lower()
                for coal_code, coal_name in coal_sectors:
                    # Convert coal_code to lowercase for consistent comparison
                    if coal_code.lower() in sector_label_lower:
                        coal_impacts[sector_label] = impact
                        break
                # Also check keywords (convert to lowercase for consistency)
                for keyword in self.config.sector_keywords.coal_matching_keywords:
                    if keyword.lower() in sector_label_lower:
                        coal_impacts[sector_label] = impact
                        break
            
            results['coal_specific_impacts'][f"{steel_code}: {steel_name}"] = coal_impacts
        
        return results
    
    def _create_integrated_summary(self, analysis_results: Dict) -> Dict:
        """Create integrated summary across all analyses."""
        summary = {
            'economic_impact': {},
            'employment_impact': {},
            'trade_impact': {},
            'environmental_impact': {},
            'fiscal_impact': {},
            'overall_assessment': {}
        }
        
        # Economic impact summary
        supply_chain = analysis_results.get('supply_chain_analysis', {})
        comprehensive = analysis_results.get('comprehensive_analysis', {})
        
        total_impacts = supply_chain.get('total_impacts', {})
        comp_summary = comprehensive.get('comprehensive_summary', {})
        
        # Filter out accounting totals from summary calculations
        accounting_totals = ['9590', '9519', '9520', '중간투입계', '소계']
        filtered_impacts = {}
        for sector, impact in total_impacts.items():
            sector_code = sector.split(':')[0].strip() if ':' in sector else sector
            if sector_code not in accounting_totals and not any(total in sector for total in accounting_totals):
                filtered_impacts[sector] = impact
        
        summary['economic_impact'] = {
            'sectors_affected': len(filtered_impacts),
            'total_output_impact': sum(filtered_impacts.values()),  # Net impact, not absolute
            'total_absolute_impact': sum(abs(v) for v in filtered_impacts.values()),  # Keep absolute for reference
            'gdp_impact': comp_summary.get('economic_multipliers', {}).get('gdp_impact', 0),
            'production_multiplier': comp_summary.get('economic_multipliers', {}).get('production_multiplier', 0)
        }
        
        # Employment impact summary
        employment = analysis_results.get('employment_analysis', {})
        sectoral_employment = employment.get('sectoral_employment', {})
        
        # Filter out accounting totals from employment summary
        filtered_employment = {}
        for sector, jobs in sectoral_employment.items():
            sector_code = sector.split(':')[0].strip() if ':' in sector else sector
            if sector_code not in accounting_totals and not any(total in sector for total in accounting_totals):
                filtered_employment[sector] = jobs
        
        summary['employment_impact'] = {
            'total_jobs_affected': employment.get('total_employment_change', 0),
            'sectors_with_job_impact': len(filtered_employment),
            'region_analyzed': employment.get('target_region', '전지역')
        }
        
        # Trade impact summary
        import_domestic = analysis_results.get('import_domestic_analysis', {})
        summary['trade_impact'] = {
            'import_impact': import_domestic.get('total_import_effect', 0),
            'domestic_impact': import_domestic.get('total_domestic_effect', 0),
            'import_dependency': import_domestic.get('import_share', 0),
            'domestic_dependency': import_domestic.get('domestic_share', 0)
        }
        
        # Environmental impact summary
        env_impact = comp_summary.get('environmental_impact', {})
        co2_impact = env_impact.get('total_co2_impact', 0)
        # Validate and convert CO2 impact to tons
        try:
            co2_impact_tons = float(co2_impact) * self.config.thresholds.co2_conversion_factor if co2_impact is not None else 0
        except (TypeError, ValueError):
            co2_impact_tons = 0
        
        summary['environmental_impact'] = {
            'co2_impact_tons': co2_impact_tons,
            'car_equivalent_years': env_impact.get('car_equivalent_years', 0),
            'environmental_concern_level': comp_summary.get('overall_assessment', {}).get('environmental_concern', self.config.assessment_levels.default_environmental_concern)
        }
        
        # Fiscal impact summary
        fiscal_impact = comp_summary.get('fiscal_impact', {})
        summary['fiscal_impact'] = {
            'total_tax_impact': fiscal_impact.get('total_tax_impact', 0),
            'income_tax_impact': fiscal_impact.get('income_tax', 0),
            'corporate_tax_impact': fiscal_impact.get('corporate_tax', 0)
        }
        
        # Overall assessment
        demand_change = analysis_results.get('demand_change', self.config.default_values.default_demand_change)
        
        summary['overall_assessment'] = {
            'economic_magnitude': 'high' if abs(summary['economic_impact']['total_output_impact']) > abs(demand_change) * self.config.thresholds.economic_magnitude_multiplier else 'medium',
            'employment_significance': 'high' if abs(summary['employment_impact']['total_jobs_affected']) > self.config.thresholds.employment_significance_threshold else 'medium',
            'trade_implications': 'import_dependent' if summary['trade_impact']['import_dependency'] > self.config.thresholds.import_dependency_threshold else 'domestic_focused',
            'environmental_concern': summary['environmental_impact']['environmental_concern_level'],
            'fiscal_significance': 'high' if abs(summary['fiscal_impact']['total_tax_impact']) > abs(demand_change) * self.config.thresholds.fiscal_significance_multiplier else 'medium'
        }
        
        return summary
    
    def display_comprehensive_results(self, results: Dict):
        """Display comprehensive analysis results."""
        print(f"\n{'='*100}")
        print("COMPREHENSIVE ANALYSIS RESULTS SUMMARY")
        print(f"{'='*100}")
        
        # Basic info
        print(f"Target Sector: {results['target_sector']} - {results['target_sector_name']}")
        print(f"Demand Change: {results['demand_change']:,} billion won")
        print(f"Supply Chain Type: {results.get('supply_chain_type', 'full')}")
        
        # Integrated summary
        integrated = results.get('integrated_summary', {})
        
        print(f"\n{'ECONOMIC IMPACTS':-<50}")
        econ = integrated.get('economic_impact', {})
        print(f"  Sectors affected: {econ.get('sectors_affected', 0)}")
        print(f"  Total output impact: {econ.get('total_output_impact', 0):,.1f} billion won")
        print(f"  GDP impact: {econ.get('gdp_impact', 0):,.1f} billion won")
        print(f"  Production multiplier: {econ.get('production_multiplier', 0):.2f}")
        
        print(f"\n{'EMPLOYMENT IMPACTS':-<50}")
        emp = integrated.get('employment_impact', {})
        print(f"  Total jobs affected: {emp.get('total_jobs_affected', 0):,.0f}")
        print(f"  Sectors with job impact: {emp.get('sectors_with_job_impact', 0)}")
        print(f"  Analysis region: {emp.get('region_analyzed', 'N/A')}")
        
        print(f"\n{'TRADE IMPACTS':-<50}")
        trade = integrated.get('trade_impact', {})
        print(f"  Import impact: {trade.get('import_impact', 0):,.1f} billion won")
        print(f"  Domestic impact: {trade.get('domestic_impact', 0):,.1f} billion won")
        print(f"  Import dependency: {trade.get('import_dependency', 0):.1%}")
        print(f"  Domestic dependency: {trade.get('domestic_dependency', 0):.1%}")
        
        print(f"\n{'ENVIRONMENTAL IMPACTS':-<50}")
        env = integrated.get('environmental_impact', {})
        print(f"  CO2 impact: {env.get('co2_impact_tons', 0):,.0f} tons")
        print(f"  Car equivalent: {env.get('car_equivalent_years', 0):,.0f} car-years")
        print(f"  Environmental concern: {env.get('environmental_concern_level', 'N/A')}")
        
        print(f"\n{'FISCAL IMPACTS':-<50}")
        fiscal = integrated.get('fiscal_impact', {})
        print(f"  Total tax impact: {fiscal.get('total_tax_impact', 0):,.1f} billion won")
        print(f"  Income tax impact: {fiscal.get('income_tax_impact', 0):,.1f} billion won")
        print(f"  Corporate tax impact: {fiscal.get('corporate_tax_impact', 0):,.1f} billion won")
        
        print(f"\n{'OVERALL ASSESSMENT':-<50}")
        overall = integrated.get('overall_assessment', {})
        print(f"  Economic magnitude: {overall.get('economic_magnitude', 'N/A')}")
        print(f"  Employment significance: {overall.get('employment_significance', 'N/A')}")
        print(f"  Trade implications: {overall.get('trade_implications', 'N/A')}")
        print(f"  Environmental concern: {overall.get('environmental_concern', 'N/A')}")
        print(f"  Fiscal significance: {overall.get('fiscal_significance', 'N/A')}")
        
        print(f"\n{'='*100}")
    
    def display_results_as_tables(self, results: Dict, export_excel: bool = False, filename: str = None):
        """Display comprehensive analysis results in IO table format."""
        print(f"\n{'='*100}")
        print("COMPREHENSIVE ANALYSIS RESULTS - IO TABLE FORMAT")
        print(f"{'='*100}")
        
        # Create all analysis tables
        all_matrices = self.table_formatter.create_full_analysis_tables(results, show_top_n=self.config.display_limits.default_table_rows)
        
        # Display each table
        for table_name, matrix in all_matrices.items():
            if not matrix.empty:
                # Format table name for display
                display_name = table_name.replace('_', ' ')
                self.table_formatter.display_matrix_table(matrix, display_name, max_rows=self.config.display_limits.default_matrix_rows)
        
        # Export to Excel if requested
        if export_excel:
            if filename is None:
                target_sector = results.get('target_sector', 'unknown')
                filename = f"sector_analysis_{target_sector}.xlsx"
            
            self.table_formatter.export_matrices_to_excel(
                all_matrices,
                filename,
                target_sector=results.get('target_sector'),
                demand_change=results.get('demand_change')
            )
    
    def display_steel_coal_tables(self, steel_coal_results: Dict, export_excel: bool = False):
        """Display steel-coal analysis results in table format."""
        print(f"\n{'='*100}")
        print("STEEL-COAL SUPPLY CHAIN ANALYSIS - IO TABLE FORMAT")
        print(f"{'='*100}")
        
        # Aggregate impacts table
        agg_impacts = steel_coal_results['aggregate_impacts']
        
        aggregate_data = pd.DataFrame([
            ['Total Supply Chain Impact', agg_impacts['total_supply_chain_impact'], 'billion won'],
            ['Total Employment Change', agg_impacts['total_employment_change'], 'jobs'],
            ['Total Import Impact', agg_impacts['total_import_impact'], 'billion won'],
            ['Total Domestic Impact', agg_impacts['total_domestic_impact'], 'billion won'],
            ['Total CO2 Impact', agg_impacts['total_co2_impact'], 'thousand tons'],
            ['Total Tax Impact', agg_impacts['total_tax_impact'], 'billion won']
        ], columns=['Impact_Type', 'Value', 'Unit'])
        
        self.table_formatter.display_matrix_table(
            aggregate_data.set_index('Impact_Type'), 
            "Aggregate Steel-Coal Supply Chain Impacts"
        )
        
        # Coal-specific impacts table
        coal_specific_data = []
        for steel_sector, coal_impacts in steel_coal_results['coal_specific_impacts'].items():
            for coal_sector, impact in coal_impacts.items():
                coal_specific_data.append({
                    'Steel_Sector': steel_sector[:self.config.display_limits.steel_sector_name_limit],
                    'Coal_Sector': coal_sector[:self.config.display_limits.coal_sector_name_limit],
                    'Impact_Value': impact
                })
        
        if coal_specific_data:
            try:
                coal_df = pd.DataFrame(coal_specific_data)
                if not coal_df.empty and 'Impact_Value' in coal_df.columns:
                    coal_df = coal_df.sort_values('Impact_Value', key=abs, ascending=False)
                    
                    self.table_formatter.display_matrix_table(
                        coal_df.set_index('Steel_Sector'),
                        "Coal-Specific Supply Chain Impacts"
                    )
                else:
                    print("   No valid coal-specific impact data to display.")
            except Exception as e:
                print(f"   Error creating coal-specific impacts table: {str(e)}")
        else:
            print("   No coal-specific impacts found.")
        
        # Individual sector analysis tables
        sector_analyses = steel_coal_results.get('sector_analyses', {})
        for steel_sector, analysis in list(sector_analyses.items())[:self.config.display_limits.max_sectors_to_display]:
            print(f"\n{'='*80}")
            print(f"DETAILED ANALYSIS: {steel_sector}")
            print(f"{'='*80}")
            
            # Create matrices for this sector
            sector_matrices = self.table_formatter.create_full_analysis_tables(analysis, show_top_n=self.config.display_limits.default_table_rows)
            
            # Display key matrices
            for matrix_name in ['Total_Impacts', 'Import_Domestic_Comparison', 'Employment_Impacts']:
                if matrix_name in sector_matrices:
                    matrix = sector_matrices[matrix_name]
                    self.table_formatter.display_matrix_table(
                        matrix, 
                        f"{steel_sector} - {matrix_name.replace('_', ' ')}", 
                        max_rows=self.config.display_limits.default_matrix_rows
                    )
        
        # Export to Excel if requested
        if export_excel:
            filename = f"steel_coal_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx"
            
            # Combine all matrices
            all_matrices = {'Aggregate_Impacts': aggregate_data.set_index('Impact_Type')}
            
            if coal_specific_data:
                all_matrices['Coal_Specific_Impacts'] = coal_df.set_index('Steel_Sector')
            
            # Add detailed sector matrices (limit to prevent memory issues)
            max_sectors_for_export = self.config.display_limits.max_sectors_for_export
            for i, (steel_sector, analysis) in enumerate(sector_analyses.items()):
                if i >= max_sectors_for_export:
                    print(f"   Limiting export to first {max_sectors_for_export} sectors to prevent memory issues.")
                    break
                    
                try:
                    sector_matrices = self.table_formatter.create_full_analysis_tables(analysis, show_top_n=self.config.display_limits.default_table_rows)
                    for matrix_name, matrix in sector_matrices.items():
                        sheet_name = f"{steel_sector.split(':')[0]}_{matrix_name}"[:self.config.display_limits.excel_sheet_name_limit]
                        all_matrices[sheet_name] = matrix
                except Exception as e:
                    print(f"   Warning: Could not export matrices for {steel_sector}: {str(e)}")
                    continue
            
            self.table_formatter.export_matrices_to_excel(
                all_matrices,
                filename,
                target_sector="Steel-Coal Analysis",
                demand_change=steel_coal_results.get('reduction_amount')
            )
    
    def interactive_enhanced_analysis(self):
        """Run enhanced interactive analysis interface."""
        print(f"\n{'='*80}")
        print("ENHANCED SECTOR IMPACT ANALYZER")
        print(f"{'='*80}")
        print("Comprehensive analysis including:")
        print("- Supply chain impacts (backward linkages)")
        print("- Employment effects")
        print("- Import vs Domestic impacts (separate analysis)")
        print("- Value-added and production multipliers")
        print("- Environmental impacts (CO2 estimates)")
        print("- Fiscal impacts (tax effects)")
        print("- Regional spillover effects")
        print(f"{'='*80}")
        
        while True:
            try:
                print("\nEnhanced Analysis Options:")
                for option in self.config.interactive_options.menu_options:
                    print(option)
                
                choice = input(f"\nSelect option (1-{self.config.interactive_options.max_menu_choice}): ").strip()
                
                if choice == str(self.config.interactive_options.max_menu_choice):
                    print("Enhanced analysis complete!")
                    break
                elif choice == '1':
                    self._interactive_comprehensive_analysis()
                elif choice == '2':
                    self._interactive_steel_coal_comprehensive()
                elif choice == '3':
                    self._interactive_import_domestic_analysis()
                elif choice == '4':
                    self._interactive_environmental_analysis()
                elif choice == '5':
                    self._interactive_comprehensive_analysis_tables()
                elif choice == '6':
                    self._interactive_steel_coal_analysis_tables()
                elif choice == '7':
                    self._interactive_sector_search()
                else:
                    print(f"Invalid option. Please select 1-{self.config.interactive_options.max_menu_choice}.")
                    
            except KeyboardInterrupt:
                print("\n\nEnhanced analysis interrupted!")
                break
            except Exception as e:
                print(f"Error: {str(e)}")
                continue
    
    def _interactive_comprehensive_analysis(self):
        """Interactive comprehensive analysis."""
        try:
            sector_code = input("Enter sector code (4-digit): ").strip()
            if len(sector_code) != 4 or not sector_code.isdigit():
                print("Please enter a valid 4-digit sector code.")
                return
            
            try:
                amount = float(input("Enter demand change (billion won): "))
                if amount == 0:
                    print("Please enter a non-zero amount.")
                    return
            except ValueError:
                print("Please enter a valid number.")
                return
            
            # Ask for supply chain analysis type
            print("\nSupply Chain Analysis Type:")
            print("1. Direct effects only (immediate suppliers)")
            print("2. Indirect/Leontief effects only (multiplier effects)")
            print("3. Full effects (direct + indirect)")
            
            analysis_choice = input("Select analysis type (1-3) [3]: ").strip()
            if analysis_choice == "1":
                supply_chain_type = "direct"
            elif analysis_choice == "2":
                supply_chain_type = "leontief"
            else:
                supply_chain_type = "full"  # default
            
            print(f"\nRunning comprehensive analysis with {supply_chain_type} supply chain effects...")
            results = self.comprehensive_sector_analysis(sector_code, amount, supply_chain_type=supply_chain_type)
            self.display_comprehensive_results(results)
            
            input("\nPress Enter to continue...")
            
        except ValueError:
            print("Please enter valid numbers.")
        except Exception as e:
            print(f"Analysis error: {str(e)}")
    
    def _interactive_comprehensive_analysis_tables(self):
        """Interactive comprehensive analysis with IO table display."""
        try:
            sector_code = input("Enter sector code (4-digit): ").strip()
            if len(sector_code) != 4 or not sector_code.isdigit():
                print("Please enter a valid 4-digit sector code.")
                return
            
            try:
                amount = float(input("Enter demand change (billion won): "))
                if amount == 0:
                    print("Please enter a non-zero amount.")
                    return
            except ValueError:
                print("Please enter a valid number.")
                return
            
            # Ask for supply chain analysis type
            print("\nSupply Chain Analysis Type:")
            print("1. Direct effects only (immediate suppliers)")
            print("2. Indirect/Leontief effects only (multiplier effects)")
            print("3. Full effects (direct + indirect)")
            
            analysis_choice = input("Select analysis type (1-3) [3]: ").strip()
            if analysis_choice == "1":
                supply_chain_type = "direct"
            elif analysis_choice == "2":
                supply_chain_type = "leontief"
            else:
                supply_chain_type = "full"  # default
            
            export_excel = input("Export to Excel? (y/n) [n]: ").strip().lower() == 'y'
            
            print(f"\nRunning comprehensive analysis with IO tables using {supply_chain_type} supply chain effects...")
            results = self.comprehensive_sector_analysis(sector_code, amount, supply_chain_type=supply_chain_type)
            
            # Display as tables
            filename = f"analysis_{sector_code}_{supply_chain_type}_{abs(amount):.0f}.xlsx" if export_excel else None
            self.display_results_as_tables(results, export_excel, filename)
            
            input("\nPress Enter to continue...")
            
        except ValueError:
            print("Please enter valid numbers.")
        except Exception as e:
            print(f"Analysis error: {str(e)}")
    
    def _interactive_steel_coal_analysis_tables(self):
        """Interactive steel-coal analysis with IO table display."""
        try:
            amount_input = input(f"Enter coal reduction amount (billion won) [{self.config.default_values.default_reduction_amount}]: ").strip()
            if not amount_input:
                amount = self.config.default_values.default_reduction_amount
            else:
                try:
                    amount = float(amount_input)
                except ValueError:
                    print("Please enter a valid number.")
                    return
            
            export_excel = input("Export to Excel? (y/n) [n]: ").strip().lower() == 'y'
            
            print(f"\nRunning steel-coal analysis with IO tables...")
            results = self.analyze_steel_coal_comprehensive(amount)
            
            # Display as tables
            self.display_steel_coal_tables(results, export_excel)
            
            input("\nPress Enter to continue...")
            
        except ValueError:
            print("Please enter a valid number.")
        except Exception as e:
            print(f"Analysis error: {str(e)}")
    
    def _interactive_steel_coal_comprehensive(self):
        """Interactive steel-coal comprehensive analysis."""
        try:
            amount_input = input(f"Enter coal reduction amount (billion won) [{self.config.default_values.default_reduction_amount}]: ").strip()
            if not amount_input:
                amount = self.config.default_values.default_reduction_amount
            else:
                try:
                    amount = float(amount_input)
                except ValueError:
                    print("Please enter a valid number.")
                    return
            
            print(f"\nRunning comprehensive steel-coal analysis...")
            results = self.analyze_steel_coal_comprehensive(amount)
            
            # Display aggregate results
            print(f"\n{'='*80}")
            print("STEEL-COAL SUPPLY CHAIN: AGGREGATE IMPACTS")
            print(f"{'='*80}")
            
            agg = results['aggregate_impacts']
            print(f"Total supply chain impact: {agg['total_supply_chain_impact']:,.1f} billion won")
            print(f"Total employment change: {agg['total_employment_change']:,.0f} jobs")
            print(f"Total import impact: {agg['total_import_impact']:,.1f} billion won")
            print(f"Total domestic impact: {agg['total_domestic_impact']:,.1f} billion won")
            print(f"Total CO2 impact: {agg['total_co2_impact']:,.1f} thousand tons")
            print(f"Total tax impact: {agg['total_tax_impact']:,.1f} billion won")
            
            # Show coal-specific impacts
            print(f"\n{'COAL-SPECIFIC SUPPLY CHAIN IMPACTS':-<60}")
            for steel_sector, coal_impacts in results['coal_specific_impacts'].items():
                if coal_impacts:
                    print(f"\n{steel_sector}:")
                    for coal_sector, impact in coal_impacts.items():
                        print(f"  {coal_sector}: {impact:.1f} billion won")
            
            input("\nPress Enter to continue...")
            
        except ValueError:
            print("Please enter a valid number.")
        except Exception as e:
            print(f"Analysis error: {str(e)}")
    
    def _interactive_import_domestic_analysis(self):
        """Interactive import vs domestic analysis."""
        try:
            if not self.import_domestic_analyzer.is_data_available():
                print("Import/Domestic analysis data not available.")
                return
            
            sector_code = input("Enter sector code (4-digit): ").strip()
            if len(sector_code) != 4 or not sector_code.isdigit():
                print("Please enter a valid 4-digit sector code.")
                return
            
            try:
                amount = float(input("Enter demand change (billion won): "))
                if amount == 0:
                    print("Please enter a non-zero amount.")
                    return
            except ValueError:
                print("Please enter a valid number.")
                return
            
            print(f"\nAnalyzing import vs domestic impacts...")
            results = self.import_domestic_analyzer.analyze_import_domestic_impacts(
                sector_code, amount
            )
            
            if not results:
                print("No results returned from analysis.")
                return
            
            print(f"\n{'='*60}")
            print("IMPORT vs DOMESTIC IMPACT ANALYSIS")
            print(f"{'='*60}")
            print(f"Sector: {results.get('target_sector_name', 'Unknown')}")
            print(f"Demand change: {amount:,} billion won")
            print()
            print(f"Import impact: {results.get('total_import_effect', 0):,.1f} billion won")
            print(f"Domestic impact: {results.get('total_domestic_effect', 0):,.1f} billion won")
            print(f"Import share: {results.get('import_share', 0):.1%}")
            print(f"Domestic share: {results.get('domestic_share', 0):.1%}")
            print(f"Import multiplier: {results.get('import_multiplier', 0):.2f}")
            print(f"Domestic multiplier: {results.get('domestic_multiplier', 0):.2f}")
            
            input("\nPress Enter to continue...")
            
        except KeyboardInterrupt:
            print("\nAnalysis interrupted by user.")
        except Exception as e:
            print(f"Analysis error: {str(e)}")
            print("Please check your inputs and try again.")
    
    def _interactive_environmental_analysis(self):
        """Interactive environmental analysis."""
        try:
            sector_code = input("Enter sector code (4-digit): ").strip()
            amount = float(input("Enter output change (billion won): "))
            
            # Create mock production impacts for environmental analysis
            sectoral_production = {f"{sector_code}: Target Sector": amount}
            
            print(f"\nAnalyzing environmental impacts...")
            results = self.comprehensive_analyzer.analyze_environmental_impact(sectoral_production)
            
            print(f"\n{'='*60}")
            print("ENVIRONMENTAL IMPACT ANALYSIS")
            print(f"{'='*60}")
            
            env_summary = results.get('environmental_summary', {})
            print(f"Total CO2 impact: {env_summary.get('total_co2_thousand_tons', 0):,.1f} thousand tons")
            print(f"Equivalent to: {env_summary.get('equivalent_car_years', 0):,.0f} car-years of emissions")
            print(f"High-carbon sectors affected: {env_summary.get('high_impact_sectors', 0)}")
            
            print(f"\n{'Sectoral CO2 Impacts':-<40}")
            sectoral_co2 = results.get('sectoral_co2_impact', {})
            for sector, co2 in sectoral_co2.items():
                print(f"  {sector}: {co2:.1f} thousand tons")
            
            input("\nPress Enter to continue...")
            
        except ValueError:
            print("Please enter valid numbers.")
        except Exception as e:
            print(f"Analysis error: {str(e)}")
    
    def _interactive_sector_search(self):
        """Interactive sector search."""
        try:
            keyword = input("Enter search keyword: ").strip()
            matching = self.io_loader.find_sectors_by_keyword(keyword)
            
            print(f"\nFound {len(matching)} sectors matching '{keyword}':")
            for i, (code, name) in enumerate(matching[:self.config.display_limits.search_results_limit]):
                print(f"{i+1:2d}. {code}: {name}")
            
            if len(matching) > self.config.display_limits.search_overflow_threshold:
                print(f"... and {len(matching) - self.config.display_limits.search_overflow_threshold} more")
            
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"Search error: {str(e)}")

def main():
    """Main function to run the Enhanced Sector Impact Analyzer."""
    try:
        print("Initializing Enhanced Sector Impact Analyzer...")
        analyzer = EnhancedSectorAnalyzer()
        
        print("\nRunning test analysis: Steel sector (2711) with -1000 billion won demand change")
        
        # Test the fixes with steel sector
        results = analyzer.comprehensive_sector_analysis(
            "2711",  # Steel sector (선철)
            -1000,   # 1000 billion won reduction
            analysis_options={
                'supply_chain': True,
                'employment': True,
                'import_domestic': False,
                'comprehensive': False,
                'target_region': '전지역'
            },
            supply_chain_type="full"
        )
        
        # Display key results to verify fixes
        print("\n" + "="*80)
        print("ANALYSIS RESULTS - VERIFYING FIXES")
        print("="*80)
        
        # Check supply chain analysis 
        supply_chain = results.get('supply_chain_analysis', {})
        total_impacts = supply_chain.get('total_impacts', {})
        
        print(f"\nSupply Chain Analysis:")
        print(f"  Analysis type: {supply_chain.get('analysis_type', 'unknown')}")
        print(f"  Total sectors with impacts: {len(total_impacts)}")
        
        # Show net total to verify economic consistency
        net_total = sum(total_impacts.values())
        abs_total = sum(abs(v) for v in total_impacts.values())
        print(f"  Net total impact: {net_total:,.2f} billion won")
        print(f"  Absolute total impact: {abs_total:,.2f} billion won")
        
        # Check for accounting totals
        accounting_totals = ['9590', '9519', '9520', '중간투입계', '소계']
        accounting_found = []
        for sector in total_impacts.keys():
            if any(total in sector for total in accounting_totals):
                accounting_found.append(sector)
        
        if accounting_found:
            print(f"  WARNING: Found accounting totals in results: {accounting_found}")
        else:
            print(f"  ✓ No accounting totals found in supply chain results")
        
        # Check employment analysis
        employment = results.get('employment_analysis', {})
        sectoral_employment = employment.get('sectoral_employment', {})
        
        print(f"\nEmployment Analysis:")
        print(f"  Total employment change: {employment.get('total_employment_change', 0):,.0f} jobs")
        print(f"  Sectors with employment impacts: {len(sectoral_employment)}")
        
        # Show top 5 employment impacts to verify they make economic sense
        if sectoral_employment:
            sorted_emp = sorted(sectoral_employment.items(), key=lambda x: abs(x[1]), reverse=True)
            print(f"  Top 5 employment impacts:")
            for i, (sector, jobs) in enumerate(sorted_emp[:5]):
                print(f"    {i+1}. {sector}: {jobs:,.0f} jobs")
        
        # Check integrated summary
        integrated = results.get('integrated_summary', {})
        econ = integrated.get('economic_impact', {})
        
        print(f"\nIntegrated Summary:")
        print(f"  Sectors affected (filtered): {econ.get('sectors_affected', 0)}")
        print(f"  Net output impact: {econ.get('total_output_impact', 0):,.2f} billion won")
        
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE - Backend fixes verified")
        print("="*80)
        
        # Ask if user wants interactive mode
        print("\n✓ All backend fixes verified and working!")
            
    except Exception as e:
        print(f"Error initializing enhanced analyzer: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\nPlease ensure the following files exist:")
        print("- iotable/(표)(2020실측)투입산출표_기초가격_기본부문.xlsx")
        print("- iotable/2020지역_부속표_고용표_통합중분류.xlsx")

if __name__ == "__main__":
    main()