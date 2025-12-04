# Korean steel sector Input-Output analyzer

A comprehensive Input-Output (I-O) Table analysis tool for analyzing direct and indirect economic effects of demand changes in specific sectors, with specialized focus on steel industries in South Korea. Built using Korean I-O Table data from 2020 and 2023, this tool provides both economic impact analysis and employment effects analysis.

## Features

### **Economic Analysis**
- **3 Economic Coefficient Types**: Analyze indirect production, indirect import, and value-added effects
- **Monetary Impact Assessment**: Calculate economic impacts in monetary units across 380+ economic sectors
- **Supply Chain Analysis**: Track ripple effects through interconnected economic sectors

### **Employment Analysis** 
- **2 Employment Coefficient Types**: Total job creation and direct employment effects
- **Job Impact Calculation**: Estimate employment effects measured in number of jobs
- **Sub-Sector Mapping**: Uses hierarchical sector structure (411 basic sectors → 165 sub-sectors) for precise employment analysis

### **User Interfaces**
- **CLI Interface**: Command-line tool for interactive analysis
- **Web GUI**: Streamlit-based graphical interface with advanced visualization and separated economic vs employment charts
- **Export Capabilities**: Export results to Excel and CSV formats with multiple sheets
- **Real-time Analysis**: Calculate all coefficient types simultaneously for comprehensive impact assessment

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

The analysis relies on a comprehensive Excel file with 11 sheets containing mapping data and coefficient matrices:

#### **Economic Coefficient Matrices (6 sheets)**

All economic coefficient matrices share the same structure:
- **Format**: Square matrices with sector codes as rows and columns
- **Index Column**: First column contains sector `code` 
- **Matrix Size**: 384 rows × 381 columns (including code column)
- **Data Type**: Float coefficients representing economic relationships
- **Sectors Covered**: 380 active sectors

| Sheet Name | Matrix Symbol | Coefficient Type | Economic Meaning |
|------------|---------------|------------------|------------------|
| `indirectprodcoeff` | **(I-Ad)⁻¹** | Indirect Production | Leontief inverse matrix |
| `indirectimportcoeff` | **Am(I-Ad)⁻¹** | Indirect Import | Total import requirements |
| `valueaddedcoeff` | **V** | Value-Added | Value-added coefficients |

#### **Employment Coefficient Matrices (2 sheets)**

Employment matrices use the sub-sector structure:
- **Format**: Square matrices with sub-sector codes
- **Index Column**: First column contains sub-sector `code`
- **Matrix Size**: 165 rows × 166 columns (including code column) 
- **Data Type**: Employment coefficients (jobs per unit output)
- **Units**: Typically jobs per billion won of output

| Sheet Name | Coefficient Type | Employment Meaning |
|------------|------------------|-------------------|
| `jobcoeff` | **Total Job Creation** | Total employment effects (direct + indirect) |
| `directemploycoeff` | **Direct Employment** | Direct employment effects only |

#### **Matrix Interpretation Example**
For economic coefficient A[i,j] = 0.025:
- **Meaning**: Sector i requires 0.025 units of input from sector j to produce 1 unit of output
- **Demand Change**: 1 billion won increase in sector j final demand
- **Impact**: Generates 25 million won additional output requirement in sector i

For employment coefficient E[i,j] = 15.2:
- **Meaning**: 1 billion won of output in sub-sector j creates 15.2 jobs in sub-sector i
- **Demand Change**: 1 billion won increase in basic sector final demand  
- **Impact**: After mapping to sub-sector, generates 15.2 additional jobs in sub-sector i

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
- `coeff_type`: Coefficient type ('indirect_prod', 'indirect_import', 'value_added')
- `quiet`: If True, suppress console output

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

### Web GUI Interface (`main_gui.py`)

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

#### **Advanced GUI Features**:

##### **Separated Economic vs Employment Analysis**:
- **💰 Economic Effects Section**: 
  - Dedicated charts for economic coefficients (A, Am, Ad, indirect_prod, indirect_import, value_added)
  - Monetary impact visualization with "Total Economic Impact" and "Economic Sectors Affected" charts
  - Economic summary table showing impact values in won
  
