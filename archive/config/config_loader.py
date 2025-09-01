#!/usr/bin/env python3
"""
Configuration loader utility for Enhanced Sector Impact Analyzer
"""

import json
import yaml
import os
from typing import Dict, Any, Optional
from .analysis_config import AnalysisConfig, DEFAULT_CONFIG

class ConfigLoader:
    """Utility class for loading configurations from various sources"""
    
    @staticmethod
    def load_from_dict(config_dict: Dict[str, Any]) -> AnalysisConfig:
        """Load configuration from dictionary"""
        return AnalysisConfig.from_dict(config_dict)
    
    @staticmethod
    def load_from_json(file_path: str) -> AnalysisConfig:
        """Load configuration from JSON file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        return AnalysisConfig.from_dict(config_dict)
    
    @staticmethod
    def load_from_yaml(file_path: str) -> AnalysisConfig:
        """Load configuration from YAML file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
        
        return AnalysisConfig.from_dict(config_dict)
    
    @staticmethod
    def save_to_json(config: AnalysisConfig, file_path: str) -> None:
        """Save configuration to JSON file"""
        config_dict = config.to_dict()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def save_to_yaml(config: AnalysisConfig, file_path: str) -> None:
        """Save configuration to YAML file"""
        config_dict = config.to_dict()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
    
    @staticmethod
    def load_config(config_source: Optional[str] = None) -> AnalysisConfig:
        """
        Load configuration from various sources with fallback to default
        
        Args:
            config_source: Path to config file (JSON/YAML) or None for default
            
        Returns:
            AnalysisConfig instance
        """
        if config_source is None:
            return DEFAULT_CONFIG
        
        if not os.path.exists(config_source):
            print(f"Warning: Configuration file {config_source} not found. Using default configuration.")
            return DEFAULT_CONFIG
        
        try:
            if config_source.endswith('.json'):
                return ConfigLoader.load_from_json(config_source)
            elif config_source.endswith(('.yml', '.yaml')):
                return ConfigLoader.load_from_yaml(config_source)
            else:
                print(f"Warning: Unsupported configuration file format: {config_source}. Using default configuration.")
                return DEFAULT_CONFIG
        except Exception as e:
            print(f"Error loading configuration from {config_source}: {str(e)}")
            print("Using default configuration.")
            return DEFAULT_CONFIG

# Example configuration templates
def create_steel_analysis_config() -> AnalysisConfig:
    """Create configuration optimized for steel industry analysis"""
    config_dict = {
        'file_paths': {
            'basic_io_file': 'iotable/(표)(2020실측)투입산출표_기초가격_기본부문.xlsx',
            'employment_file': 'iotable/2020지역_부속표_고용표_통합중분류.xlsx'
        },
        'thresholds': {
            'employment_impact_threshold': 0.1,
            'economic_magnitude_multiplier': 1.5,
            'employment_significance_threshold': 100,
            'import_dependency_threshold': 0.5,
            'fiscal_significance_multiplier': 0.1,
            'co2_conversion_factor': 1000.0
        },
        'display_limits': {
            'default_table_rows': 20,
            'default_matrix_rows': 15,
            'steel_sector_name_limit': 40,
            'coal_sector_name_limit': 50,
            'max_sectors_to_display': 3,
            'max_sectors_for_export': 8,
            'excel_sheet_name_limit': 31,
            'search_results_limit': 25,
            'search_overflow_threshold': 25
        },
        'default_values': {
            'default_reduction_amount': 1000.0,
            'default_demand_change': 1.0,
            'default_target_region': '전지역'
        },
        'sector_keywords': {
            'steel_keywords': ['철강', '제철', '선철', '강철'],
            'coal_keywords': ['석탄', '코크스'],
            'coal_matching_keywords': ['석탄', '코크스', 'coal', 'coke']
        },
        'assessment_levels': {
            'environmental_concern_levels': ['low', 'medium', 'high'],
            'economic_magnitude_levels': ['low', 'medium', 'high'],
            'employment_significance_levels': ['low', 'medium', 'high'],
            'trade_implication_types': ['import_dependent', 'domestic_focused'],
            'fiscal_significance_levels': ['low', 'medium', 'high'],
            'default_environmental_concern': 'low'
        },
        'analysis_options': {
            'default_supply_chain': True,
            'default_employment': True,
            'default_import_domestic': True,
            'default_comprehensive': True
        },
        'interactive_options': {
            'menu_options': [
                "1. Comprehensive sector analysis",
                "2. Steel-coal supply chain (comprehensive)",
                "3. Import vs Domestic impact comparison",
                "4. Environmental impact analysis",
                "5. Comprehensive analysis with IO tables",
                "6. Steel-coal analysis with IO tables",
                "7. Search sectors",
                "8. Exit"
            ],
            'max_menu_choice': 8
        }
    }
    
    return AnalysisConfig.from_dict(config_dict)

