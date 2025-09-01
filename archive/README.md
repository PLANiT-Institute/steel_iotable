# 🏭 Steel-Coal I-O Analysis System

A comprehensive Korean Input-Output table analysis system focusing on steel-coal supply chain impacts with both command-line interface and modern web GUI.

## 🚀 Quick Start

### Option 1: Web GUI (Recommended)
```bash
# Install GUI dependencies
pip install -r requirements_gui.txt

# Launch the web interface
python run_gui.py
```
Then open your browser to `http://localhost:8501`

### Option 2: Demo Version (No Data Files Needed)
```bash
pip install streamlit plotly pandas numpy
streamlit run libs/gui/demo_gui.py
```

### Option 3: Command Line Interface
```bash
python enhanced_sector_analyzer.py
```

## 📊 Features

### Web GUI Interface
- **Interactive Analysis**: Point-and-click interface with real-time visualizations
- **Multiple Analysis Types**: Direct effects, Leontief multipliers, or full supply chain impacts
- **Rich Visualizations**: Interactive charts using Plotly (bar charts, treemaps, employment impacts)
- **Professional Reports**: Download results as Excel, CSV, or summary reports
- **Responsive Design**: Works on desktop, tablet, and mobile devices

### Analysis Capabilities
- **Supply Chain Impact Analysis**: Backward linkages and multiplier effects
- **Employment Impact Assessment**: Regional job effects across sectors
- **Import vs Domestic Analysis**: Separate analysis of import and domestic supply chains
- **Environmental Impact**: CO₂ emissions and environmental assessments
- **Steel-Coal Specific Analysis**: Specialized analysis for steel-coal supply chains

### Analysis Types
1. **Direct Effects Only**: Immediate supplier relationships
2. **Leontief/Indirect Effects Only**: Economic multiplier effects
3. **Full Effects**: Combined direct and indirect impacts

## 🗂️ Project Structure

```
steel_iotable/
├── run_gui.py                    # 🚀 GUI launcher script (main entry point)
├── enhanced_sector_analyzer.py  # 💻 CLI application
├── config/                       # ⚙️ Configuration files
│   ├── __init__.py
│   ├── analysis_config.py        # Main configuration classes
│   └── config_loader.py          # Configuration loading utilities
├── libs/                         # 📚 Core analysis modules
│   ├── io_data_loader.py         # I-O data loading and processing
│   ├── supply_chain_analyzer.py  # Supply chain impact analysis
│   ├── employment_analyzer.py    # Employment impact calculations
│   ├── import_domestic_analyzer.py # Import/domestic analysis
│   ├── comprehensive_analyzer.py # Environmental and fiscal analysis
│   ├── table_formatter.py       # Results formatting and export
│   └── gui/                      # 🖥️ GUI components
│       ├── __init__.py
│       ├── streamlit_app.py      # Main web GUI application
│       └── demo_gui.py           # Demo version with mock data
├── doc/                          # 📖 Documentation
│   └── README_GUI.md             # GUI-specific documentation
├── iotable/                      # 💾 I-O data files (user provided)
├── requirements.txt              # Core dependencies
├── requirements_gui.txt          # GUI dependencies
└── archive/                      # 📦 Older versions and experimental files
```

## 📋 Requirements

### For CLI Version
- Python 3.8+
- pandas, numpy, openpyxl
- Korean I-O data files (see Data Requirements below)

### For GUI Version
```bash
pip install -r requirements_gui.txt
```

### Data Requirements
Place the following files in the `iotable/` directory:
- `(표)(2020실측)투입산출표_기초가격_기본부문.xlsx` - Main I-O table
- `2020지역_부속표_고용표_통합중분류.xlsx` - Employment coefficients

## 🎯 Usage Examples

### Web GUI
1. Launch with `python run_gui.py`
2. Select analysis mode (Single Sector or Steel-Coal Supply Chain)
3. Choose sector and parameters through the interface
4. View interactive results and download reports

