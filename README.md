# Steel-Coal I-O Table Direct Effects Analyzer

A comprehensive Input-Output (I-O) Table analysis tool for analyzing direct and indirect economic effects of demand changes in specific sectors, with a focus on steel and coal industries. Built using Korean I-O Table data from 2020.

## Features

- **Multiple Coefficient Types**: Analyze 6 different types of economic coefficients
- **CLI Interface**: Command-line tool for interactive analysis
- **Web GUI**: Streamlit-based graphical interface with advanced visualization
- **Export Capabilities**: Export results to Excel and CSV formats
- **Comprehensive Analysis**: Calculate direct and indirect effects across all economic sectors

## Installation

### Requirements

```bash
pip install pandas streamlit openpyxl
```

### Python Version
- Python 3.7 or higher

## Quick Start

### Command Line Interface
```bash
python main.py
```

### Web GUI Interface
```bash
streamlit run main_gui.py
```

## Data Structure

### Excel File Format (`data/iotable_2020.xlsx`)

The analysis relies on a structured Excel file containing multiple sheets:

#### 1. **basicmap** - Sector Mapping
- **Columns**: `code`, `product`
- **Size**: 411 sectors
- **Purpose**: Maps sector codes to product names
- **Example**:
  ```
  code | product
  111  | 벼 (Rice)
  112  | 맥류 및 잡곡 (Barley and misc grains)
  2711 | 철강 (Steel)
  ```

#### 2. **subsectormap** - Detailed Sector Mapping
- Extended mapping with subsector classifications

#### 3. **codemap** - Code Reference
- Additional code reference information

#### 4. **Coefficient Matrices** (6 types)

All coefficient matrices follow the same structure:
- **Format**: Square matrices with sector codes as both rows and columns
- **Index**: First column contains sector `code`
- **Size**: 384 rows × 381 columns (including code column)
- **Values**: Economic coefficients representing inter-sectoral relationships

**Available Coefficient Types**:

| Sheet Name | Coefficient Type | Description |
|------------|------------------|-------------|
| `directinputcoeff_A` | **A** - Direct Total | Total direct input coefficients |
| `importinputcoeff_Am` | **Am** - Direct Import | Import input coefficients |
| `domesticinputcoeff_Ad` | **Ad** - Direct Domestic | Domestic input coefficients |
| `indirectprodcoeff` | **indirect_prod** | Indirect Production (I-Ad)⁻¹ |
| `indirectimportcoeff` | **indirect_import** | Indirect Import coefficients |
| `valueaddedcoeff` | **value_added** | Value-Added coefficients |

## Core Classes and Methods

### IOTableAnalyzer Class

Located in `libs/io_analyzer.py`, this is the main analysis engine.

#### Initialization
```python
from libs.io_analyzer import IOTableAnalyzer

analyzer = IOTableAnalyzer(data_file='data/iotable_2020.xlsx')
```

#### Key Methods

##### `load_data()`
- **Purpose**: Load all coefficient matrices and mapping data from Excel
- **Process**: 
  1. Loads sector mapping from `basicmap` sheet
  2. Loads 6 coefficient matrices
  3. Creates code-to-product mapping dictionaries
  4. Handles proper code formatting (3-digit codes get leading zeros)

##### `get_sector_options() -> Dict`
- **Returns**: Dictionary of formatted sector codes to display strings
- **Format**: `{"0111": "0111: 벼", "2711": "2711: 철강", ...}`
- **Usage**: Populate UI selection lists

##### `get_sector_from_display(display_string: str)`
- **Purpose**: Extract sector code from display string
- **Input**: Display string like "0111: 벼"  
- **Returns**: Properly formatted sector code ("0111" or integer)
- **Logic**: Maintains string format for codes starting with "0"

##### `calculate_direct_effects(target_sector, demand_change, coeff_type, quiet=False) -> Dict`

**Core analysis method** that calculates economic impacts.

**Parameters**:
- `target_sector`: Sector code (string like "0111" or integer like 2711)
- `demand_change`: Final demand change amount (float, can be negative)
- `coeff_type`: Coefficient type ('A', 'Am', 'Ad', 'indirect_prod', 'indirect_import', 'value_added')
- `quiet`: If True, suppress console output

**Returns**: Dictionary with complete analysis results
```python
{
    'target_sector': '0111',
    'target_product': '벼',
    'demand_change': 1000000,
    'coeff_type': 'A',
    'coeff_name': 'Direct Total',
    'impacts': [
        {
            'sector_code': '0111',
            'sector_name': '벼',
            'impact': 850000.5
        },
        # ... more impacts
    ],
    'total_impact': 1250000.75,
    'num_affected_sectors': 137
}
```

