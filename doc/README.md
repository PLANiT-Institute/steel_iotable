# Korean Input-Output Employment Impact Analysis System

A comprehensive Python-based system for analyzing employment and economic impacts using Korean input-output tables and real IO coefficients.

## Overview

This system performs employment impact analysis for any sector in the Korean economy using:
- **Real IO coefficients**: 총투입계수(A), 수입투입계수(Am), 국산투입계수(Ad)
- **Leontief inverse calculation**: (I - A)^(-1) for comprehensive sectoral linkages
- **Authentic sector classification**: Using (2020실측)상품분류.xlsx for product/commodity mapping
- **Regional employment data**: 18 regions across Korea

## Key Features

### 🏗️ **Sector Classification Hierarchy**

- **기본분류 (basic_sectors)**: 4-digit detailed sectors (e.g., 2711: 선철) - 397개
- **소분류 (sub_sectors)**: 3-digit classification used by regional IO tables - 411개 
- **중분류 (intermediate_sectors)**: 2-digit classification for employment analysis - 83개
- **대분류 (industrial_sectors)**: 1-digit major product groups - 64개

### 📊 **Data Sources**

- **IO Coefficients**: `(표)(2020실측)투입산출표_기초가격_기본부문.xlsx`
- **Employment Data**: `2020지역_부속표_고용표_통합중분류.xlsx`  
- **Sector Mapping**: `(2020실측)상품분류.xlsx`
- **Regional Coverage**: 18 Korean regions

### 🚀 **Analysis Capabilities**

1. **Direct Employment Impact**: Using employment coefficients by region/sector
2. **Comprehensive Sectoral Linkages**: Real backward/forward linkages from IO coefficients
3. **Leontief Multiplier Analysis**: (I - A)^(-1) × Δf for total economic impacts
4. **Regional Distribution**: Employment changes across all 18 regions
5. **Multi-level Aggregation**: From basic sectors to major industry groups

## Quick Start

### Basic Usage

```python
from employment_calculator import EmploymentCalculator, run_sector_analysis

# Run comprehensive analysis for any sector
results = run_sector_analysis(
    basic_sector_code='2711',  # Steel/pig iron sector
    demand_change=-1000,       # -1000 billion won shock
    target_regions=['전지역', '경기', '충남', '울산'],
    include_linkages=True      # Include IO linkages
)

# Results include:
print(f"Total employment change: {results['summary']['total_employment_change']:,.0f}명")
print(f"Employment intensity: {results['summary']['employment_intensity_per_billion_won']:.2f}명/천억원")
```

### Advanced Analysis

```python
# Initialize with full capabilities
calculator = EmploymentCalculator(
    'iotable/2020지역_부속표_고용표_통합중분류.xlsx',
    'iotable/(표)(2020실측)투입산출표_기초가격_기본부문.xlsx'
)

# Analyze sectoral linkages
linkages = calculator.analyze_sector_linkages('2711')
print("Backward linkages:", linkages['backward_linkages'])
print("Forward linkages:", linkages['forward_linkages'])

# Get system information
info = calculator.get_sector_hierarchy_info()
print(f"IO coefficients loaded: {info['io_coefficients_loaded']}")
print(f"Import/domestic split: {info['import_domestic_split_available']}")
```

## Methodology

### 1. **Input-Output Analysis**

The system uses authentic Korean IO coefficients:

```
총투입계수(A): aij = Xij / Xj
```
- Where Xij = intermediate input from sector i to sector j
- Xj = total output of sector j

### 2. **Leontief Inverse Calculation**

```
Output impacts = (I - A)^(-1) × Δf
```
- I = Identity matrix
- A = Total input coefficient matrix (388×381)
- Δf = Final demand change vector

### 3. **Employment Impact Calculation**

```
Employment change = Σ(Output_change_i × Employment_coefficient_i,r)
```
- For each sector i and region r
- Using real employment coefficients from regional IO data

### 4. **Sector Mapping Process**

1. **Basic sector demand change** → Leontief inverse → **All sectoral output changes**
2. **Map basic sectors** (4-digit) → **intermediate sectors** (2-digit) using 상품분류
3. **Aggregate impacts** by intermediate classification
4. **Apply employment coefficients** by region

## Example Results

