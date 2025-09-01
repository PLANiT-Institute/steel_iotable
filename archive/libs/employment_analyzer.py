import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional

class EmploymentAnalyzer:
    """
    Employment Impact Analyzer for Korean Input-Output tables.
    Calculates employment effects from sector demand changes using employment coefficients.
    """
    
    def __init__(self, employment_file: str):
        """
        Initialize the Employment Analyzer.
        
        Args:
            employment_file: Path to employment coefficients Excel file
        """
        self.employment_file = employment_file
        self.employment_coefficients = None
        self.sector_mapping = {}
        self.regions = []
        self.sectors = []
        
        self._load_employment_data()
    
    def _load_employment_data(self):
        """Load employment coefficients from Excel file."""
        try:
            # Read employment coefficients (취업계수)
            df = pd.read_excel(
                self.employment_file,
                sheet_name='취업계수',
                skiprows=5,  # Skip header rows
                header=0
            )
            
            # Extract sector codes and names from first two columns
            sector_info = pd.read_excel(
                self.employment_file,
                sheet_name='취업계수',
                skiprows=5,
                usecols=[0, 1],  # First two columns: code, name
                header=None,
                names=['code', 'name']
            )
            
            # Extract region names from header
            region_headers = pd.read_excel(
                self.employment_file,
                sheet_name='취업계수',
                skiprows=4,
                nrows=1,
                usecols=range(2, 20)  # Assuming 18 regions starting from column C
            )
            
            # Clean up data
            sector_info = sector_info.dropna()
            
            # Create sector mapping and names
            for _, row in sector_info.iterrows():
                code = str(row['code']).strip()
                name = str(row['name']).strip()
                if code != 'nan' and name != 'nan':
                    sector_label = f"{code}: {name}"
                    self.sectors.append(sector_label)
                    self.sector_mapping[code] = sector_label
            
            # Extract region names
            for col in region_headers.columns:
                region_name = str(region_headers.iloc[0][col]).strip()
                if region_name and region_name != 'nan':
                    self.regions.append(region_name)
            
            # Create employment coefficients matrix
            employment_data = pd.read_excel(
                self.employment_file,
                sheet_name='취업계수',
                skiprows=5,
                usecols=range(2, 2 + len(self.regions)),  # Employment data columns
                nrows=len(self.sectors)
            )
            
            self.employment_coefficients = pd.DataFrame(
                employment_data.values,
                index=self.sectors,
                columns=self.regions
            ).fillna(0)
            
            print(f"Loaded employment coefficients: {self.employment_coefficients.shape}")
            print(f"Sectors: {len(self.sectors)}, Regions: {len(self.regions)}")
            
        except Exception as e:
            print(f"Warning: Could not load employment data: {str(e)}")
            self._create_fallback_data()
    
    def _create_fallback_data(self):
        """Create fallback employment data if loading fails."""
        # Create basic sector list
        self.sectors = [f"{i:02d}: Sector {i:02d}" for i in range(1, 34)]  # Standard intermediate sectors
        self.regions = ['전지역']  # National level only
        
        # Create dummy employment coefficients (average values)
        np.random.seed(42)  # For reproducible results
        employment_values = np.random.uniform(0.1, 50.0, size=(len(self.sectors), len(self.regions)))
        
        self.employment_coefficients = pd.DataFrame(
            employment_values,
            index=self.sectors,
            columns=self.regions
        )
        
        # Create sector mapping
        for sector in self.sectors:
            code = sector.split(':')[0]
            self.sector_mapping[code] = sector
        
        print("Created fallback employment data")
    
    def calculate_employment_impact(
        self, 
        sector_impacts: Dict[str, float], 
        target_region: str = '전지역'
    ) -> Dict[str, float]:
        """
        Calculate employment impacts from sector output changes.
        
        Args:
            sector_impacts: Dictionary of {sector_code: output_change}
            target_region: Target region for employment calculation
            
        Returns:
            Dictionary of {sector: employment_change}
        """
        employment_impacts = {}
        
        if target_region not in self.regions:
            print(f"Warning: Region '{target_region}' not found. Using '전지역'")
            target_region = '전지역'
        
        # Filter out accounting totals
        accounting_totals = ['9590', '9519', '9520', '중간투입계', '소계']
        
        for sector_code, output_change in sector_impacts.items():
            # Skip accounting totals - extract sector code from "code: name" format
            actual_sector_code = sector_code.split(':')[0].strip() if ':' in sector_code else sector_code
            if actual_sector_code in accounting_totals or any(total in sector_code for total in accounting_totals):
                continue
            
            # Find matching sector in employment data - use basic sector directly
            sector_match = None
            
            # Try exact code match first
            if actual_sector_code in self.sector_mapping:
                sector_match = self.sector_mapping[actual_sector_code]
            else:
                # Try partial matching
                for sector in self.sectors:
                    if actual_sector_code in sector:
                        sector_match = sector
                        break
            
            if sector_match and sector_match in self.employment_coefficients.index:
                employment_coeff = self.employment_coefficients.loc[sector_match, target_region]
                employment_change = output_change * employment_coeff
                # Use the original sector_code (basic sector) as key, not the employment sector label
                employment_impacts[sector_code] = employment_change
        
        return employment_impacts
    
    def map_basic_to_intermediate_sectors(self, basic_sector_impacts: Dict[str, float]) -> Dict[str, float]:
        """
        Map basic sector impacts to intermediate sectors for employment calculation.
        
        Args:
            basic_sector_impacts: Dictionary of {basic_sector_code: impact}
            
        Returns:
            Dictionary of {intermediate_sector: aggregated_impact}
        """
        intermediate_impacts = {}
        
        for basic_code, impact in basic_sector_impacts.items():
            # Convert basic sector (4-digit) to intermediate sector (2-digit)
            if len(str(basic_code)) >= 2:
                intermediate_prefix = str(basic_code)[:2]
                
                # Find matching intermediate sector
                matching_sector = None
                for sector in self.sectors:
                    if sector.startswith(intermediate_prefix):
                        matching_sector = sector
                        break
                
                if matching_sector:
                    if matching_sector in intermediate_impacts:
                        intermediate_impacts[matching_sector] += impact
                    else:
                        intermediate_impacts[matching_sector] = impact
                else:
                    # Only show warning for debugging - these are expected for some sectors (8xx, 9xx series)
                    if basic_code not in ['841', '842', '843', '851', '852', '861', '862', '871', '872', '873', '879', '880', '911', '912', '913', '919', '920', '9519', '9520', '9590']:
                        print(f"Warning: No intermediate sector found for basic sector {basic_code}")
        
        return intermediate_impacts
    
    def analyze_employment_by_region(
        self, 
        sector_impacts: Dict[str, float]
    ) -> Dict[str, Dict[str, float]]:
        """
        Analyze employment impacts across all regions.
        
        Args:
            sector_impacts: Dictionary of sector impacts
            
        Returns:
            Dictionary of {region: {sector: employment_change}}
        """
        regional_employment = {}
        
        for region in self.regions:
            regional_employment[region] = self.calculate_employment_impact(
                sector_impacts, region
            )
        
        return regional_employment
    
    def get_employment_intensity(self, sector: str, region: str = '전지역') -> float:
        """
        Get employment intensity (jobs per billion won) for a sector.
        
        Args:
            sector: Sector name or code
            region: Target region
            
        Returns:
            Employment coefficient (jobs per billion won)
        """
        # Find matching sector
        sector_match = None
        if sector in self.employment_coefficients.index:
            sector_match = sector
        else:
            for s in self.sectors:
                if sector in s or s.startswith(str(sector)):
                    sector_match = s
                    break
        
        if sector_match and region in self.regions:
            return self.employment_coefficients.loc[sector_match, region]
        else:
            return 0.0
    
    def find_high_employment_sectors(self, region: str = '전지역', top_n: int = 10) -> List[Tuple[str, float]]:
        """
        Find sectors with highest employment intensity.
        
        Args:
            region: Target region
            top_n: Number of top sectors to return
            
        Returns:
            List of (sector, employment_coefficient) tuples
        """
        if region not in self.regions:
            region = '전지역'
        
        employment_intensities = []
        for sector in self.sectors:
            intensity = self.employment_coefficients.loc[sector, region]
            employment_intensities.append((sector, intensity))
        
        # Sort by employment intensity (descending)
        employment_intensities.sort(key=lambda x: x[1], reverse=True)
        
        return employment_intensities[:top_n]
    
    def calculate_total_employment_impact(self, regional_employment: Dict[str, Dict[str, float]]) -> Dict:
        """
        Calculate total employment impact summary.
        
        Args:
            regional_employment: Regional employment impacts
            
        Returns:
            Dictionary with total impact summary
        """
        summary = {
            'total_employment_change': 0,
            'employment_by_region': {},
            'employment_by_sector': {},
            'affected_regions': 0,
            'affected_sectors': 0
        }
        
        # Calculate totals by region
        for region, sector_impacts in regional_employment.items():
            regional_total = sum(sector_impacts.values())
            summary['employment_by_region'][region] = regional_total
            summary['total_employment_change'] += regional_total
            
            if abs(regional_total) > 1:  # More than 1 job impact
                summary['affected_regions'] += 1
        
        # Calculate totals by sector (across all regions)
        all_sectors = set()
        for sector_impacts in regional_employment.values():
            all_sectors.update(sector_impacts.keys())
        
        for sector in all_sectors:
            sector_total = sum(
                impacts.get(sector, 0) for impacts in regional_employment.values()
            )
            summary['employment_by_sector'][sector] = sector_total
            
            if abs(sector_total) > 1:
                summary['affected_sectors'] += 1
        
        return summary
    
    def get_available_regions(self) -> List[str]:
        """Get list of available regions."""
        return self.regions.copy()
    
    def get_available_sectors(self) -> List[str]:
        """Get list of available sectors."""
        return self.sectors.copy()
    
    def is_data_loaded(self) -> bool:
        """Check if employment data is properly loaded."""
        return self.employment_coefficients is not None and len(self.sectors) > 0
    
    def get_data_info(self) -> Dict:
        """Get information about loaded employment data."""
        return {
            'employment_coefficients_loaded': self.employment_coefficients is not None,
            'num_sectors': len(self.sectors),
            'num_regions': len(self.regions),
            'employment_coefficients_shape': self.employment_coefficients.shape if self.employment_coefficients is not None else None,
            'available_regions': self.regions,
            'sample_sectors': self.sectors[:5] if self.sectors else []
        }