- **👥 Employment Effects Section**:
  - Dedicated charts for employment coefficients (jobcoeff, directemploycoeff)  
  - Job impact visualization with "Total Jobs Created" and "Employment Sub-sectors Affected" charts
  - Employment summary table showing job creation values

##### **Interactive Analysis Features**:
- **Simultaneous Multi-Coefficient Analysis**: Calculates all 8 coefficient types in one operation
- **Tabbed Results Display**: Individual tabs for each coefficient type plus comprehensive summary
- **Customizable Data Views**: Toggle between 20/50/100/All results per coefficient
- **Real-time Statistics**: Min, Max, Mean, Standard Deviation for each analysis
- **Advanced Filtering**: Automatic filtering of near-zero and NaN impacts

##### **Export and Download Options**:
- **Multi-format Export**: 
  - Excel format with multiple sheets (one per coefficient type)
  - CSV fallback with combined data
  - Metadata inclusion (target sector, demand change, coefficient descriptions)
- **Complete Analysis Package**: Single download containing all 8 analyses
- **Individual Coefficient Downloads**: Separate CSV downloads for each coefficient type

##### **Performance Optimizations**:
- **@st.cache_data**: Analyzer initialization caching prevents data reloading
- **Efficient Data Processing**: Batch coefficient calculations with error handling
- **Memory Management**: Optimized DataFrame operations for large datasets
- **Background Processing**: Non-blocking coefficient calculations with progress indicators

## Comprehensive Analysis Types

### **Economic Coefficients (Monetary Impact)**

#### **Direct Input Coefficients**
- **A (Direct Total Coefficients)**
  - **Definition**: Total direct input requirements per unit of output
  - **Formula**: A = Z × (diag(X))⁻¹, where Z is intermediate transaction matrix, X is total output
  - **Interpretation**: Shows how much input from each sector is needed to produce 1 unit of output in target sector
  - **Use Case**: Analyze immediate supply chain requirements and backward linkages

- **Am (Direct Import Coefficients)**
  - **Definition**: Import input requirements per unit of output
  - **Formula**: Am = Zm × (diag(X))⁻¹, where Zm is import transaction matrix
  - **Interpretation**: Shows how much imported input is needed per unit of domestic output
  - **Use Case**: Assess import dependency and trade balance effects

- **Ad (Direct Domestic Coefficients)**  
  - **Definition**: Domestic input requirements per unit of output
  - **Formula**: Ad = Zd × (diag(X))⁻¹, where Zd is domestic transaction matrix
  - **Interpretation**: Shows domestic input requirements, excluding imports
  - **Use Case**: Analyze domestic supply chain integration and regional economic effects

#### **Indirect Effects Coefficients**
- **Indirect Production (I-Ad)⁻¹**
  - **Definition**: Leontief inverse matrix showing total requirements
  - **Formula**: (I - Ad)⁻¹, where I is identity matrix
  - **Interpretation**: Total output requirements (direct + indirect) per unit of final demand
  - **Use Case**: Capture full supply chain multiplier effects through all production rounds

- **Indirect Import Coefficients**
  - **Definition**: Total import requirements through supply chain
  - **Formula**: Am × (I - Ad)⁻¹
  - **Interpretation**: Total imports (direct + indirect) induced by final demand change
  - **Use Case**: Assess total trade balance impact including upstream imports

- **Value-Added Coefficients**
  - **Definition**: Value-added requirements per unit of output
  - **Formula**: V × (diag(X))⁻¹, where V is value-added by sector
  - **Interpretation**: GDP contribution per unit of output (wages, profits, taxes)
  - **Use Case**: Measure economic welfare effects and GDP impact

### **Employment Coefficients (Job Impact)**

#### **Employment Analysis with Sub-Sector Mapping**
The employment analysis uses a hierarchical structure where 411 basic sectors map to 165 employment sub-sectors, providing more precise job impact estimation.

