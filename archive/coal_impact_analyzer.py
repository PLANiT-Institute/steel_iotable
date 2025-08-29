import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from employment_calculator import EmploymentCalculator

class CoalImpactAnalyzer:
    def __init__(self):
        """
        Initialize the Coal Impact Analyzer for estimating economic impacts 
        and employment changes from coal consumption reduction using national-level 
        basic sector data (기본부문) at basic prices (기초가격).
        """
        self.employment_file = 'iotable/2020지역_부속표_고용표_통합중분류.xlsx'
        self.basic_io_file = 'iotable/(표)(2020실측)투입산출표_기초가격_기본부문.xlsx'
        
        # Initialize employment calculator
        self.calculator = EmploymentCalculator(
            self.employment_file,
            self.basic_io_file
        )
        
        # Load basic IO table data
        self.io_table = None
        self.sector_names = []
        self.sector_codes = []
        self._load_basic_io_table()
        
        # GUI components
        self.root = None
        self.sector_var = None
        self.amount_var = None
        self.results_text = None
        self.fig = None
        self.canvas = None
    
    def _load_basic_io_table(self):
        """Load the basic sector input-output table at basic prices."""
        try:
            # Load the basic IO table
            self.io_table = pd.read_excel(
                self.basic_io_file,
                sheet_name='총거래표',
                skiprows=6,
                index_col=[0, 1],
                header=[0, 1]
            )
            
            # Extract sector information
            self.sector_codes = [str(idx[0]) for idx in self.io_table.index if pd.notna(idx[0])]
            self.sector_names = [f"{str(idx[0])}: {str(idx[1])}" for idx in self.io_table.index if pd.notna(idx[0])]
            
            print(f"Loaded basic IO table with {len(self.sector_codes)} sectors")
            
        except Exception as e:
            print(f"Warning: Could not load basic IO table: {str(e)}")
            # Create fallback sector list
            self.sector_codes = [f"{i:04d}" for i in range(1, 398)]
            self.sector_names = [f"{code}: Sector {code}" for code in self.sector_codes]
    
    def get_available_sectors(self) -> List[str]:
        """Get list of available basic sectors for analysis."""
        return self.sector_names
    
    def calculate_economic_impact(
        self, 
        sector_code: str, 
        amount_change: float,
        impact_type: str = 'reduce'
    ) -> Dict:
        """
        Calculate economic impacts of sector demand changes.
        
        Args:
            sector_code: Basic sector code (4-digit)
            amount_change: Amount of change in billion won (10억원)
            impact_type: 'reduce' for reduction, 'increase' for increase
        
        Returns:
            Dictionary containing economic impact results
        """
        # Adjust amount based on impact type
        final_amount = -abs(amount_change) if impact_type == 'reduce' else abs(amount_change)
        
        try:
            # Calculate comprehensive impacts using existing calculator
            results = self.calculator.analyze_comprehensive_impact(
                basic_sector_code=sector_code,
                demand_change=final_amount,
                target_regions=['전지역'],  # National level only
                include_employment=True,
                include_production=True,
                include_imports=True,
                include_value_added=True
            )
            
            # Extract national-level results
            national_results = {
                'sector_code': sector_code,
                'amount_change': final_amount,
                'impact_type': impact_type,
                'employment_impact': results.get('employment', {}).get('전지역', {}),
                'production_impact': results.get('production', {}).get('전지역', {}),
                'import_impact': results.get('imports', {}).get('전지역', {}),
                'value_added_impact': results.get('value_added', {}).get('전지역', {}),
                'summary': results.get('summary', {})
            }
            
            return national_results
            
        except Exception as e:
            print(f"Error in economic impact calculation: {str(e)}")
            return {
                'sector_code': sector_code,
                'amount_change': final_amount,
                'impact_type': impact_type,
                'error': str(e),
                'employment_impact': {},
                'production_impact': {},
                'import_impact': {},
                'value_added_impact': {},
                'summary': {}
            }
    
    def analyze_coal_related_impacts(
        self, 
        coal_sectors: List[str], 
        reduction_amounts: List[float]
    ) -> Dict:
        """
        Analyze impacts of coal consumption reduction across multiple sectors.
        
        Args:
            coal_sectors: List of coal-related sector codes
            reduction_amounts: List of reduction amounts for each sector
        
        Returns:
            Aggregated impact analysis results
        """
        total_impacts = {
            'total_employment_change': 0,
            'total_production_change': 0,
            'total_import_change': 0,
            'total_value_added_change': 0,
            'sector_details': {},
            'employment_by_sector': {},
            'production_by_sector': {},
            'affected_sectors': set()
        }
        
        for sector, amount in zip(coal_sectors, reduction_amounts):
            sector_impact = self.calculate_economic_impact(sector, amount, 'reduce')
            
            # Aggregate impacts
            if 'summary' in sector_impact and sector_impact['summary']:
                summary = sector_impact['summary']
                total_impacts['total_employment_change'] += summary.get('total_employment_change', 0)
                total_impacts['total_production_change'] += summary.get('total_production_change', 0)
                total_impacts['total_import_change'] += summary.get('total_import_change', 0)
                total_impacts['total_value_added_change'] += summary.get('total_value_added_change', 0)
            
            # Store sector details
            total_impacts['sector_details'][sector] = sector_impact
            
            # Aggregate employment impacts by affected sectors
            employment_impacts = sector_impact.get('employment_impact', {})
            for affected_sector, jobs in employment_impacts.items():
                if affected_sector not in total_impacts['employment_by_sector']:
                    total_impacts['employment_by_sector'][affected_sector] = 0
                total_impacts['employment_by_sector'][affected_sector] += jobs
                total_impacts['affected_sectors'].add(affected_sector)
            
            # Aggregate production impacts by affected sectors
            production_impacts = sector_impact.get('production_impact', {})
            for affected_sector, production in production_impacts.items():
                if affected_sector not in total_impacts['production_by_sector']:
                    total_impacts['production_by_sector'][affected_sector] = 0
                total_impacts['production_by_sector'][affected_sector] += production
                total_impacts['affected_sectors'].add(affected_sector)
        
        total_impacts['affected_sectors'] = list(total_impacts['affected_sectors'])
        
        return total_impacts
    
    def find_coal_related_sectors(self) -> List[str]:
        """Find sectors related to coal consumption."""
        coal_keywords = ['석탄', '무연탄', '유연탄', '코크스', '화력', '연소', 'coal']
        coal_sectors = []
        
        for sector_name in self.sector_names:
            for keyword in coal_keywords:
                if keyword in sector_name.lower():
                    # Extract sector code (first part before :)
                    sector_code = sector_name.split(':')[0].strip()
                    coal_sectors.append((sector_code, sector_name))
                    break
        
        return coal_sectors
    
    def create_gui(self):
        """Create the GUI interface for coal impact analysis."""
        self.root = tk.Tk()
        self.root.title("Coal Consumption Impact Analyzer - 석탄 소비 영향 분석기")
        self.root.geometry("1200x800")
        
        # Create main frames
        control_frame = ttk.Frame(self.root)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        results_frame = ttk.Frame(self.root)
        results_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        chart_frame = ttk.Frame(self.root)
        chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Control panel
        ttk.Label(control_frame, text="기본부문 선택 (Basic Sector):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.sector_var = tk.StringVar()
        sector_combo = ttk.Combobox(control_frame, textvariable=self.sector_var, width=60)
        sector_combo['values'] = self.sector_names
        sector_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(control_frame, text="변화량 (10억원) Change Amount:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.amount_var = tk.StringVar(value="1000")
        amount_entry = ttk.Entry(control_frame, textvariable=self.amount_var, width=20)
        amount_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Impact type selection
        ttk.Label(control_frame, text="영향 유형 (Impact Type):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.impact_type_var = tk.StringVar(value="reduce")
        impact_frame = ttk.Frame(control_frame)
        impact_frame.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Radiobutton(impact_frame, text="감소 (Reduce)", variable=self.impact_type_var, value="reduce").pack(side=tk.LEFT)
        ttk.Radiobutton(impact_frame, text="증가 (Increase)", variable=self.impact_type_var, value="increase").pack(side=tk.LEFT, padx=(20,0))
        
        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="분석 실행 (Analyze)", command=self.run_analysis).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="석탄 관련 부문 찾기 (Find Coal Sectors)", command=self.find_coal_sectors).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="결과 지우기 (Clear)", command=self.clear_results).pack(side=tk.LEFT, padx=5)
        
        # Results display
        ttk.Label(results_frame, text="분석 결과 (Analysis Results):").pack(anchor=tk.W)
        
        self.results_text = tk.Text(results_frame, height=35, width=70)
        results_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Chart display
        ttk.Label(chart_frame, text="시각화 (Visualization):").pack(anchor=tk.W)
        
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(8, 10))
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Show initial coal-related sectors
        self.find_coal_sectors()
    
    def run_analysis(self):
        """Run the impact analysis based on user inputs."""
        try:
            sector_selection = self.sector_var.get()
            if not sector_selection:
                messagebox.showerror("오류", "분석할 부문을 선택해주세요.")
                return
            
            # Extract sector code
            sector_code = sector_selection.split(':')[0].strip()
            amount = float(self.amount_var.get())
            impact_type = self.impact_type_var.get()
            
            # Run analysis
            results = self.calculate_economic_impact(sector_code, amount, impact_type)
            
            # Display results
            self.display_results(results)
            
            # Update charts
            self.update_charts(results)
            
        except ValueError:
            messagebox.showerror("오류", "올바른 숫자를 입력해주세요.")
        except Exception as e:
            messagebox.showerror("오류", f"분석 중 오류 발생: {str(e)}")
    
    def find_coal_sectors(self):
        """Find and display coal-related sectors."""
        coal_sectors = self.find_coal_related_sectors()
        
        result_text = "=== 석탄 관련 부문 (Coal-Related Sectors) ===\n\n"
        
        if coal_sectors:
            for sector_code, sector_name in coal_sectors:
                result_text += f"{sector_name}\n"
        else:
            result_text += "석탄 관련 부문을 찾을 수 없습니다.\n"
            result_text += "\n직접 관련 부문을 선택하여 분석하실 수 있습니다:\n"
            result_text += "- 전기 관련 부문\n"
            result_text += "- 철강 관련 부문\n"
            result_text += "- 시멘트 관련 부문\n"
        
        result_text += f"\n총 {len(self.sector_names)}개 기본부문이 분석 가능합니다.\n"
        result_text += "드롭다운에서 원하는 부문을 선택하고 분석하세요.\n"
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, result_text)
    
    def display_results(self, results: Dict):
        """Display analysis results in the text widget."""
        result_text = "=== 경제 영향 분석 결과 (Economic Impact Analysis Results) ===\n\n"
        
        result_text += f"분석 부문: {results['sector_code']}\n"
        result_text += f"변화량: {results['amount_change']:,} 10억원\n"
        result_text += f"영향 유형: {'감소' if results['impact_type'] == 'reduce' else '증가'}\n\n"
        
        if 'error' in results:
            result_text += f"오류: {results['error']}\n"
        else:
            # Summary results
            summary = results.get('summary', {})
            if summary:
                result_text += "=== 종합 영향 (Summary Impact) ===\n"
                result_text += f"총 고용 변화: {summary.get('total_employment_change', 0):,.0f} 명\n"
                result_text += f"총 생산 변화: {summary.get('total_production_change', 0):,.0f} 10억원\n"
                result_text += f"총 수입 변화: {summary.get('total_import_change', 0):,.0f} 10억원\n"
                result_text += f"총 부가가치 변화: {summary.get('total_value_added_change', 0):,.0f} 10억원\n"
                
                if results['amount_change'] != 0:
                    result_text += f"\n고용 집약도: {summary.get('employment_intensity', 0):.2f} 명/10억원\n"
                    result_text += f"생산 승수: {summary.get('production_multiplier', 0):.2f}\n"
                    result_text += f"수입 승수: {summary.get('import_multiplier', 0):.2f}\n"
                    result_text += f"부가가치 승수: {summary.get('value_added_multiplier', 0):.2f}\n"
            
            # Employment impact by sector
            employment_impact = results.get('employment_impact', {})
            if employment_impact:
                result_text += "\n=== 부문별 고용 영향 (Employment Impact by Sector) ===\n"
                sorted_employment = sorted(employment_impact.items(), 
                                         key=lambda x: abs(x[1]), reverse=True)
                for sector, jobs in sorted_employment[:15]:  # Top 15 sectors
                    if abs(jobs) > 0.1:
                        result_text += f"{sector}: {jobs:,.1f} 명\n"
            
            # Production impact by sector
            production_impact = results.get('production_impact', {})
            if production_impact:
                result_text += "\n=== 부문별 생산 영향 (Production Impact by Sector) ===\n"
                sorted_production = sorted(production_impact.items(), 
                                         key=lambda x: abs(x[1]), reverse=True)
                for sector, production in sorted_production[:10]:  # Top 10 sectors
                    if abs(production) > 0.1:
                        result_text += f"{sector}: {production:,.1f} 10억원\n"
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, result_text)
    
    def update_charts(self, results: Dict):
        """Update the visualization charts."""
        self.ax1.clear()
        self.ax2.clear()
        
        try:
            # Employment impact chart
            employment_impact = results.get('employment_impact', {})
            if employment_impact:
                # Get top 10 sectors by absolute impact
                sorted_employment = sorted(employment_impact.items(), 
                                         key=lambda x: abs(x[1]), reverse=True)[:10]
                
                if sorted_employment:
                    sectors = [item[0][:20] + '...' if len(item[0]) > 20 else item[0] 
                              for item in sorted_employment]
                    values = [item[1] for item in sorted_employment]
                    
                    colors = ['red' if v < 0 else 'blue' for v in values]
                    
                    self.ax1.barh(sectors, values, color=colors, alpha=0.7)
                    self.ax1.set_xlabel('Employment Change (명)')
                    self.ax1.set_title('Top 10 Employment Impact by Sector')
                    self.ax1.grid(True, alpha=0.3)
            
            # Summary impact pie chart
            summary = results.get('summary', {})
            if summary:
                categories = []
                values = []
                
                employment = abs(summary.get('total_employment_change', 0))
                production = abs(summary.get('total_production_change', 0)) / 1000  # Convert to trillion won
                imports = abs(summary.get('total_import_change', 0)) / 1000
                value_added = abs(summary.get('total_value_added_change', 0)) / 1000
                
                if employment > 0:
                    categories.append(f'Employment\n({employment:,.0f} 명)')
                    values.append(employment)
                
                if production > 0:
                    categories.append(f'Production\n({production:,.1f} 조원)')
                    values.append(production * 10)  # Scale for visualization
                
                if imports > 0:
                    categories.append(f'Imports\n({imports:,.1f} 조원)')
                    values.append(imports * 10)
                
                if value_added > 0:
                    categories.append(f'Value Added\n({value_added:,.1f} 조원)')
                    values.append(value_added * 10)
                
                if values:
                    self.ax2.pie(values, labels=categories, autopct='%1.1f%%', startangle=90)
                    self.ax2.set_title('Economic Impact Distribution')
            
            self.fig.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            print(f"Chart update error: {str(e)}")
    
    def clear_results(self):
        """Clear all results and charts."""
        self.results_text.delete(1.0, tk.END)
        self.ax1.clear()
        self.ax2.clear()
        self.canvas.draw()
    
    def run_gui(self):
        """Run the GUI application."""
        self.create_gui()
        self.root.mainloop()

def main():
    """Main function to run the Coal Impact Analyzer."""
    print("=== Coal Consumption Impact Analyzer ===")
    print("석탄 소비 영향 분석기")
    print()
    print("이 도구는 다음을 분석합니다:")
    print("- 기본부문 단위의 경제 영향 분석")
    print("- 전국 단위 데이터 사용 (지역 데이터 제외)")
    print("- 기초가격 기준 투입산출표 활용")
    print("- 고용, 생산, 수입, 부가가치 영향 계산")
    print()
    
    try:
        analyzer = CoalImpactAnalyzer()
        print("분석기 초기화 완료. GUI를 시작합니다...")
        analyzer.run_gui()
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        print("필요한 파일들이 iotable 폴더에 있는지 확인해주세요.")

if __name__ == "__main__":
    main()