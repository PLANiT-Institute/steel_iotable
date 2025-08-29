#!/usr/bin/env python3
"""
Sector Impact Analyzer

Analyzes economic impacts and employment changes from sector demand changes
using Korean Input-Output tables at basic prices (기초가격).

This tool helps analyze supply chain effects when sectors reduce their input consumption.
For example: What happens to the coal supply chain when steel sector uses less coal?
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from libs.io_data_loader import IODataLoader
from libs.supply_chain_analyzer import SupplyChainAnalyzer
from libs.employment_analyzer import EmploymentAnalyzer
import pandas as pd
from typing import Dict, List, Tuple, Optional

class SectorImpactAnalyzer:
    """
    Main class for comprehensive sector impact analysis.
    Integrates IO analysis, supply chain analysis, and employment analysis.
    """
    
    def __init__(self, 
                 basic_io_file: str = 'iotable/(표)(2020실측)투입산출표_기초가격_기본부문.xlsx',
                 employment_file: str = 'iotable/2020지역_부속표_고용표_통합중분류.xlsx'):
        """
        Initialize the Sector Impact Analyzer.
        
        Args:
            basic_io_file: Path to basic IO table file (기초가격_기본부문)
            employment_file: Path to employment coefficients file
        """
        self.basic_io_file = basic_io_file
        self.employment_file = employment_file
        
        # Initialize component analyzers
        print("Initializing IO Data Loader...")
        self.io_loader = IODataLoader(basic_io_file)
        
        print("Initializing Supply Chain Analyzer...")
        self.supply_chain_analyzer = SupplyChainAnalyzer(self.io_loader)
        
        print("Initializing Employment Analyzer...")
        self.employment_analyzer = EmploymentAnalyzer(employment_file)
        
        self._check_data_status()
    
    def _check_data_status(self):
        """Check and report data loading status."""
        print("\n" + "="*60)
        print("DATA LOADING STATUS")
        print("="*60)
        
        # IO Data status
        io_info = self.io_loader.get_data_info()
        print(f"IO Table Data:")
        print(f"  - Sectors loaded: {io_info['num_sectors']}")
        print(f"  - Transaction table: {'✓' if io_info['transaction_table_loaded'] else '✗'}")
        print(f"  - Input coefficients: {'✓' if io_info['input_coefficients_loaded'] else '✗'}")
        
        # Employment data status
        emp_info = self.employment_analyzer.get_data_info()
        print(f"\nEmployment Data:")
        print(f"  - Employment coefficients: {'✓' if emp_info['employment_coefficients_loaded'] else '✗'}")
        print(f"  - Sectors: {emp_info['num_sectors']}")
        print(f"  - Regions: {emp_info['num_regions']}")
        
        # Supply chain analyzer status
        print(f"\nSupply Chain Analysis:")
        print(f"  - Leontief inverse: {'✓' if self.supply_chain_analyzer.leontief_inverse is not None else '✗'}")
        
        print("="*60 + "\n")
    
    def analyze_sector_reduction_impact(
        self,
        target_sector: str,
        reduction_amount: float,
        include_employment: bool = True,
        target_region: str = '전지역'
    ) -> Dict:
        """
        Comprehensive analysis of sector demand reduction impacts.
        
        Args:
            target_sector: Sector code that reduces its demand
            reduction_amount: Amount of demand reduction (10억원)
            include_employment: Include employment impact analysis
            target_region: Target region for employment analysis
            
        Returns:
            Dictionary containing comprehensive impact results
        """
        results = {
            'target_sector': target_sector,
            'target_sector_name': self.io_loader.get_sector_name(target_sector),
            'reduction_amount': reduction_amount,
            'target_region': target_region,
            'supply_chain_impacts': {},
            'employment_impacts': {},
            'summary': {}
        }
        
        print(f"\nAnalyzing impact of {reduction_amount:,} billion won reduction in sector {target_sector}")
        print(f"Sector: {results['target_sector_name']}")
        
        # 1. Supply chain impact analysis
        print("1. Analyzing supply chain impacts...")
        supply_chain_results = self.supply_chain_analyzer.analyze_demand_reduction_impact(
            target_sector, 
            reduction_amount,
            include_indirect=True
        )
        results['supply_chain_impacts'] = supply_chain_results
        
        # 2. Employment impact analysis
        if include_employment:
            print("2. Analyzing employment impacts...")
            
            # Use total impacts from supply chain analysis for employment calculation
            total_impacts = supply_chain_results.get('total_impacts', {})
            
            # Convert sector labels to codes for employment analysis
            sector_impact_codes = {}
            for sector_label, impact in total_impacts.items():
                # Extract sector code from label (format: "code: name")
                if ':' in sector_label:
                    sector_code = sector_label.split(':')[0].strip()
                    sector_impact_codes[sector_code] = impact
            
            # Map basic sectors to intermediate sectors for employment calculation
            intermediate_impacts = self.employment_analyzer.map_basic_to_intermediate_sectors(sector_impact_codes)
            
            # Calculate employment impacts
            employment_impacts = self.employment_analyzer.calculate_employment_impact(
                {'dummy': 1},  # We'll calculate directly from intermediate impacts
                target_region
            )
            
            # Calculate employment impacts for each affected intermediate sector
            employment_results = {}
            for intermediate_sector, impact in intermediate_impacts.items():
                emp_coeff = self.employment_analyzer.get_employment_intensity(intermediate_sector, target_region)
                employment_change = impact * emp_coeff
                if abs(employment_change) > 0.1:  # Only include significant changes
                    employment_results[intermediate_sector] = employment_change
            
            results['employment_impacts'] = employment_results
        
        # 3. Generate summary
        results['summary'] = self._generate_summary(results)
        
        return results
    
    def analyze_steel_coal_supply_chain(self, steel_coal_reduction: float = 1000) -> Dict:
        """
        Specific analysis for steel-coal supply chain impacts.
        
        Args:
            steel_coal_reduction: Amount of coal reduction in steel sector (10억원)
            
        Returns:
            Analysis results for steel-coal supply chain
        """
        print(f"\n{'='*60}")
        print("STEEL-COAL SUPPLY CHAIN ANALYSIS")
        print(f"{'='*60}")
        
        # Find steel sectors
        steel_sectors = self.io_loader.find_sectors_by_keyword('철강')
        steel_sectors.extend(self.io_loader.find_sectors_by_keyword('제철'))
        steel_sectors.extend(self.io_loader.find_sectors_by_keyword('선철'))
        
        if not steel_sectors:
            # Try alternative keywords
            steel_sectors = self.io_loader.find_sectors_by_keyword('27')  # Steel industry code prefix
        
        print(f"Found {len(steel_sectors)} steel-related sectors")
        for i, (code, name) in enumerate(steel_sectors[:5]):
            print(f"  {i+1}. {code}: {name}")
        
        # Find coal sectors
        coal_sectors = self.io_loader.find_sectors_by_keyword('석탄')
        coal_sectors.extend(self.io_loader.find_sectors_by_keyword('코크스'))
        
        print(f"\nFound {len(coal_sectors)} coal-related sectors")
        for i, (code, name) in enumerate(coal_sectors):
            print(f"  {i+1}. {code}: {name}")
        
        # Analyze supply chain for each steel sector
        analysis_results = {}
        
        for steel_code, steel_name in steel_sectors[:3]:  # Analyze top 3 steel sectors
            print(f"\nAnalyzing: {steel_code}: {steel_name}")
            
            # Analyze what happens when this steel sector reduces coal consumption
            sector_analysis = self.analyze_sector_reduction_impact(
                steel_code,
                steel_coal_reduction,
                include_employment=True
            )
            
            # Identify coal-specific impacts
            coal_specific_impacts = {}
            supply_chain_impacts = sector_analysis['supply_chain_impacts']['total_impacts']
            
            for affected_sector, impact in supply_chain_impacts.items():
                # Check if this affected sector is coal-related
                for coal_code, coal_name in coal_sectors:
                    if coal_code in affected_sector.lower():
                        coal_specific_impacts[affected_sector] = impact
                        break
                # Also check for coal keywords in sector name
                for keyword in ['석탄', '코크스', 'coal', 'coke']:
                    if keyword in affected_sector.lower():
                        coal_specific_impacts[affected_sector] = impact
                        break
            
            sector_analysis['coal_specific_impacts'] = coal_specific_impacts
            analysis_results[f"{steel_code}: {steel_name}"] = sector_analysis
        
        return {
            'steel_sectors': steel_sectors,
            'coal_sectors': coal_sectors,
            'analysis_results': analysis_results,
            'reduction_amount': steel_coal_reduction
        }
    
    def _generate_summary(self, analysis_results: Dict) -> Dict:
        """Generate summary statistics for analysis results."""
        summary = {
            'total_sectors_affected': 0,
            'total_supply_chain_impact': 0,
            'total_employment_change': 0,
            'top_affected_sectors': [],
            'employment_intensity': 0
        }
        
        # Supply chain summary
        supply_impacts = analysis_results.get('supply_chain_impacts', {}).get('total_impacts', {})
        if supply_impacts:
            summary['total_sectors_affected'] = len([s for s, i in supply_impacts.items() if abs(i) > 0.1])
            summary['total_supply_chain_impact'] = sum(abs(i) for i in supply_impacts.values())
            
            # Top 5 affected sectors
            sorted_impacts = sorted(supply_impacts.items(), key=lambda x: abs(x[1]), reverse=True)
            summary['top_affected_sectors'] = sorted_impacts[:5]
        
        # Employment summary
        employment_impacts = analysis_results.get('employment_impacts', {})
        if employment_impacts:
            summary['total_employment_change'] = sum(employment_impacts.values())
            
            # Employment intensity (jobs per billion won)
            reduction_amount = analysis_results.get('reduction_amount', 1)
            if reduction_amount != 0:
                summary['employment_intensity'] = abs(summary['total_employment_change'] / reduction_amount)
        
        return summary
    
    def display_results(self, results: Dict):
        """Display comprehensive analysis results."""
        print(f"\n{'='*80}")
        print("COMPREHENSIVE SECTOR IMPACT ANALYSIS RESULTS")
        print(f"{'='*80}")
        
        print(f"Target Sector: {results['target_sector']} - {results['target_sector_name']}")
        print(f"Demand Reduction: {results['reduction_amount']:,} billion won")
        print(f"Analysis Region: {results.get('target_region', '전지역')}")
        
        # Summary
        summary = results.get('summary', {})
        if summary:
            print(f"\n{'Summary':-<50}")
            print(f"Total affected sectors: {summary.get('total_sectors_affected', 0)}")
            print(f"Total supply chain impact: {summary.get('total_supply_chain_impact', 0):,.1f} billion won")
            print(f"Total employment change: {summary.get('total_employment_change', 0):,.0f} jobs")
            print(f"Employment intensity: {summary.get('employment_intensity', 0):.2f} jobs/billion won")
        
        # Supply chain impacts
        supply_impacts = results.get('supply_chain_impacts', {}).get('total_impacts', {})
        if supply_impacts:
            print(f"\n{'Top Supply Chain Impacts':-<50}")
            sorted_impacts = sorted(supply_impacts.items(), key=lambda x: abs(x[1]), reverse=True)
            for i, (sector, impact) in enumerate(sorted_impacts[:10]):
                print(f"{i+1:2d}. {sector[:60]:<60} {impact:>10.1f}")
        
        # Employment impacts
        employment_impacts = results.get('employment_impacts', {})
        if employment_impacts:
            print(f"\n{'Employment Impacts by Sector':-<50}")
            sorted_emp = sorted(employment_impacts.items(), key=lambda x: abs(x[1]), reverse=True)
            for i, (sector, jobs) in enumerate(sorted_emp[:10]):
                print(f"{i+1:2d}. {sector[:60]:<60} {jobs:>10.1f} jobs")
        
        # Coal-specific impacts (if available)
        coal_impacts = results.get('coal_specific_impacts', {})
        if coal_impacts:
            print(f"\n{'Coal-Specific Supply Chain Impacts':-<50}")
            for sector, impact in coal_impacts.items():
                print(f"    {sector}: {impact:.1f} billion won")
    
    def interactive_analysis(self):
        """Run interactive analysis interface."""
        print(f"\n{'='*80}")
        print("SECTOR IMPACT ANALYZER - Interactive Mode")
        print(f"{'='*80}")
        print("Analyze economic and employment impacts of sector demand changes")
        print("Example: What happens when steel sector reduces coal consumption?")
        print(f"{'='*80}")
        
        while True:
            try:
                print("\nAnalysis Options:")
                print("1. Analyze specific sector impact")
                print("2. Steel-coal supply chain analysis")
                print("3. Search sectors by keyword")
                print("4. List available sectors")
                print("5. Exit")
                
                choice = input("\nSelect option (1-5): ").strip()
                
                if choice == '5':
                    print("Analysis complete. Goodbye!")
                    break
                elif choice == '1':
                    self._interactive_sector_analysis()
                elif choice == '2':
                    self._interactive_steel_coal_analysis()
                elif choice == '3':
                    self._interactive_sector_search()
                elif choice == '4':
                    self._list_sectors()
                else:
                    print("Invalid option. Please select 1-5.")
                    
            except KeyboardInterrupt:
                print("\n\nAnalysis interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"Error: {str(e)}")
                continue
    
    def _interactive_sector_analysis(self):
        """Interactive specific sector analysis."""
        try:
            sector_code = input("Enter sector code (4-digit): ").strip()
            if len(sector_code) != 4 or not sector_code.isdigit():
                print("Please enter a valid 4-digit sector code.")
                return
            
            reduction_amount = float(input("Enter reduction amount (billion won): "))
            if reduction_amount <= 0:
                print("Please enter a positive number.")
                return
            
            print(f"\nAnalyzing {reduction_amount:,} billion won reduction in sector {sector_code}...")
            results = self.analyze_sector_reduction_impact(sector_code, reduction_amount)
            self.display_results(results)
            
        except ValueError:
            print("Please enter valid numbers.")
        except Exception as e:
            print(f"Analysis error: {str(e)}")
    
    def _interactive_steel_coal_analysis(self):
        """Interactive steel-coal supply chain analysis."""
        try:
            reduction_amount = input("Enter coal reduction amount (billion won) [default: 1000]: ").strip()
            if not reduction_amount:
                reduction_amount = 1000
            else:
                reduction_amount = float(reduction_amount)
            
            print(f"\nAnalyzing steel-coal supply chain impacts...")
            results = self.analyze_steel_coal_supply_chain(reduction_amount)
            
            # Display results for each steel sector
            for steel_sector, analysis in results['analysis_results'].items():
                print(f"\n{'='*60}")
                print(f"STEEL SECTOR: {steel_sector}")
                print(f"{'='*60}")
                self.display_results(analysis)
            
        except ValueError:
            print("Please enter a valid number.")
        except Exception as e:
            print(f"Analysis error: {str(e)}")
    
    def _interactive_sector_search(self):
        """Interactive sector search."""
        try:
            keyword = input("Enter search keyword (Korean or English): ").strip()
            if not keyword:
                print("Please enter a keyword.")
                return
            
            matching_sectors = self.io_loader.find_sectors_by_keyword(keyword)
            
            if not matching_sectors:
                print(f"No sectors found matching '{keyword}'")
                return
            
            print(f"\nFound {len(matching_sectors)} sectors matching '{keyword}':")
            print("-" * 70)
            for i, (code, name) in enumerate(matching_sectors[:20]):  # Show top 20
                print(f"{i+1:2d}. {code}: {name}")
            
            if len(matching_sectors) > 20:
                print(f"... and {len(matching_sectors) - 20} more")
            
        except Exception as e:
            print(f"Search error: {str(e)}")
    
    def _list_sectors(self):
        """List available sectors."""
        try:
            sectors = self.io_loader.get_sector_names()
            print(f"\nAvailable sectors ({len(sectors)} total):")
            print("-" * 70)
            
            # Show first 30 sectors
            for i, sector in enumerate(sectors[:30]):
                print(f"{i+1:2d}. {sector}")
            
            if len(sectors) > 30:
                print(f"... and {len(sectors) - 30} more sectors")
                
                show_more = input("\nShow all sectors? (y/n): ").lower().strip()
                if show_more == 'y':
                    for i, sector in enumerate(sectors[30:], 31):
                        print(f"{i:2d}. {sector}")
            
        except Exception as e:
            print(f"Error listing sectors: {str(e)}")

def main():
    """Main function to run the Sector Impact Analyzer."""
    try:
        analyzer = SectorImpactAnalyzer()
        analyzer.interactive_analysis()
    except Exception as e:
        print(f"Error initializing analyzer: {str(e)}")
        print("\nPlease ensure the following files exist:")
        print("- iotable/(표)(2020실측)투입산출표_기초가격_기본부문.xlsx")
        print("- iotable/2020지역_부속표_고용표_통합중분류.xlsx")

if __name__ == "__main__":
    main()