def create_detailed_analysis_config() -> AnalysisConfig:
    """Create configuration for detailed analysis with more data"""
    config_dict = {
        'file_paths': {
            'basic_io_file': 'iotable/(표)(2020실측)투입산출표_기초가격_기본부문.xlsx',
            'employment_file': 'iotable/2020지역_부속표_고용표_통합중분류.xlsx'
        },
        'thresholds': {
            'employment_impact_threshold': 0.05,  # More sensitive
            'economic_magnitude_multiplier': 1.2,  # More sensitive
            'employment_significance_threshold': 50,  # More sensitive
            'import_dependency_threshold': 0.3,  # More sensitive
            'fiscal_significance_multiplier': 0.05,  # More sensitive
            'co2_conversion_factor': 1000.0
        },
        'display_limits': {
            'default_table_rows': 30,  # More rows
            'default_matrix_rows': 25,  # More rows
            'steel_sector_name_limit': 60,  # Longer names
            'coal_sector_name_limit': 70,  # Longer names
            'max_sectors_to_display': 5,  # More sectors
            'max_sectors_for_export': 15,  # More export
            'excel_sheet_name_limit': 31,
            'search_results_limit': 50,  # More results
            'search_overflow_threshold': 50
        },
        'default_values': {
            'default_reduction_amount': 500.0,  # Smaller default
            'default_demand_change': 1.0,
            'default_target_region': '전지역'
        },
        'sector_keywords': {
            'steel_keywords': ['철강', '제철', '선철', '강철', '스테인리스', '합금'],
            'coal_keywords': ['석탄', '코크스', '연탄'],
            'coal_matching_keywords': ['석탄', '코크스', 'coal', 'coke', '연탄', 'briquette']
        },
        'assessment_levels': {
            'environmental_concern_levels': ['very_low', 'low', 'medium', 'high', 'very_high'],
            'economic_magnitude_levels': ['very_low', 'low', 'medium', 'high', 'very_high'],
            'employment_significance_levels': ['very_low', 'low', 'medium', 'high', 'very_high'],
            'trade_implication_types': ['import_dependent', 'balanced', 'domestic_focused'],
            'fiscal_significance_levels': ['very_low', 'low', 'medium', 'high', 'very_high'],
            'default_environmental_concern': 'medium'
        },
        'analysis_options': {
            'default_supply_chain': True,
            'default_employment': True,
            'default_import_domestic': True,
            'default_comprehensive': True
        },
        'interactive_options': {
            'menu_options': [
                "1. Comprehensive sector analysis",
                "2. Steel-coal supply chain (comprehensive)",
                "3. Import vs Domestic impact comparison",
                "4. Environmental impact analysis",
                "5. Comprehensive analysis with IO tables",
                "6. Steel-coal analysis with IO tables",
                "7. Search sectors",
                "8. Advanced sector comparison",
                "9. Export all results",
                "10. Exit"
            ],
            'max_menu_choice': 10
        }
    }
    
    return AnalysisConfig.from_dict(config_dict)