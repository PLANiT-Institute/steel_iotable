import pandas as pd
import numpy as np
from typing import List, Dict, Union, Optional

class EmploymentCalculator:
    def __init__(self, excel_file_path: str, basic_iotable_path: str = None):
        """
        Initialize the employment calculator with comprehensive sector analysis capabilities.
        
        Classification Hierarchy:
        - basic_sectors (기본부문): 397 detailed sectors (e.g., 2711: 선철)
        - intermediate_sectors (중분류): Intermediate classification used for employment analysis 
        - industry_sectors (대분류): Major industry groups (농림수산업, 제조업, 서비스업 등)
        
        Args:
            excel_file_path: Path to the 2020지역_부속표_고용표_통합중분류.xlsx file
            basic_iotable_path: Path to the basic sector IO table (기본부문) for linkage analysis
        """
        self.excel_file = excel_file_path
        self.basic_iotable_path = basic_iotable_path
        self.employment_coefficients = None
        self.employment_multipliers = None
        
        # Input-Output Matrices and Coefficients
        self.basic_io_matrix = None
        self.A_matrix = None            # 총투입계수 (Total input coefficients)
        self.Am_matrix = None           # 수입투입계수 (Import input coefficients)  
        self.Ad_matrix = None           # 국산투입계수 (Domestic input coefficients)
        self.production_multipliers = None  # 생산유발계수
        self.import_multipliers = None      # 수입유발계수
        self.value_added_multipliers = None # 부가가치유발계수
        
        # Sector Classifications
        self.basic_sectors = None       # 기본부문 (397 sectors)
        self.intermediate_sectors = None # 중분류 (intermediate classification)
        self.industry_sectors = None    # 대분류 (major industry groups)
        self.regions = None
        self.sector_hierarchy = None
        self._load_data()
        if basic_iotable_path:
            self._load_basic_iotable()
        self._load_sector_mapping()
        self._build_sector_hierarchy()
    
    def _load_data(self):
        """Load employment coefficients and multipliers from the Excel file."""
        try:
            # Read the employment coefficients sheet
            # Skip first 4 rows, then row 5 has codes (col A) and row 6 has names (col B)
            df = pd.read_excel(
                self.excel_file, 
                sheet_name='취업계수',
                skiprows=4,
                header=[0, 1]  # Use two header rows
            )
            
            # Get the sector codes (first data column after skipping 4 rows)
            codes_df = pd.read_excel(
                self.excel_file, 
                sheet_name='취업계수',
                skiprows=4,
                usecols=[0],  # Column A has codes
                header=None
            )
            
            # Get the sector names (second data column after skipping 4 rows) 
            names_df = pd.read_excel(
                self.excel_file, 
                sheet_name='취업계수',
                skiprows=4,
                usecols=[1],  # Column B has names
                header=None
            )
            
            # Get the employment data (columns from C onwards)
            data_df = pd.read_excel(
                self.excel_file, 
                sheet_name='취업계수',
                skiprows=5,  # Skip one more row to get to actual data
                usecols=range(2, 20)  # Columns C through T (18 regions)
            )
            
            # Get region names from header row (row 5 after skipping 4)
            header_df = pd.read_excel(
                self.excel_file, 
                sheet_name='취업계수',
                skiprows=4,
                nrows=1,
                usecols=range(2, 20)
            )
            
            # Clean up region names
            region_names = []
            for col in header_df.columns:
                region_name = str(header_df.iloc[0][col]).strip()
                if region_name and region_name != 'nan':
                    region_names.append(region_name)
            
            # Create proper sector names (code: name format)
            sector_names = []
            for i in range(min(len(codes_df), len(names_df))):
                code = str(codes_df.iloc[i, 0]).strip()
                name = str(names_df.iloc[i, 0]).strip()
                if code != 'nan' and name != 'nan':
                    sector_names.append(f"{code}: {name}")
            
            # Set up the employment coefficients dataframe
            self.employment_coefficients = data_df.iloc[:len(sector_names), :len(region_names)]
            self.employment_coefficients.index = sector_names
            self.employment_coefficients.columns = region_names
            
            # Remove any rows/columns with all NaN values
            self.employment_coefficients = self.employment_coefficients.dropna(how='all')
            self.employment_coefficients = self.employment_coefficients.dropna(axis=1, how='all')
            
            self.regions = list(self.employment_coefficients.columns)
            self.intermediate_sectors = list(self.employment_coefficients.index)
            
            # Load multipliers (optional)
            try:
                self.employment_multipliers = pd.read_excel(
                    self.excel_file,
                    sheet_name='취업유발계수표',
                    index_col=0
                )
            except:
                self.employment_multipliers = None
            
        except Exception as e:
            raise ValueError(f"Error loading data from {self.excel_file}: {str(e)}")
    
    def _load_basic_iotable(self):
        """Load basic sector input-output table for linkage analysis."""
        try:
            # Load input coefficients (A, Am, Ad matrices)
            self._load_input_coefficients()
            
            # Load basic sector data (\uae30\ubcf8\ubd80\ubb38)
            self._load_basic_sectors()
            
        except Exception as e:
            print(f"Warning: Could not load basic IO table: {str(e)}")
            self.basic_io_matrix = None
    
    def _load_input_coefficients(self):
        """Load input-output coefficient matrices from basic sector IO table."""
        try:
            # Load 총투입계수(A) - Total input coefficients
            self.A_matrix = pd.read_excel(
                self.basic_iotable_path,
                sheet_name='총투입계수(A)',
                skiprows=6,  # Skip header rows
                index_col=[0, 1],  # Use first two columns as index (code, name)
                header=0
            )
            print(f"Loaded A matrix: {self.A_matrix.shape}")
            
            # Load 수입투입계수(Am) - Import input coefficients  
            self.Am_matrix = pd.read_excel(
                self.basic_iotable_path,
                sheet_name='수입투입계수(Am)',
                skiprows=6,
                index_col=[0, 1],
                header=0
            )
            print(f"Loaded Am matrix: {self.Am_matrix.shape}")
            
            # Load 국산투입계수(Ad) - Domestic input coefficients
            self.Ad_matrix = pd.read_excel(
                self.basic_iotable_path,
                sheet_name='국산투입계수(Ad)',
                skiprows=6,
                index_col=[0, 1],
                header=0
            )
            print(f"Loaded Ad matrix: {self.Ad_matrix.shape}")
            
        except Exception as e:
            print(f"Warning: Could not load input coefficients: {str(e)}")
            # Create fallback identity-like matrices if loading fails
            self.A_matrix = None
            self.Am_matrix = None
            self.Ad_matrix = None
    
    def _load_sector_mapping(self):
        """Load sector classification mapping from 2020_산업분류표.xlsx."""
        try:
            # Load the classification mapping file
            mapping_file = 'iotable/2020_산업분류표.xlsx'
            df = pd.read_excel(mapping_file, sheet_name='부문분류', header=2)
            
            # Set proper column names
            df.columns = ['기본부문_코드', '기본부문_명', '소분류_코드', '소분류_명', 
                         '중분류_코드', '중분류_명', '대분류_코드', '대분류_명']
            
            # Remove empty rows
            df = df.dropna(subset=['기본부문_코드'])
            
            # Forward fill to complete the hierarchical mapping
            for col in ['소분류_코드', '소분류_명', '중분류_코드', '중분류_명', '대분류_코드', '대분류_명']:
                df[col] = df[col].ffill()
            
            # Create mapping dictionaries
            self.basic_to_intermediate_map = {}
            self.basic_to_industry_map = {}
            
            for _, row in df.iterrows():
                basic_code = str(row['기본부문_코드']).strip()
                intermediate_code = row['중분류_코드']
                intermediate_name = row['중분류_명']
                industry_code = row['대분류_코드'] 
                industry_name = row['대분류_명']
                
                # Create intermediate sector key (code: name format)
                if pd.notna(intermediate_code) and pd.notna(intermediate_name):
                    intermediate_key = f"{int(intermediate_code)}: {intermediate_name}"
                    self.basic_to_intermediate_map[basic_code] = intermediate_key
                
                # Create industry sector key
                if pd.notna(industry_code) and pd.notna(industry_name):
                    self.basic_to_industry_map[basic_code] = industry_name
            
            print(f"Loaded sector mapping: {len(self.basic_to_intermediate_map)} basic → intermediate")
            print(f"Loaded sector mapping: {len(self.basic_to_industry_map)} basic → industry")
            
        except Exception as e:
            print(f"Warning: Could not load sector mapping: {str(e)}")
            self.basic_to_intermediate_map = {}
            self.basic_to_industry_map = {}
    
    def _load_multipliers(self):
        """Load production, import, and value-added multipliers."""
        # This will be implemented to load regional multiplier files
        pass
    
    def _build_sector_hierarchy(self):
        """Build comprehensive sector hierarchy mapping."""
        self.sector_hierarchy = {
            'basic_to_intermediate': {},  # 기본부문 -> 중분류
            'intermediate_to_industry': {},  # 중분류 -> 대뵔류
            'industry_groups': {}  # 대분류 그룹핑
        }
        
        # Create systematic mapping based on sector codes
        for sector in self.intermediate_sectors:
            if ':' in sector:
                code, name = sector.split(':', 1)
                code = code.strip()
                name = name.strip()
                
                # Map to industry sectors based on code ranges
                if code.isdigit():
                    code_num = int(code)
                    if 1 <= code_num <= 6:
                        industry = "농림수산업"
                    elif 7 <= code_num <= 14:
                        industry = "광업"
                    elif 15 <= code_num <= 42:
                        industry = "제조업"
                    elif 43 <= code_num <= 48:
                        industry = "전력가스수도건설업"
                    elif 49 <= code_num <= 56:
                        industry = "서비스업"
                    else:
                        industry = "기타"
                        
                    self.sector_hierarchy['intermediate_to_industry'][sector] = industry
        
        # Build reverse mappings
        self.sector_hierarchy['industry_to_intermediate'] = {}
        for intermediate, industry in self.sector_hierarchy['intermediate_to_industry'].items():
            if industry not in self.sector_hierarchy['industry_to_intermediate']:
                self.sector_hierarchy['industry_to_intermediate'][industry] = []
            self.sector_hierarchy['industry_to_intermediate'][industry].append(intermediate)
    
    def _load_basic_sectors(self):
        """Load basic sectors (기본부문) from IO table."""
        try:
            if self.basic_io_matrix is not None:
                # Get basic sector codes and names from IO table index
                self.basic_sectors = list(self.basic_io_matrix.index)
            else:
                # Fallback: create standard basic sector list
                self.basic_sectors = [f"{i:04d}" for i in range(1, 398)]  # 397 sectors
        except Exception as e:
            print(f"Warning: Could not load basic sectors: {str(e)}")
    
    def calculate_direct_employment_impact(
        self, 
        sector_demands: Dict[str, float],
        region: str = '전지역'
    ) -> Dict[str, float]:
        """
        Calculate direct employment creation/loss for selected sectors using employment coefficients.
        
        Args:
            sector_demands: Dictionary mapping sector names to demand changes (in 10억원)
                          Positive values = job creation, Negative values = job loss
            region: Target region for analysis (default: '전지역' for nationwide)
        
        Returns:
            Dictionary with sector-wise employment changes (in persons)
        """
        if region not in self.regions:
            raise ValueError(f"Region '{region}' not found. Available regions: {self.regions}")
        
        employment_changes = {}
        
        for sector, demand_change in sector_demands.items():
            if sector not in self.intermediate_sectors:
                # Find similar sectors by checking if any sector contains the search term
                available_sectors = [s for s in self.intermediate_sectors if isinstance(s, str) and sector.lower() in s.lower()]
                raise ValueError(f"Sector '{sector}' not found. Similar sectors: {available_sectors[:5]}")
            
            coefficient = self.employment_coefficients.loc[sector, region]
            employment_change = demand_change * coefficient
            employment_changes[sector] = employment_change
        
        return employment_changes
    
    def calculate_total_employment_impact(
        self,
        sector_demands: Dict[str, float],
        source_region: str = '전지역',
        target_regions: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate total employment impact including indirect effects using multipliers.
        
        Args:
            sector_demands: Dictionary mapping sector names to demand changes (in 10억원)
            source_region: Region where the demand shock occurs
            target_regions: List of regions to analyze impacts (default: all regions)
        
        Returns:
            Nested dictionary: {target_region: {sector: employment_change}}
        """
        if target_regions is None:
            target_regions = self.regions
        
        if source_region not in self.regions:
            raise ValueError(f"Source region '{source_region}' not found.")
        
        total_impacts = {}
        
        for target_region in target_regions:
            total_impacts[target_region] = {}
            
            for sector, demand_change in sector_demands.items():
                if sector not in self.intermediate_sectors:
                    continue
                
                source_key = f"{source_region}_{sector}"
                
                region_impacts = {}
                for target_sector in self.sectors:
                    target_key = f"{target_region}_{target_sector}"
                    
                    if source_key in self.employment_multipliers.index and target_key in self.employment_multipliers.columns:
                        multiplier = self.employment_multipliers.loc[source_key, target_key]
                        impact = demand_change * multiplier
                        region_impacts[target_sector] = impact
                
                total_impacts[target_region] = region_impacts
        
        return total_impacts
    
    def get_sector_employment_coefficients(self, sectors: List[str], region: str = '전지역') -> pd.DataFrame:
        """
        Get employment coefficients for specific sectors and region.
        
        Args:
            sectors: List of sector names
            region: Target region
        
        Returns:
            DataFrame with employment coefficients
        """
        available_sectors = [s for s in sectors if s in self.intermediate_sectors]
        missing_sectors = [s for s in sectors if s not in self.intermediate_sectors]
        
        if missing_sectors:
            print(f"Warning: These sectors were not found: {missing_sectors}")
        
        return self.employment_coefficients.loc[available_sectors, region]
    
    def compare_regional_impacts(
        self,
        sector_demands: Dict[str, float],
        regions: List[str]
    ) -> pd.DataFrame:
        """
        Compare direct employment impacts across different regions.
        
        Args:
            sector_demands: Dictionary mapping sector names to demand changes
            regions: List of regions to compare
        
        Returns:
            DataFrame comparing employment impacts across regions
        """
        comparison_data = {}
        
        for region in regions:
            if region in self.regions:
                impacts = self.calculate_direct_employment_impact(sector_demands, region)
                comparison_data[region] = impacts
        
        return pd.DataFrame(comparison_data).fillna(0)
    
    def summarize_employment_impact(
        self,
        employment_changes: Dict[str, float],
        show_details: bool = True
    ) -> Dict[str, Union[float, Dict]]:
        """
        Summarize employment impact results.
        
        Args:
            employment_changes: Dictionary of sector-wise employment changes
            show_details: Whether to show detailed breakdown
        
        Returns:
            Summary statistics and details
        """
        total_job_creation = sum(change for change in employment_changes.values() if change > 0)
        total_job_loss = sum(change for change in employment_changes.values() if change < 0)
        net_employment_change = sum(employment_changes.values())
        
        summary = {
            'total_job_creation': total_job_creation,
            'total_job_loss': abs(total_job_loss),
            'net_employment_change': net_employment_change,
            'affected_sectors': len(employment_changes)
        }
        
        if show_details:
            summary['sector_details'] = employment_changes
        
        return summary
    
    def find_sectors(self, search_terms: List[str]) -> Dict[str, List[str]]:
        """
        Find sectors matching search terms.
        
        Args:
            search_terms: List of terms to search for in sector names
        
        Returns:
            Dictionary mapping search terms to matching sectors
        """
        results = {}
        for term in search_terms:
            matches = [s for s in self.intermediate_sectors if isinstance(s, str) and term.lower() in s.lower()]
            results[term] = matches
        return results

    def analyze_sector_employment_impact(
        self,
        basic_sector_code: str,
        demand_change: float,
        target_regions: Optional[List[str]] = None,
        include_linkages: bool = True
    ) -> Dict[str, Dict[str, float]]:
        """
        Analyze employment impact of any sub-sector (기본부문) changes.
        
        Methodology:
        1. Use basic sector input-output linkages to identify affected sectors
        2. Map affected basic sectors to intermediate classification (중분류)
        3. Calculate employment effects using intermediate classification employment coefficients
        
        Args:
            basic_sector_code: Basic sector code (e.g., '2711' for pig iron)
            demand_change: Change in sector demand (10억원)
            target_regions: List of regions to analyze (default: all regions)
            include_linkages: Whether to include backward/forward linkages (default: True)
        
        Returns:
            Dictionary: {region: {affected_sector: employment_change}}
        """
        if target_regions is None:
            target_regions = self.regions
        
        # Step 1: Identify sectors affected by the basic sector demand change
        if include_linkages:
            affected_sectors = self._calculate_sectoral_impacts_from_basic_sector(
                basic_sector_code, demand_change
            )
        else:
            # Direct impact only
            affected_sectors = {basic_sector_code: demand_change}
        
        # Step 2: Map affected basic sectors to intermediate classification and aggregate
        intermediate_sector_impacts = self._map_basic_to_intermediate_impacts(affected_sectors)
        
        # Step 3: Calculate employment changes by region using intermediate classification
        regional_employment_impacts = {}
        
        for region in target_regions:
            regional_impacts = {}
            
            for intermediate_sector, demand_change in intermediate_sector_impacts.items():
                if intermediate_sector in self.intermediate_sectors:
                    coefficient = self.employment_coefficients.loc[intermediate_sector, region]
                    employment_change = demand_change * coefficient
                    regional_impacts[intermediate_sector] = employment_change
            
            regional_employment_impacts[region] = regional_impacts
        
        return regional_employment_impacts
    
    def _calculate_sectoral_impacts_from_basic_sector(self, basic_sector_code: str, demand_change: float) -> Dict[str, float]:
        """
        Calculate impacts on all sectors from any basic sector demand change using real IO coefficients.
        
        Args:
            basic_sector_code: Basic sector code (e.g., '2711', '3611', etc.)
            demand_change: Change in final demand (10억원)
        
        Returns:
            Dictionary mapping basic sector codes to output changes
        """
        if self.A_matrix is None:
            # Fallback: direct impact only
            return {basic_sector_code: demand_change}
        
        try:
            # Use proper Leontief inverse calculation: (I - A)^(-1) * Δf
            return self._calculate_leontief_impacts(basic_sector_code, demand_change)
            
        except Exception as e:
            print(f"Warning: Using fallback calculation: {str(e)}")
            return {basic_sector_code: demand_change}
    
    def _calculate_leontief_impacts(self, basic_sector_code: str, demand_change: float) -> Dict[str, float]:
        """
        Calculate sectoral impacts using Leontief inverse: (I - A)^(-1) * Δf
        
        Args:
            basic_sector_code: Target sector for demand shock
            demand_change: Change in final demand
        
        Returns:
            Dictionary mapping sector codes to output changes
        """
        try:
            # Get sector index in the A matrix - handle both string and int codes
            sector_codes = [str(idx[0]) if isinstance(idx, tuple) else str(idx) for idx in self.A_matrix.index]
            basic_sector_str = str(basic_sector_code)
            
            if basic_sector_str not in sector_codes:
                print(f"Warning: Sector {basic_sector_str} not found in A matrix")
                return {basic_sector_str: demand_change}
            
            # Ensure A matrix is square by using minimum dimension
            n_rows, n_cols = self.A_matrix.shape
            matrix_size = min(n_rows, n_cols)
            
            # Truncate matrix and sector codes to square dimensions
            A_square = self.A_matrix.iloc[:matrix_size, :matrix_size].fillna(0).values
            sector_codes_square = sector_codes[:matrix_size]
            
            # Create final demand shock vector for square matrix
            final_demand_shock = np.zeros(matrix_size)
            if basic_sector_str in sector_codes_square:
                shock_index = sector_codes_square.index(basic_sector_str)
                final_demand_shock[shock_index] = demand_change
            else:
                print(f"Warning: Sector {basic_sector_str} not in square matrix")
                return {basic_sector_str: demand_change}
            
            # Calculate (I - A) matrix
            I_minus_A = np.eye(matrix_size) - A_square
            
            # Calculate Leontief inverse: (I - A)^(-1)
            try:
                leontief_inverse = np.linalg.inv(I_minus_A)
            except np.linalg.LinAlgError:
                # If matrix is singular, use pseudo-inverse
                leontief_inverse = np.linalg.pinv(I_minus_A)
            
            # Calculate output impacts: (I - A)^(-1) * Δf
            output_impacts = leontief_inverse @ final_demand_shock
            
            # Convert to dictionary format
            sectoral_impacts = {}
            for i, sector in enumerate(sector_codes_square):
                if abs(output_impacts[i]) > 0.01:  # Only include significant impacts
                    sectoral_impacts[sector] = output_impacts[i]
            
            return sectoral_impacts
            
        except Exception as e:
            print(f"Error in Leontief calculation: {str(e)}")
            return {basic_sector_code: demand_change}
    
    def get_sector_linkages(self, basic_sector_code: str, linkage_type: str = 'backward') -> Dict[str, float]:
        """
        Get backward or forward linkages for a specific sector using IO coefficients.
        
        Args:
            basic_sector_code: Target sector code
            linkage_type: 'backward' or 'forward'
        
        Returns:
            Dictionary of sector linkages
        """
        if self.A_matrix is None:
            return {}
        
        try:
            sector_codes = [idx[0] if isinstance(idx, tuple) else idx for idx in self.A_matrix.index]
            
            if basic_sector_code not in sector_codes:
                return {}
            
            if linkage_type == 'backward':
                # Backward linkages: what this sector buys from others
                sector_idx = sector_codes.index(basic_sector_code)
                linkages = self.A_matrix.iloc[:, sector_idx].fillna(0)
                return {sector_codes[i]: linkages.iloc[i] for i in range(len(linkages)) if linkages.iloc[i] > 0.001}
            
            elif linkage_type == 'forward':
                # Forward linkages: what other sectors buy from this sector  
                sector_idx = sector_codes.index(basic_sector_code)
                linkages = self.A_matrix.iloc[sector_idx, :].fillna(0)
                return {sector_codes[i]: linkages.iloc[i] for i in range(len(linkages)) if linkages.iloc[i] > 0.001}
            
        except Exception as e:
            print(f"Error calculating linkages: {str(e)}")
            return {}
    
    def _map_basic_to_intermediate_impacts(self, basic_sector_impacts: Dict[str, float]) -> Dict[str, float]:
        """
        Map basic sector impacts to intermediate classification and aggregate using real sector mapping.
        
        Args:
            basic_sector_impacts: Dictionary of basic sector impacts
        
        Returns:
            Dictionary of intermediate classification impacts
        """
        intermediate_impacts = {}
        
        for basic_sector, impact in basic_sector_impacts.items():
            # Convert to string for consistent handling
            basic_sector_str = str(basic_sector)
            
            # Use real sector mapping if available
            if hasattr(self, 'basic_to_intermediate_map') and basic_sector_str in self.basic_to_intermediate_map:
                intermediate_sector = self.basic_to_intermediate_map[basic_sector_str]
            else:
                # Fallback to pattern-based mapping
                if basic_sector_str.startswith('27'):
                    intermediate_sector = '27: 철강1차제품'
                elif basic_sector_str.startswith('28'):
                    intermediate_sector = '28: 비철금속괴 및 1차제품'
                elif basic_sector_str.startswith('05'):
                    intermediate_sector = '05: 석탄 및 금속광물'
                elif basic_sector_str.startswith('20'):
                    intermediate_sector = '20: 석유정제품'
                elif basic_sector_str.startswith('35'):
                    intermediate_sector = '35: 전력'
                else:
                    intermediate_sector = f'{basic_sector_str[:2]}: 기타제조업'
            
            # Aggregate impacts by intermediate classification
            if intermediate_sector in intermediate_impacts:
                intermediate_impacts[intermediate_sector] += impact
            else:
                intermediate_impacts[intermediate_sector] = impact
        
        return intermediate_impacts
    
    def summarize_sector_analysis(
        self,
        regional_impacts: Dict[str, Dict[str, float]],
        basic_sector_code: str,
        demand_change: float
    ) -> Dict[str, Union[float, Dict]]:
        """
        Summarize sector employment impact analysis results.
        
        Args:
            regional_impacts: Regional employment impacts from analyze_sector_employment_impact
            basic_sector_code: Original basic sector code analyzed
            demand_change: Original demand change amount
        
        Returns:
            Summary with total impacts and regional breakdown
        """
        total_employment_change = 0
        regional_totals = {}
        
        for region, impacts in regional_impacts.items():
            regional_total = sum(impacts.values())
            regional_totals[region] = regional_total
            total_employment_change += regional_total
        
        # Calculate employment intensity (jobs per billion won)
        employment_intensity = total_employment_change / demand_change if demand_change != 0 else 0
        
        summary = {
            'basic_sector_code': basic_sector_code,
            'demand_change_billion_won': demand_change,
            'total_employment_change': total_employment_change,
            'employment_intensity_per_billion_won': employment_intensity,
            'regional_totals': regional_totals,
            'affected_regions': len([r for r, total in regional_totals.items() if abs(total) > 1]),
            'detailed_impacts': regional_impacts
        }
        
        return summary
    
    def get_available_basic_sectors(self, search_term: str = None) -> List[str]:
        """
        Get list of available basic sectors (기본부문).
        
        Args:
            search_term: Optional search term to filter sectors
        
        Returns:
            List of basic sector codes and names
        """
        if self.basic_sectors is None:
            return []
        
        if search_term is None:
            return self.basic_sectors
        else:
            return [s for s in self.basic_sectors if search_term.lower() in str(s).lower()]
    
    def get_available_regions(self) -> List[str]:
        """Get list of available regions."""
        return self.regions if self.regions else []
    
    def get_sector_hierarchy_info(self) -> Dict[str, Union[List[str], int]]:
        """Get information about sector hierarchy."""
        return {
            'industry_sectors': list(self.sector_hierarchy.get('industry_to_intermediate', {}).keys()),
            'intermediate_sectors': self.intermediate_sectors,
            'total_basic_sectors': len(self.basic_sectors) if self.basic_sectors else 0,
            'io_coefficients_loaded': self.A_matrix is not None,
            'import_domestic_split_available': self.Am_matrix is not None and self.Ad_matrix is not None
        }
    
    def analyze_sector_linkages(self, basic_sector_code: str) -> Dict[str, Dict[str, float]]:
        """
        Analyze backward and forward linkages for a specific sector.
        
        Args:
            basic_sector_code: Basic sector code to analyze
        
        Returns:
            Dictionary with backward and forward linkages
        """
        return {
            'backward_linkages': self.get_sector_linkages(basic_sector_code, 'backward'),
            'forward_linkages': self.get_sector_linkages(basic_sector_code, 'forward')
        }

def interactive_sector_analysis():
    """Interactive user interface for sector employment impact analysis."""
    
    # Initialize calculator
    calculator = EmploymentCalculator(
        'iotable/2020지역_부속표_고용표_통합중분류.xlsx',
        'iotable/(표)(2020실측)투입산출표_기초가격_기본부문.xlsx'
    )
    
    print("=== 한국 산업연관표 기반 고용영향분석 시스템 ===\n")
    
    # Show system info
    hierarchy_info = calculator.get_sector_hierarchy_info()
    print(f"사용 가능한 데이터:")
    print(f"- 기본부문 (basic_sectors): {hierarchy_info['total_basic_sectors']}개")
    print(f"- 중분류 (intermediate_sectors): {len(hierarchy_info['intermediate_sectors'])}개") 
    print(f"- 대분류 (industry_sectors): {len(hierarchy_info['industry_sectors'])}개")
    print(f"- 분석 지역: {len(calculator.get_available_regions())}개")
    print(f"- IO 계수 로딩: {'✓' if hierarchy_info['io_coefficients_loaded'] else '✗'}")
    print(f"- 수입/국산 분리: {'✓' if hierarchy_info['import_domestic_split_available'] else '✗'}")
    
    print(f"\n대분류 산업 목록:")
    for industry in hierarchy_info['industry_sectors']:
        print(f"  - {industry}")
    
    print(f"\n분석 가능 지역:")
    regions = calculator.get_available_regions()
    for i, region in enumerate(regions):
        if i < 10:  # Show first 10 regions
            print(f"  - {region}")
        elif i == 10:
            print(f"  ... 총 {len(regions)}개 지역")
            break
    
    return calculator

def run_sector_analysis(basic_sector_code: str, demand_change: float, 
                       target_regions: List[str] = None, include_linkages: bool = True):
    """
    Run employment impact analysis for any basic sector.
    
    Args:
        basic_sector_code: Basic sector code (e.g., '2711' for pig iron)
        demand_change: Demand change in 10억원 (positive for increase, negative for decrease)
        target_regions: List of regions to analyze (default: all regions)
        include_linkages: Include backward linkages (default: True)
    
    Returns:
        Dictionary with analysis results
    """
    calculator = EmploymentCalculator(
        'iotable/2020지역_부속표_고용표_통합중분류.xlsx',
        'iotable/(표)(2020실측)투입산출표_기초가격_기본부문.xlsx'
    )
    
    # Run analysis
    regional_impacts = calculator.analyze_sector_employment_impact(
        basic_sector_code=basic_sector_code,
        demand_change=demand_change,
        target_regions=target_regions,
        include_linkages=include_linkages
    )
    
    # Summarize results
    summary = calculator.summarize_sector_analysis(
        regional_impacts, basic_sector_code, demand_change
    )
    
    return {
        'calculator': calculator,
        'regional_impacts': regional_impacts,
        'summary': summary
    }

def example_steel_analysis():
    """Example: Steel industry (pig iron) employment impact analysis."""
    
    print("=== 예시: 선철 산업 고용영향 분석 ===\n")
    
    # First, let's explore available steel-related sectors
    calculator = EmploymentCalculator(
        'iotable/2020지역_부속표_고용표_통합중분류.xlsx',
        'iotable/(표)(2020실측)투입산출표_기초가격_기본부문.xlsx'
    )
    
    # Find steel-related sectors in the A matrix
    if calculator.A_matrix is not None:
        sector_codes = [idx[0] if isinstance(idx, tuple) else idx for idx in calculator.A_matrix.index]
        steel_sectors = [s for s in sector_codes if '27' in str(s) or '선철' in str(s) or '철강' in str(s)]
        print(f"Available steel-related sectors: {steel_sectors[:10]}")
        
        # Use first available steel sector
        if steel_sectors:
            steel_sector = steel_sectors[0]
            print(f"Using sector: {steel_sector}")
        else:
            steel_sector = '2711'  # Fallback
    else:
        steel_sector = '2711'
    
    # Analyze steel sector with 1000억원 decrease
    results = run_sector_analysis(
        basic_sector_code=steel_sector,
        demand_change=-1000,       # -1000 billion won
        target_regions=['전지역', '경기', '충남', '울산', '강원'],
        include_linkages=True
    )
    
    summary = results['summary']
    regional_impacts = results['regional_impacts']
    
    print(f"분석 대상: 기본부문 {summary['basic_sector_code']} (선철)")
    print(f"수요 변화: {summary['demand_change_billion_won']:,.0f}억원")
    print(f"총 고용 변화: {summary['total_employment_change']:,.0f}명")
    print(f"고용 집약도: {summary['employment_intensity_per_billion_won']:.2f}명/천억원")
    
    print("\n=== 지역별 고용 영향 ===")
    for region, total_impact in summary['regional_totals'].items():
        if abs(total_impact) > 1:
            print(f"{region}: {total_impact:,.0f}명")
    
    print("\n=== 부문별 상세 영향 (전지역) ===")
    if '전지역' in regional_impacts:
        for sector, impact in regional_impacts['전지역'].items():
            if abs(impact) > 1:  # Show sectors with >1 job impact
                print(f"  {sector}: {impact:,.0f}명")
    
    # Show linkage analysis if IO coefficients are available
    if results['calculator'].A_matrix is not None:
        print(f"\n=== {steel_sector} 부문 연관관계 분석 ===")
        linkages = results['calculator'].analyze_sector_linkages(steel_sector)
        
        print("\n주요 후방연관 (이 부문이 구매하는 투입재):")
        backward = linkages['backward_linkages']
        sorted_backward = sorted(backward.items(), key=lambda x: x[1], reverse=True)[:5]
        for sector, coeff in sorted_backward:
            if coeff > 0.001:
                print(f"  {sector}: {coeff:.4f}")
        
        print("\n주요 전방연관 (이 부문 생산물을 구매하는 부문):")
        forward = linkages['forward_linkages']
        sorted_forward = sorted(forward.items(), key=lambda x: x[1], reverse=True)[:5]
        for sector, coeff in sorted_forward:
            if coeff > 0.001:
                print(f"  {sector}: {coeff:.4f}")
    
    return results

if __name__ == "__main__":
    # Show interactive interface
    interactive_sector_analysis()
    print("\n" + "="*50)
    
    # Run example analysis
    example_steel_analysis()