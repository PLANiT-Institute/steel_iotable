#!/usr/bin/env python3
"""
Configuration file for Enhanced Sector Impact Analyzer
Eliminates all hardcoded values and makes them configurable
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass, field

@dataclass
class FilePaths:
    """Configuration for file paths"""
    basic_io_file: str = 'iotable/(표)(2020실측)투입산출표_기초가격_기본부문.xlsx'
    employment_file: str = 'iotable/2020지역_부속표_고용표_통합중분류.xlsx'
    
    def __post_init__(self):
        """Validate file paths exist"""
        if not os.path.exists(self.basic_io_file):
            raise FileNotFoundError(f"Basic IO file not found: {self.basic_io_file}")
        if not os.path.exists(self.employment_file):
            raise FileNotFoundError(f"Employment file not found: {self.employment_file}")

@dataclass
class AnalysisThresholds:
    """Configuration for analysis thresholds"""
    employment_impact_threshold: float = 0.01  # Lowered from 0.1 to catch smaller impacts
    economic_magnitude_multiplier: float = 1.5
    employment_significance_threshold: int = 1   # Lowered from 100 to 1 job to be more sensitive
    import_dependency_threshold: float = 0.5
    fiscal_significance_multiplier: float = 0.1
    co2_conversion_factor: float = 1000.0  # Convert thousand tons to tons

@dataclass
class DisplayLimits:
    """Configuration for display and export limits"""
    default_table_rows: int = 15
    default_matrix_rows: int = 15
    steel_sector_name_limit: int = 30
    coal_sector_name_limit: int = 40
    max_sectors_to_display: int = 2
    max_sectors_for_export: int = 5
    excel_sheet_name_limit: int = 31
    search_results_limit: int = 20
    search_overflow_threshold: int = 20

@dataclass
class DefaultValues:
    """Configuration for default values"""
    default_reduction_amount: float = 1000.0
    default_demand_change: float = 1.0
    default_target_region: str = '전지역'

@dataclass
class SectorKeywords:
    """Configuration for sector search keywords"""
    steel_keywords: List[str] = field(default_factory=lambda: ['철강', '제철', '선철'])
    coal_keywords: List[str] = field(default_factory=lambda: ['석탄', '코크스'])
    coal_matching_keywords: List[str] = field(default_factory=lambda: ['석탄', '코크스', 'coal', 'coke'])

@dataclass
class AssessmentLevels:
    """Configuration for assessment levels and thresholds"""
    environmental_concern_levels: List[str] = field(default_factory=lambda: ['low', 'medium', 'high'])
    economic_magnitude_levels: List[str] = field(default_factory=lambda: ['low', 'medium', 'high'])
    employment_significance_levels: List[str] = field(default_factory=lambda: ['low', 'medium', 'high'])
    trade_implication_types: List[str] = field(default_factory=lambda: ['import_dependent', 'domestic_focused'])
    fiscal_significance_levels: List[str] = field(default_factory=lambda: ['low', 'medium', 'high'])
    
    # Default assessment values
    default_environmental_concern: str = 'low'

@dataclass
class AnalysisOptions:
    """Configuration for default analysis options"""
    default_supply_chain: bool = True
    default_employment: bool = True
    default_import_domestic: bool = True
    default_comprehensive: bool = True

@dataclass
class InteractiveOptions:
    """Configuration for interactive menu options"""
    menu_options: List[str] = field(default_factory=lambda: [
        "1. Comprehensive sector analysis",
        "2. Steel-coal supply chain (comprehensive)",
        "3. Import vs Domestic impact comparison",
        "4. Environmental impact analysis",
        "5. Comprehensive analysis with IO tables",
        "6. Steel-coal analysis with IO tables",
        "7. Search sectors",
        "8. Exit"
    ])
    max_menu_choice: int = 8

@dataclass
class AnalysisConfig:
    """Main configuration class that combines all configuration sections"""
    file_paths: FilePaths = field(default_factory=FilePaths)
    thresholds: AnalysisThresholds = field(default_factory=AnalysisThresholds)
    display_limits: DisplayLimits = field(default_factory=DisplayLimits)
    default_values: DefaultValues = field(default_factory=DefaultValues)
    sector_keywords: SectorKeywords = field(default_factory=SectorKeywords)
    assessment_levels: AssessmentLevels = field(default_factory=AssessmentLevels)
    analysis_options: AnalysisOptions = field(default_factory=AnalysisOptions)
    interactive_options: InteractiveOptions = field(default_factory=InteractiveOptions)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'AnalysisConfig':
        """Create configuration from dictionary"""
        return cls(
            file_paths=FilePaths(**config_dict.get('file_paths', {})),
            thresholds=AnalysisThresholds(**config_dict.get('thresholds', {})),
            display_limits=DisplayLimits(**config_dict.get('display_limits', {})),
            default_values=DefaultValues(**config_dict.get('default_values', {})),
            sector_keywords=SectorKeywords(**config_dict.get('sector_keywords', {})),
            assessment_levels=AssessmentLevels(**config_dict.get('assessment_levels', {})),
            analysis_options=AnalysisOptions(**config_dict.get('analysis_options', {})),
            interactive_options=InteractiveOptions(**config_dict.get('interactive_options', {}))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'file_paths': self.file_paths.__dict__,
            'thresholds': self.thresholds.__dict__,
            'display_limits': self.display_limits.__dict__,
            'default_values': self.default_values.__dict__,
            'sector_keywords': self.sector_keywords.__dict__,
            'assessment_levels': self.assessment_levels.__dict__,
            'analysis_options': self.analysis_options.__dict__,
            'interactive_options': self.interactive_options.__dict__
        }
    
    def validate(self) -> bool:
        """Validate configuration values"""
        # Validate thresholds are positive
        if self.thresholds.employment_impact_threshold < 0:
            raise ValueError("Employment impact threshold must be positive")
        if self.thresholds.economic_magnitude_multiplier <= 0:
            raise ValueError("Economic magnitude multiplier must be positive")
        if self.thresholds.employment_significance_threshold < 0:
            raise ValueError("Employment significance threshold must be non-negative")
        if not 0 <= self.thresholds.import_dependency_threshold <= 1:
            raise ValueError("Import dependency threshold must be between 0 and 1")
        if self.thresholds.fiscal_significance_multiplier < 0:
            raise ValueError("Fiscal significance multiplier must be non-negative")
        if self.thresholds.co2_conversion_factor <= 0:
            raise ValueError("CO2 conversion factor must be positive")
        
        # Validate display limits are positive
        for attr_name in dir(self.display_limits):
            if not attr_name.startswith('_'):
                value = getattr(self.display_limits, attr_name)
                if isinstance(value, int) and value <= 0:
                    raise ValueError(f"Display limit {attr_name} must be positive")
        
        # Validate default values
        if self.default_values.default_reduction_amount < 0:
            raise ValueError("Default reduction amount must be non-negative")
        if self.default_values.default_demand_change <= 0:
            raise ValueError("Default demand change must be positive")
        
        return True

# Default configuration instance
DEFAULT_CONFIG = AnalysisConfig()

# Configuration validation
DEFAULT_CONFIG.validate()