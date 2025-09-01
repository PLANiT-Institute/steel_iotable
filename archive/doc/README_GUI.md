# 🏭 Steel-Coal I-O Analysis GUI Dashboard

A comprehensive web-based interface for Korean Input-Output table analysis focusing on steel-coal supply chain impacts with interactive visualizations and downloadable reports.

## 🚀 Quick Start

### Option 1: Full Application (with real I-O data)
```bash
# Install GUI dependencies
pip install -r requirements_gui.txt

# Launch the full application
python run_gui.py
```

### Option 2: Demo Version (with mock data)
```bash
# Install streamlit if needed
pip install streamlit plotly pandas numpy

# Run demo version
streamlit run demo_gui.py
```

The GUI will automatically open in your web browser at `http://localhost:8501`

## ✨ Features

### 🎯 Single Sector Analysis
- **Interactive Input Controls**: Select sector codes, demand changes, and analysis types
- **Multiple Analysis Types**: 
  - Direct effects only (immediate suppliers)
  - Indirect/Leontief effects only (multiplier effects)
  - Full effects (direct + indirect)
- **Real-time Results**: Live calculations with progress indicators
- **Rich Visualizations**: Interactive charts and graphs using Plotly

### ⛏️ Steel-Coal Supply Chain Analysis
- **Comprehensive Supply Chain Mapping**: Analyze impacts across steel and coal sectors
- **Aggregate Impact Metrics**: Total economic, employment, and environmental effects
- **Coal-Specific Analysis**: Focus on coal-related supply chain impacts
- **Flexible Parameters**: Adjust reduction amounts and sector limits

### 📊 Interactive Visualizations
- **Bar Charts**: Top impacted sectors with color coding
- **Pie Charts**: Breakdown of direct vs indirect effects
- **Employment Charts**: Job impact analysis with positive/negative indicators
- **Treemaps**: Hierarchical impact visualization
- **Responsive Design**: Charts adapt to screen size

### 📈 Key Metrics Dashboard
- **Economic Impacts**: Output impact, GDP effects, production multipliers
- **Employment Effects**: Total jobs affected across sectors and regions
- **Environmental Impact**: CO₂ emissions and car-equivalent calculations
- **Fiscal Impact**: Tax revenue effects

### 📥 Report Generation & Downloads
- **Excel Reports**: Detailed I-O tables with multiple sheets
- **CSV Data**: Raw data exports for further analysis
- **Summary Reports**: Text summaries of key findings
- **Real-time Export**: Generate reports on-demand

## 🎨 User Interface

### Layout
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Sidebar Controls**: Easy access to analysis parameters
- **Multi-column Layout**: Efficient use of screen space
- **Progress Indicators**: Real-time feedback during analysis

### Styling
- **Professional Theme**: Clean, modern interface
- **Color-coded Metrics**: Visual indicators for different impact types  
- **Custom CSS**: Enhanced styling beyond default Streamlit
- **Interactive Elements**: Hover effects and clickable charts

## 🔧 Technical Architecture

### Frontend (Streamlit)
- **Streamlit Framework**: Python-based web app framework
- **Plotly Visualizations**: Interactive charts and graphs
- **Pandas Integration**: Seamless data table displays
- **Custom CSS**: Enhanced styling and responsive design

### Backend Integration
- **Enhanced Sector Analyzer**: Full integration with existing analysis engine
- **Real-time Processing**: Live calculations without page refreshes
- **Error Handling**: Graceful error messages and recovery
- **Caching**: Optimized performance with data caching

### Data Flow
```
User Input → Streamlit Interface → Enhanced Analyzer → Results → Visualizations
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Required I-O data files (for full version):
  - `iotable/(표)(2020실측)투입산출표_기초가격_기본부문.xlsx`
  - `iotable/2020지역_부속표_고용표_통합중분류.xlsx`

### Step-by-Step Setup
1. **Clone/Download** the repository
2. **Install Dependencies**:
   ```bash
   pip install -r requirements_gui.txt
   ```
3. **Prepare Data** (for full version):
   - Ensure I-O data files are in the `iotable/` directory
   - Verify file paths in `config.py`
4. **Launch Application**:
   ```bash
   python run_gui.py
   ```

### Docker Setup (Optional)
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements_gui.txt

EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## 📋 Usage Examples

### Basic Sector Analysis
1. Select "Single Sector Analysis" from the sidebar
2. Enter sector code (e.g., "2411" for steel)
3. Set demand change (e.g., -1000 billion won)
4. Choose analysis type (direct/leontief/full)
5. Click "Run Analysis"
6. View results and download reports

### Steel-Coal Supply Chain
1. Select "Steel-Coal Supply Chain" mode
2. Set coal reduction amount
3. Choose maximum sectors to analyze
4. Select visualization type
5. Run analysis and explore results

### Exporting Results
- **Excel**: Detailed tables with multiple sheets
- **CSV**: Raw data for external analysis
- **Summary**: Text report with key findings

## 🎯 Comparison: GUI vs CLI

| Feature | GUI (Streamlit) | CLI (Text-based) |
|---------|-----------------|------------------|
| **Ease of Use** | ✅ Point-and-click interface | ❌ Command-line knowledge needed |
| **Visualizations** | ✅ Interactive charts & graphs | ❌ Text tables only |
| **Real-time Feedback** | ✅ Progress bars & live updates | ❌ Static output |
| **Export Options** | ✅ Multiple formats, one-click | ❌ Limited export options |
| **Accessibility** | ✅ Web browser, any device | ❌ Terminal access required |
| **Sharing** | ✅ Easy to share results | ❌ Difficult to share |
| **Professional Reports** | ✅ Publication-ready outputs | ❌ Raw text output |

## 🚀 Deployment Options

### Local Development
- Run on localhost for personal use
- Ideal for development and testing

### Streamlit Cloud
- Free hosting for public repositories
- Automatic deployment from GitHub
- Custom domain support

### Docker Container
- Containerized deployment
- Easy scaling and distribution
- Cloud platform deployment

### Enterprise Setup
- Internal server deployment
- Custom authentication
- Data security compliance

## 🔮 Future Enhancements

### Planned Features
- **Multi-language Support**: Korean/English interface
- **Advanced Filtering**: Complex sector selection criteria
- **Comparison Mode**: Side-by-side analysis of multiple scenarios
- **API Integration**: REST API for external systems
- **Advanced Reports**: PDF generation with custom templates

### Visualization Improvements
- **Network Graphs**: Supply chain relationship mapping
- **Geographic Maps**: Regional impact visualization
- **Time Series**: Historical trend analysis
- **3D Charts**: Multi-dimensional impact visualization

## 🐛 Troubleshooting

### Common Issues
1. **Streamlit not found**: Install with `pip install streamlit`
2. **Data files missing**: Ensure I-O files are in correct location
3. **Port already in use**: Try different port with `--server.port 8502`
4. **Memory issues**: Use demo version or limit sector analysis

### Performance Tips
- Use demo version for testing
- Limit number of sectors in analysis
- Clear browser cache if visualizations don't load
- Ensure adequate RAM for large datasets

## 📞 Support

For issues with the GUI application:
1. Check the troubleshooting section above
2. Verify all dependencies are installed
3. Try the demo version first
4. Check browser console for JavaScript errors

## 📄 License

Same license as the main application. See the main README for details.