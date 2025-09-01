# Enhanced Sector Impact Analyzer

Comprehensive economic impact analysis tool for Korean Input-Output tables with **IO table format output** and **simple YAML configuration**.

## 🎯 Key Features

### 1. **Complete Supply Chain Analysis**
- **Import vs Domestic separation** using Am (import) and Ad (domestic) coefficient matrices
- **Supply chain impact analysis** with backward and forward linkages
- **Employment impact calculation** using employment coefficients
- **Environmental impact estimates** (CO2 emissions)
- **Fiscal impact analysis** (tax revenue effects)

### 2. **IO Table Format Output**
- **Traditional matrix display** with sectors as rows, impacts as columns
- **Multiple impact tables**: Supply Chain, Import/Domestic, Employment, Comprehensive
- **Excel export** with multiple sheets for professional reports
- **Customizable display limits** and formatting

### 3. **Simple YAML Configuration**
- **Single config.yaml file** for all settings
- **Easy customization** without code changes
- **Dot notation access**: `get_config('files.basic_io_file')`
- **Built-in defaults** with graceful fallback

## 📊 What It Analyzes

### **Steel-Coal Supply Chain Example:**
When steel sector reduces coal consumption by 1000 billion won:

```
================================================================================
AGGREGATE STEEL-COAL SUPPLY CHAIN IMPACTS
================================================================================
Impact_Type                     Value      Unit
Total Supply Chain Impact    5,658.5      billion won
Total Employment Change      4,414        jobs  
Total Import Impact         1,837.7       billion won
Total Domestic Impact       9,029.6       billion won
Total CO2 Impact            2,018.5       thousand tons
Total Tax Impact           -213.2         billion won
================================================================================
```

### **Import vs Domestic Matrix:**
```
================================================================================
IMPORT VS DOMESTIC COMPARISON
================================================================================
                    Import_Impact  Domestic_Impact  Import_Share  Domestic_Share
Sector_Code                                                                      
2727                       -167.3          -823.2        16.9%           83.1%
7110                        -45.2          -173.6        20.7%           79.3%
5200                         28.4           104.0        21.5%           78.5%
================================================================================
```

## 🚀 Quick Start

### **Interactive Mode:**
```bash
# With simple YAML config
python enhanced_sector_analyzer_simple.py

# Menu options:
# 1. Comprehensive sector analysis
# 2. Steel-coal supply chain (comprehensive)  
# 3. Import vs Domestic impact comparison
# 4. Environmental impact analysis
# 5. Comprehensive analysis with IO tables
# 6. Steel-coal analysis with IO tables
# 7. Search sectors
# 8. Exit
```

### **Programmatic Usage:**
```python
from enhanced_sector_analyzer_simple import EnhancedSectorAnalyzer
from simple_config import get_config

# Initialize with YAML config
analyzer = EnhancedSectorAnalyzer()

# Comprehensive analysis
results = analyzer.comprehensive_sector_analysis('2727', -1000)

# Display as IO tables with Excel export
analyzer.display_results_as_tables(results, export_excel=True)

# Steel-coal specific analysis
steel_results = analyzer.analyze_steel_coal_comprehensive(1000)
analyzer.display_steel_coal_tables(steel_results, export_excel=True)
```

## ⚙️ Configuration

### **config.yaml Structure:**
```yaml
# File paths
files:
  basic_io_file: "iotable/(표)(2020실측)투입산출표_기초가격_기본부문.xlsx"
  employment_file: "iotable/2020지역_부속표_고용표_통합중분류.xlsx"

# Default values  
defaults:
  reduction_amount: 1000  # billion won
  target_region: "전지역"

# Analysis options
analysis:
  supply_chain: true
  employment: true
  import_domestic: true
  comprehensive: true

# Display limits
display:
  table_rows: 15
  matrix_rows: 15
  max_sectors_display: 2

# Thresholds
thresholds:
  employment_impact: 0.1
  economic_magnitude: 1.5
  employment_significance: 100

# Search keywords
sectors:
  steel_keywords: ["철강", "제철", "선철"]
  coal_keywords: ["석탄", "코크스"]
```