### Command Line
```python
from enhanced_sector_analyzer import EnhancedSectorAnalyzer

# Initialize analyzer
analyzer = EnhancedSectorAnalyzer()

# Run comprehensive analysis
results = analyzer.comprehensive_sector_analysis(
    target_sector="2411",      # Steel sector
    demand_change=-1000,       # 1000 billion won reduction
    supply_chain_type="full"   # Full supply chain effects
)

# Display results
analyzer.display_comprehensive_results(results)
```

## 📊 Analysis Methods

### Supply Chain Analysis
- **Input-Output Methodology**: Uses Leontief inverse matrix (I-A)⁻¹
- **Backward Linkages**: Identifies supplier dependencies
- **Multiplier Effects**: Calculates economy-wide ripple effects

### Analysis Equations
- **Direct Effects**: A × Δf (where A = input coefficients, Δf = final demand change)
- **Total Effects**: (I-A)⁻¹ × Δf (Leontief multiplier)
- **Indirect Effects**: Total Effects - Direct Effects

### Employment Analysis
- **Regional Employment Coefficients**: Jobs per billion won of output
- **Sectoral Employment Mapping**: Maps basic sectors to employment sectors

## 🎨 Visualization Features (GUI)

- **Supply Chain Impact Charts**: Bar charts showing top affected sectors
- **Effect Decomposition**: Pie charts breaking down direct vs indirect effects
- **Employment Impact Visualization**: Color-coded job gain/loss charts
- **Treemap Views**: Hierarchical impact representation
- **Interactive Elements**: Hover details, zoom, export capabilities

## 📥 Export Capabilities

- **Excel Reports**: Multi-sheet workbooks with detailed I-O tables
- **CSV Data**: Raw data for external analysis
- **Summary Reports**: Executive summaries in text format
- **Chart Exports**: PNG/SVG visualization downloads

## 🔧 Configuration

Main configuration in `config/analysis_config.py`:
- File paths for I-O data
- Analysis thresholds and parameters
- Display options and limits
- Sector keywords for steel/coal identification

Load configuration:
```python
from config import DEFAULT_CONFIG, AnalysisConfig
```

## 🚀 Deployment

### Local Development
```bash
streamlit run streamlit_app.py
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements_gui.txt
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py"]
```

### Cloud Deployment
- Compatible with Streamlit Cloud, Heroku, AWS, etc.
- See `README_GUI.md` for detailed deployment instructions

## 📖 Documentation

- **`doc/README_GUI.md`**: Detailed GUI documentation and features
- **Code Documentation**: Inline docstrings and comments
- **Configuration Guide**: See `config/analysis_config.py` for customization options

## 🔍 Analysis Workflow

1. **Data Loading**: Korean I-O tables at basic prices (기초가격)
2. **Sector Selection**: Choose target sector for analysis
3. **Impact Calculation**: Apply Leontief inverse methodology
4. **Multi-dimensional Analysis**: Economic, employment, environmental impacts
5. **Results Visualization**: Interactive charts and professional reports
6. **Export and Sharing**: Multiple format downloads

## ⚡ Performance

- **Caching**: Streamlit caching for improved performance
- **Optimized Calculations**: Efficient matrix operations using numpy
- **Scalable**: Handles large I-O matrices (400+ sectors)
- **Memory Management**: Smart data loading and processing

## 🐛 Troubleshooting

### Common Issues
- **Data files not found**: Ensure I-O files are in `iotable/` directory
- **GUI won't start**: Install requirements with `pip install -r requirements_gui.txt`
- **Analysis errors**: Try demo version first to verify setup

### Demo Version
Use `demo_gui.py` to test the interface without real data files.

## 📄 License

See LICENSE file for details.

---

**Built for economic impact analysis of Korean steel-coal supply chains using Input-Output methodology with modern web interface and comprehensive visualization capabilities.**