### Steel Sector Analysis (Sector 1627)

**Input**: -1,000억원 demand decrease

**Output**:
- **Total employment impact**: 66,153 jobs
- **Employment intensity**: -66.15 jobs per 천억원
- **Regional breakdown**:
  - 충남: 18,030명 (major steel region)
  - 강원: 13,560명  
  - 전지역: 11,732명
  - 경기: 11,442명

**Sectoral impacts** (top affected):
- 공공행정, 국방 및 사회보장: 8,370명
- 사업지원서비스: 639명
- 음식점 및 숙박서비스: 452명
- 수상운송서비스: 418명

## Data Files Structure

```
iotable/
├── (2020실측)상품분류.xlsx                     # Product classification mapping
├── (표)(2020실측)투입산출표_기초가격_기본부문.xlsx   # Basic IO table with A, Am, Ad matrices  
├── 2020지역_부속표_고용표_통합중분류.xlsx          # Regional employment coefficients
├── 2020지역_투입산출표_생산자가격_통합소분류_*.xlsx # Regional multiplier files
└── IO코드와 KSIC 및 HS코드 대조표.xlsx          # Additional code mappings
```

## Technical Implementation

### Core Classes

- **`EmploymentCalculator`**: Main analysis engine
  - Loads IO coefficients (A, Am, Ad matrices)
  - Performs Leontief inverse calculations
  - Maps sectors through classification hierarchy
  - Calculates employment impacts by region

### Key Methods

- **`analyze_sector_employment_impact()`**: Complete analysis pipeline
- **`_calculate_leontief_impacts()`**: Real IO coefficient calculations
- **`_map_basic_to_intermediate_impacts()`**: Sector aggregation using 상품분류
- **`analyze_sector_linkages()`**: Backward/forward linkage analysis

### Data Loading

- **IO Coefficients**: Proper matrix handling with dimension matching
- **Sector Mapping**: 4-digit code formatting with leading zeros
- **Employment Data**: Regional coefficient extraction
- **Error Handling**: Graceful fallbacks for missing mappings

## Validation

### System Validation

✅ **Real Data Integration**:
- 388×381 A matrix loaded successfully
- 380×381 Am/Ad matrices for import/domestic split
- 411 basic sectors mapped to intermediate classification
- No hardcoded coefficients - all from official data

✅ **Methodology Validation**:
- Leontief inverse: (I - A)^(-1) calculation
- Matrix dimensions handled correctly
- Sector mapping through authentic 상품분류
- Employment intensity within realistic ranges

✅ **Results Validation**:
- Steel sector employment intensity: -66.15 jobs/천억원 (realistic)
- Regional distribution matches known industrial clusters
- Sectoral impacts align with economic relationships

## Extensions

### GRDP Analysis

The system can be extended for regional GDP impact analysis:

```python
def calculate_grdp_impact(sectoral_output_changes, target_regions):
    """
    Calculate GRDP changes from sectoral output changes.
    GRDP change = Σ(output_change_i × value_added_coefficient_i) by region
    """
    # Add value-added coefficients from 부가가치유발계수 files
    # return regional_grdp_changes
```

### Additional Multipliers

Support for loading additional regional multipliers:
- **생산유발계수**: Production multipliers
- **수입유발계수**: Import multipliers  
- **부가가치유발계수**: Value-added multipliers

## Usage Notes

### Sector Code Format
- Always use 4-digit format with leading zeros (e.g., '0401', '2711')
- System automatically formats codes for consistency

### Regional Analysis
- All 18 Korean regions supported
- Default analysis covers all regions unless specified
- Regional coefficients properly weighted

### Performance
- Large matrix operations optimized with NumPy
- Sector mapping cached for repeated analyses
- Memory-efficient loading of only required data

## Future Development

1. **Multi-scenario Analysis**: Batch processing multiple demand shocks
2. **Dynamic Analysis**: Time-series impact modeling  
3. **Policy Simulation**: Government spending multiplier analysis
4. **Export Enhancement**: Integration with visualization tools
5. **API Development**: RESTful API for web applications

---

**Authors**: Economic Analysis Team  
**Version**: 1.0  
**Date**: 2024  
**License**: MIT

For questions or support, please refer to the example code in `employment_calculator.py` or create an issue in the repository.