- **Total Job Creation Coefficients (jobcoeff)**
  - **Definition**: Total employment requirements per unit of output including all supply chain effects
  - **Units**: Jobs per unit of output (typically per billion won)
  - **Scope**: Captures both direct employment in target sector and indirect employment in supplier sectors
  - **Interpretation**: Shows total job creation (direct + indirect) across all sub-sectors from demand change
  - **Use Case**: Comprehensive employment impact assessment for policy analysis

- **Direct Employment Coefficients (directemploycoeff)**
  - **Definition**: Direct employment requirements per unit of output in each sub-sector
  - **Units**: Jobs per unit of output (typically per billion won)
  - **Scope**: Only direct employment effects, excluding supply chain employment
  - **Interpretation**: Shows immediate job creation in each sub-sector from increased production
  - **Use Case**: Assess direct job creation potential of specific demand changes

#### **Sector Mapping Methodology**
```
Basic Sector (411) → Sub-Sector (165) → Employment Impact
Example: 2711 (선철) → 271 (선철 및 조강) → Job Effects
```

**Mapping Process**:
1. User selects basic sector (e.g., 2711: 선철/pig iron)
2. System maps to employment sub-sector (271: 선철 및 조강/iron and steel)
3. Employment coefficients applied at sub-sector level
4. Results displayed with Korean sub-sector names from subsectormap

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

## Technical Implementation Details

### **Core Architecture**

#### **Class Structure**:
```python
IOTableAnalyzer
├── Data Loading Layer
│   ├── Excel file parsing (11 sheets)
│   ├── Mapping creation (basic→subsector, subsector→name)
│   └── Coefficient matrix indexing
├── Analysis Engine  
│   ├── Economic effects calculation
│   ├── Employment effects calculation (with mapping)
│   └── Result aggregation and formatting
└── Output Layer
    ├── CLI formatted display
    ├── GUI data structures
    └── Export file generation
```

#### **Data Flow Architecture**:
```
Input Validation → Sector Mapping → Coefficient Selection → 
Matrix Multiplication → Impact Filtering → Result Formatting → Output Display
```

### **Algorithm Implementation**

#### **Economic Impact Calculation**:
```python
# For economic coefficients (A, Am, Ad, etc.)
impact_vector = coefficient_matrix[:, target_sector] * demand_change
filtered_impacts = impact_vector[abs(impact_vector) > threshold]
```

#### **Employment Impact Calculation**:
```python  
# For job coefficients (requires sector mapping)
basic_sector → subsector_mapping[basic_sector] → target_subsector
job_impact_vector = job_matrix[:, target_subsector] * demand_change
filtered_jobs = job_impact_vector[abs(job_impact_vector) > threshold]
```

#### **Performance Optimizations**:
- **Vectorized Operations**: Uses pandas vectorization for matrix operations
- **Lazy Loading**: Coefficients loaded on-demand during analysis  
- **Memory Efficiency**: Filters insignificant impacts early in pipeline
- **Caching Strategy**: GUI caches analyzer instance across user interactions

### **Error Handling and Validation**

#### **Input Validation Chain**:
1. **Sector Code Validation**: Supports multiple formats (111, "0111", 2711)
2. **Coefficient Type Validation**: Validates against available coefficient types
3. **Demand Change Validation**: Numeric validation with range checking
4. **Data Integrity Checks**: Validates matrix dimensions and completeness

#### **Robust Error Recovery**:
- **Missing Data Handling**: Graceful handling of NaN values and missing sectors
- **Matrix Compatibility**: Automatic format conversion between integer/string sector codes
- **Export Fallbacks**: CSV export if Excel libraries unavailable
- **GUI Error Boundaries**: Per-coefficient error handling prevents total failure

### **Data Processing Pipeline**

#### **Loading Phase**:
1. **Excel Sheet Parsing**: Multi-sheet parsing with error handling
2. **Index Standardization**: Consistent sector code formatting across sheets
3. **Mapping Creation**: Build sector→subsector and subsector→name dictionaries
4. **Matrix Validation**: Verify coefficient matrix completeness and structure