### **Easy Customization:**
```python
# Get config values
reduction_amount = get_config('defaults.reduction_amount', 1000)
steel_keywords = get_config('sectors.steel_keywords', ['철강'])
table_rows = get_config('display.table_rows', 15)

# Modify thresholds
# Edit config.yaml:
# thresholds:
#   employment_impact: 0.5      # Higher threshold
#   economic_magnitude: 2.0     # Stricter high impact criteria
```

## 📁 File Structure

```
steel_iotable/
├── config.yaml                           # Simple YAML configuration
├── simple_config.py                      # Config loader
├── enhanced_sector_analyzer_simple.py    # Main analyzer with YAML config
├── libs/
│   ├── io_data_loader.py                 # IO table data loader
│   ├── supply_chain_analyzer.py          # Supply chain analysis
│   ├── employment_analyzer.py            # Employment impact analysis
│   ├── import_domestic_analyzer.py       # Import/domestic separation
│   ├── comprehensive_analyzer.py         # Value-added, environmental, fiscal
│   └── table_formatter.py                # IO table format output
├── demos/
│   ├── yaml_demo.py                      # YAML config demonstration
│   ├── table_demo.py                     # IO table output demo
│   └── enhanced_demo.py                  # Full capabilities demo
└── iotable/                              # Korean IO data files
    ├── (표)(2020실측)투입산출표_기초가격_기본부문.xlsx
    └── 2020지역_부속표_고용표_통합중분류.xlsx
```

## 💡 Use Cases

### **1. Policy Analysis**
```python
# Analyze impact of carbon tax on steel industry
results = analyzer.comprehensive_sector_analysis('2711', -500)
analyzer.display_results_as_tables(results, export_excel=True)
```

### **2. Supply Chain Risk Assessment**  
```python
# What happens when coal supply is disrupted?
steel_coal = analyzer.analyze_steel_coal_comprehensive(1000)
print(f"Total employment at risk: {steel_coal['aggregate_impacts']['total_employment_change']:,} jobs")
```

### **3. Trade Impact Analysis**
```python
# Import vs domestic effects of sector changes
import_results = analyzer.import_domestic_analyzer.analyze_import_domestic_impacts('2727', -1000)
print(f"Import dependency: {import_results['import_share']:.1%}")
```

### **4. Environmental Assessment**
```python
# CO2 reduction from industrial transition
results = analyzer.comprehensive_sector_analysis('1610', -2000)  # Coal sector reduction
env_impact = results['comprehensive_analysis']['environmental_analysis']
print(f"CO2 reduction: {env_impact['environmental_summary']['total_co2_thousand_tons']:,.0f} thousand tons")
```

## 📈 Output Formats

### **1. Console Display**
- Formatted tables with aligned columns
- Ranked impacts by magnitude
- Summary statistics and assessments

### **2. Excel Export**
- Multiple sheets for different impact types
- Professional formatting
- Metadata sheet with analysis parameters
- Ready for reports and presentations

### **3. IO Table Format**
- Traditional input-output matrix structure
- Sectors as rows, impact types as columns
- Familiar format for IO analysis practitioners

## 🔬 Analysis Capabilities

### **Economic Impacts:**
- Direct, indirect, and total supply chain effects
- Production multipliers and value-added impacts
- GDP and economic output changes

### **Employment Effects:**
- Job creation/loss by sector
- Employment intensity calculations
- Regional employment analysis

### **Trade Analysis:**
- Import vs domestic production impacts
- Import dependency ratios
- Trade balance implications

### **Environmental Assessment:**
- CO2 emission estimates by sector
- Carbon intensity calculations
- Environmental cost-benefit analysis

### **Fiscal Implications:**
- Tax revenue impacts
- Income, corporate, and indirect tax effects
- Fiscal cost of economic transitions

## 🎓 Academic & Research Applications

- **Input-Output modeling** with Korean national accounts data
- **Supply chain analysis** for industrial policy
- **Environmental economics** and carbon footprint analysis
- **Regional economic analysis** and development planning
- **Trade policy analysis** and import substitution studies

---

**Built for:** Economic researchers, policy analysts, industrial planners, and academic institutions working with Korean Input-Output data.

**Data Source:** 2020 Korean Input-Output Tables at basic prices (기초가격) from Bank of Korea.