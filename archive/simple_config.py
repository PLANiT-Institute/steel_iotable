"""
Simple Configuration System for Enhanced Sector Impact Analyzer
Uses YAML for easy configuration management
"""

import yaml
import os
from typing import Dict, Any

class Config:
    """Simple configuration class that loads from YAML"""
    
    def __init__(self, config_file: str = "config.yaml"):
        """
        Initialize configuration from YAML file
        
        Args:
            config_file: Path to YAML configuration file
        """
        self.config_file = config_file
        self.data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            if not os.path.exists(self.config_file):
                print(f"Warning: Config file {self.config_file} not found. Using defaults.")
                return self._get_default_config()
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config if config else self._get_default_config()
                
        except Exception as e:
            print(f"Warning: Error loading config file: {str(e)}. Using defaults.")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if YAML file is not available"""
        return {
            'files': {
                'basic_io_file': 'iotable/(표)(2020실측)투입산출표_기초가격_기본부문.xlsx',
                'employment_file': 'iotable/2020지역_부속표_고용표_통합중분류.xlsx'
            },
            'defaults': {
                'reduction_amount': 1000,
                'target_region': '전지역',
                'demand_change': 1000
            },
            'analysis': {
                'supply_chain': True,
                'employment': True,
                'import_domestic': True,
                'comprehensive': True
            },
            'display': {
                'table_rows': 15,
                'matrix_rows': 15,
                'max_sectors_display': 2,
                'max_sectors_export': 5,
                'search_results': 20,
                'steel_sector_name': 30,
                'coal_sector_name': 40,
                'excel_sheet_name': 31
            },
            'thresholds': {
                'employment_impact': 0.1,
                'economic_magnitude': 1.5,
                'employment_significance': 100,
                'import_dependency': 0.5,
                'fiscal_significance': 0.1,
                'co2_conversion': 1000
            },
            'sectors': {
                'steel_keywords': ['철강', '제철', '선철'],
                'coal_keywords': ['석탄', '코크스'],
                'coal_matching': ['석탄', '코크스', 'coal', 'coke']
            },
            'menu': {
                'options': [
                    '1. Comprehensive sector analysis',
                    '2. Steel-coal supply chain (comprehensive)', 
                    '3. Import vs Domestic impact comparison',
                    '4. Environmental impact analysis',
                    '5. Comprehensive analysis with IO tables',
                    '6. Steel-coal analysis with IO tables',
                    '7. Search sectors',
                    '8. Exit'
                ],
                'max_choice': 8
            },
            'assessment': {
                'environmental_concern': 'low'
            }
        }
    
    def get(self, key: str, default=None):
        """Get configuration value using dot notation (e.g., 'files.basic_io_file')"""
        keys = key.split('.')
        value = self.data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def save(self, config_file: str = None):
        """Save current configuration to YAML file"""
        if config_file is None:
            config_file = self.config_file
            
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.data, f, default_flow_style=False, allow_unicode=True)
            print(f"Configuration saved to {config_file}")
        except Exception as e:
            print(f"Error saving configuration: {str(e)}")

# Global configuration instance
CONFIG = Config()

# Convenience functions
def get_config(key: str, default=None):
    """Get configuration value"""
    return CONFIG.get(key, default)

def reload_config():
    """Reload configuration from file"""
    global CONFIG
    CONFIG = Config()
    return CONFIG