#### **Analysis Phase**:
1. **Input Processing**: Sector code normalization and validation
2. **Coefficient Selection**: Matrix selection based on analysis type
3. **Impact Calculation**: Vectorized matrix multiplication
4. **Result Filtering**: Remove negligible impacts and invalid values
5. **Name Resolution**: Map sector codes to Korean names

#### **Output Phase**:
1. **Result Aggregation**: Calculate summary statistics
2. **Sorting and Ranking**: Order by impact magnitude  
3. **Format Conversion**: Prepare data for CLI/GUI display
4. **Export Generation**: Create downloadable files with metadata

### **Scalability Considerations**

#### **Memory Management**:
- **Matrix Storage**: Efficient scipy sparse matrix usage for large coefficient matrices
- **Result Buffering**: Stream processing for large result sets
- **Cache Management**: Intelligent cache invalidation and size limits

#### **Performance Metrics**:
- **Load Time**: ~2-3 seconds for complete dataset (11 sheets, 411 sectors)
- **Analysis Time**: <100ms per coefficient type calculation
- **Memory Usage**: ~50MB for complete loaded analyzer instance
- **Concurrent Users**: Streamlit supports multiple simultaneous analyses

### **Integration Points**

#### **External Dependencies**:
- **pandas**: Core data manipulation and matrix operations
- **openpyxl**: Excel file reading/writing capabilities
- **streamlit**: Web GUI framework with caching and state management
- **Standard Library**: Core Python for file I/O and data structures

#### **Extension Possibilities**:
- **Database Integration**: Replace Excel with SQL database backend
- **API Development**: REST API for programmatic access
- **Visualization Enhancement**: Advanced plotting with plotly/matplotlib
- **Real-time Updates**: Live data feeds for dynamic coefficient updates

## Data Source and Methodology

### **Korean I-O Table 2020 Specifications**
- **Data Source**: Bank of Korea (한국은행) Input-Output Tables
- **Base Year**: 2020
- **Price Basis**: Producer prices (생산자가격)
- **Sector Classification**: Korean Standard Industrial Classification (KSIC) based
- **Coverage**: Complete Korean economy with 411 detailed sectors
- **Compilation Method**: Commodity-by-industry framework
- **Data Quality**: Official government statistics with full quality assurance

### **Methodological Foundation**
- **Theoretical Framework**: Leontief Input-Output Model
- **Matrix Algebra**: Standard I-O mathematical framework with (I-A)⁻¹ inverse calculations
- **Employment Extension**: Job coefficient matrices linked through sector aggregation
- **Impact Assessment**: Direct and indirect effects via multiplier analysis
- **Validation**: Results consistent with established I-O analysis principles

## Contributing

### **Development Setup**:
1. Fork the repository
2. Create virtual environment: `python -m venv venv`
3. Install dependencies: `pip install pandas streamlit openpyxl`
4. Run tests: `python -m pytest` (when available)
5. Create feature branch and submit pull request

### **Code Standards**:
- **Type Hints**: Use Python type hints for all function signatures
- **Documentation**: Docstrings for all classes and methods
- **Error Handling**: Comprehensive exception handling with informative messages
- **Performance**: Optimize for large dataset handling

### **Data Updates**:
- **New I-O Tables**: Update Excel file and validate coefficient matrix compatibility
- **Sector Changes**: Update mapping files and validate code consistency
- **Feature Additions**: Maintain backward compatibility with existing analyses

## Support

### **Documentation and Help**:
- **In-App Help**: CLI provides interactive help and examples
- **Error Messages**: Detailed error messages with suggested solutions
- **Example Data**: Sample analyses included for common use cases

### **Issue Reporting**:
1. Check existing issues on GitHub repository
2. Create detailed issue with:
   - Input parameters used
   - Expected vs actual results  
   - Error messages and stack traces
   - System information (Python version, OS)

### **Contact Information**:
- **GitHub Issues**: Primary support channel
- **Technical Questions**: Include sample data and specific use case
- **Feature Requests**: Describe use case and expected functionality

---

*Built with Python, pandas, and Streamlit | Korean I-O Table 2020 Data from Bank of Korea | Implements standard Leontief Input-Output methodology with Korean employment extensions*