**Calculation Logic**:
1. Select appropriate coefficient matrix
2. Extract column for target sector
3. Multiply coefficients by demand change: `impact = coefficient × demand_change`
4. Filter out near-zero impacts (< 1e-6) and NaN values
5. Sort results by absolute impact value
6. Add sector names using mapping data

##### `display_results(results: Dict)`
- **Purpose**: Format and display analysis results in console
- **Output**: Formatted table showing top 20 impacts with statistics

## User Interfaces

### 1. Command Line Interface (`main.py`)

Interactive menu system with options:

1. **List all sectors**: Display all 411 available sectors
2. **Analyze direct effects**: 
   - Select coefficient type
   - Enter sector code (supports 111, 0111, or 2711 formats)
   - Enter demand change amount
   - View formatted results
3. **Exit**: Quit application

**Usage Example**:
```
Select option (1-3): 2
Select coefficient type: A
Enter sector code: 2711
Enter demand change amount: 1000000
```

### 2. Web GUI Interface (`main_gui.py`)

Built with Streamlit, featuring:

#### Features:
- **Sector Selection**: Dropdown with all 411 sectors
- **Demand Input**: Numeric input with default 1,000,000
- **Comprehensive Analysis**: Calculates all 6 coefficient types simultaneously
- **Tabbed Results**: Separate tab for each coefficient type plus summary
- **Interactive Tables**: Sortable results with customizable row limits (20/50/100/All)
- **Export Options**: 
  - Excel format with multiple sheets (requires openpyxl)
  - CSV format fallback
- **Statistics**: Min, Max, Mean, Standard Deviation for each analysis
- **Charts**: Bar charts comparing total impacts across coefficient types

#### GUI Structure:
```
Sidebar:
├── Sector Selection (Dropdown)
├── Demand Change (Number Input)  
└── Analyze Button

Main Area:
├── Summary Tab
│   ├── Overall comparison table
│   ├── Download complete analysis
│   └── Impact comparison charts
└── Individual Coefficient Tabs (6)
    ├── Metrics (Total Impact, Affected Sectors, Max Impact)
    ├── Results Table (with filtering)
    ├── Download button
    └── Statistics (Min, Max, Mean, Std Dev)
```

#### Caching:
- Uses `@st.cache_data` for analyzer initialization
- Prevents reloading data on each interaction

## Analysis Types Explained

### Direct Effects (A, Am, Ad)
- **A (Direct Total)**: Total direct input requirements per unit of output
- **Am (Direct Import)**: Import requirements per unit of output  
- **Ad (Direct Domestic)**: Domestic input requirements per unit of output

### Indirect Effects
- **Indirect Production**: Effects through the production chain (I-Ad)⁻¹
- **Indirect Import**: Import effects through supply chains
- **Value-Added**: Value-added effects (wages, profits, taxes)

## Sector Code Format

The system handles multiple sector code formats:

| Input Format | Internal Format | Example |
|--------------|-----------------|---------|
| 111 | "0111" | Agriculture |
| "0111" | "0111" | Agriculture |  
| 2711 | "2711" or 2711 | Steel |
| "2711" | "2711" or 2711 | Steel |

**Logic**: 
- 3-digit codes: Add leading zero → string format
- 4-digit codes: Maintain as integer or string based on data structure

## Error Handling

### Common Scenarios:
- **Invalid sector code**: Validates against available sectors
- **Invalid coefficient type**: Validates against available types
- **Missing dependencies**: Graceful fallback (Excel → CSV export)
- **Data quality**: Filters NaN values and near-zero impacts
- **Input validation**: Type checking and format conversion

### Error Messages:
- User-friendly error messages in both CLI and GUI
- Detailed exception information for debugging
- Graceful degradation (warnings instead of errors where appropriate)

## File Structure

```
steel_iotable/
├── main.py                 # CLI interface
├── main_gui.py            # Streamlit web GUI  
├── libs/
│   ├── __init__.py
│   └── io_analyzer.py     # Core analysis engine
├── data/
│   └── iotable_2020.xlsx  # I-O table data
├── archive/               # Legacy code and examples
└── README.md             # This file
```

## Data Source

- **Source**: Korean Input-Output Table 2020
- **Coverage**: 411 sectors across all economic activities
- **Language**: Korean sector names with numeric codes
- **Format**: Producer prices, basic classification

## License

MIT License - see LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues or questions:
1. Check existing issues on GitHub
2. Create a new issue with detailed description
3. Include sample data and error messages

---

*Built with Python, pandas, and Streamlit | Korean I-O Table 2020 Data*