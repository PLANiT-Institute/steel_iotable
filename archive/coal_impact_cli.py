import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from employment_calculator import EmploymentCalculator

class CoalImpactAnalyzerCLI:
    def __init__(self):
        """
        Initialize the Coal Impact Analyzer CLI for estimating economic impacts 
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
    
    def find_coal_related_sectors(self) -> List[Tuple[str, str]]:
        """Find sectors related to coal consumption."""
        coal_keywords = ['석탄', '무연탄', '유연탄', '코크스', '화력', '연소', 'coal', '전력', '전기']
        coal_sectors = []
        
        for sector_name in self.sector_names:
            for keyword in coal_keywords:
                if keyword in sector_name.lower():
                    # Extract sector code (first part before :)
                    sector_code = sector_name.split(':')[0].strip()
                    coal_sectors.append((sector_code, sector_name))
                    break
        
        return coal_sectors
    
    def display_results(self, results: Dict):
        """Display analysis results."""
        print("=" * 80)
        print("경제 영향 분석 결과 (Economic Impact Analysis Results)")
        print("=" * 80)
        
        print(f"분석 부문: {results['sector_code']}")
        print(f"변화량: {results['amount_change']:,} 10억원")
        print(f"영향 유형: {'감소' if results['impact_type'] == 'reduce' else '증가'}")
        print()
        
        if 'error' in results:
            print(f"오류: {results['error']}")
            return
        
        # Summary results
        summary = results.get('summary', {})
        if summary:
            print("종합 영향 (Summary Impact)")
            print("-" * 40)
            print(f"총 고용 변화: {summary.get('total_employment_change', 0):,.0f} 명")
            print(f"총 생산 변화: {summary.get('total_production_change', 0):,.0f} 10억원")
            print(f"총 수입 변화: {summary.get('total_import_change', 0):,.0f} 10억원")
            print(f"총 부가가치 변화: {summary.get('total_value_added_change', 0):,.0f} 10억원")
            print()
            
            if results['amount_change'] != 0:
                print("승수 효과 (Multiplier Effects)")
                print("-" * 40)
                print(f"고용 집약도: {summary.get('employment_intensity', 0):.2f} 명/10억원")
                print(f"생산 승수: {summary.get('production_multiplier', 0):.2f}")
                print(f"수입 승수: {summary.get('import_multiplier', 0):.2f}")
                print(f"부가가치 승수: {summary.get('value_added_multiplier', 0):.2f}")
                print()
        
        # Employment impact by sector
        employment_impact = results.get('employment_impact', {})
        if employment_impact:
            print("부문별 고용 영향 (Employment Impact by Sector)")
            print("-" * 60)
            sorted_employment = sorted(employment_impact.items(), 
                                     key=lambda x: abs(x[1]), reverse=True)
            for i, (sector, jobs) in enumerate(sorted_employment[:15]):  # Top 15 sectors
                if abs(jobs) > 0.1:
                    print(f"{i+1:2d}. {sector[:50]:<50} {jobs:>10.1f} 명")
            print()
        
        # Production impact by sector
        production_impact = results.get('production_impact', {})
        if production_impact:
            print("부문별 생산 영향 (Production Impact by Sector)")
            print("-" * 60)
            sorted_production = sorted(production_impact.items(), 
                                     key=lambda x: abs(x[1]), reverse=True)
            for i, (sector, production) in enumerate(sorted_production[:10]):  # Top 10 sectors
                if abs(production) > 0.1:
                    print(f"{i+1:2d}. {sector[:40]:<40} {production:>15.1f} 10억원")
            print()
    
    def interactive_analysis(self):
        """Run interactive analysis."""
        print("=" * 80)
        print("석탄 소비 영향 분석기 (Coal Consumption Impact Analyzer)")
        print("=" * 80)
        print()
        print("이 도구는 다음을 분석합니다:")
        print("- 기본부문 단위의 경제 영향 분석")
        print("- 전국 단위 데이터 사용 (지역 데이터 제외)")
        print("- 기초가격 기준 투입산출표 활용")
        print("- 고용, 생산, 수입, 부가가치 영향 계산")
        print()
        
        # Show available sectors
        print(f"분석 가능한 기본부문: {len(self.sector_names)}개")
        print()
        
        # Find coal-related sectors
        coal_sectors = self.find_coal_related_sectors()
        if coal_sectors:
            print("석탄 관련 부문 (Coal-Related Sectors):")
            print("-" * 60)
            for i, (code, name) in enumerate(coal_sectors):
                print(f"{i+1:2d}. {name}")
            print()
        
        while True:
            try:
                print("분석 옵션:")
                print("1. 부문 코드로 분석")
                print("2. 부문 이름 검색")
                print("3. 종료")
                
                choice = input("\n선택 (1-3): ").strip()
                
                if choice == '3':
                    print("분석을 종료합니다.")
                    break
                elif choice == '1':
                    self._analyze_by_code()
                elif choice == '2':
                    self._search_and_analyze()
                else:
                    print("올바른 선택지를 입력해주세요.")
                    continue
                    
            except KeyboardInterrupt:
                print("\n\n분석을 종료합니다.")
                break
            except Exception as e:
                print(f"오류 발생: {str(e)}")
                continue
    
    def _analyze_by_code(self):
        """Analyze by sector code."""
        try:
            sector_code = input("분석할 부문 코드 (4자리): ").strip()
            if len(sector_code) != 4 or not sector_code.isdigit():
                print("4자리 숫자 코드를 입력해주세요.")
                return
            
            amount = float(input("변화량 (10억원, 양수 입력): "))
            if amount <= 0:
                print("양수를 입력해주세요.")
                return
            
            impact_type = input("영향 유형 (reduce/increase) [reduce]: ").strip().lower()
            if not impact_type:
                impact_type = 'reduce'
            
            if impact_type not in ['reduce', 'increase']:
                print("reduce 또는 increase를 입력해주세요.")
                return
            
            print("\n분석 중...")
            results = self.calculate_economic_impact(sector_code, amount, impact_type)
            self.display_results(results)
            
            input("\n계속하려면 Enter를 누르세요...")
            
        except ValueError:
            print("올바른 숫자를 입력해주세요.")
        except Exception as e:
            print(f"분석 중 오류 발생: {str(e)}")
    
    def _search_and_analyze(self):
        """Search sectors and analyze."""
        try:
            search_term = input("검색할 부문 이름: ").strip()
            if not search_term:
                print("검색어를 입력해주세요.")
                return
            
            # Search for matching sectors
            matching_sectors = []
            for sector_name in self.sector_names:
                if search_term.lower() in sector_name.lower():
                    matching_sectors.append(sector_name)
            
            if not matching_sectors:
                print("일치하는 부문을 찾을 수 없습니다.")
                return
            
            print(f"\n검색 결과 ({len(matching_sectors)}개):")
            print("-" * 60)
            for i, sector in enumerate(matching_sectors[:20]):  # Show top 20
                print(f"{i+1:2d}. {sector}")
            
            if len(matching_sectors) > 20:
                print(f"... (총 {len(matching_sectors)}개)")
            
            try:
                choice = int(input(f"\n분석할 부문 번호 (1-{min(20, len(matching_sectors))}): "))
                if choice < 1 or choice > min(20, len(matching_sectors)):
                    print("올바른 번호를 선택해주세요.")
                    return
                
                selected_sector = matching_sectors[choice - 1]
                sector_code = selected_sector.split(':')[0].strip()
                
                amount = float(input("변화량 (10억원, 양수 입력): "))
                if amount <= 0:
                    print("양수를 입력해주세요.")
                    return
                
                impact_type = input("영향 유형 (reduce/increase) [reduce]: ").strip().lower()
                if not impact_type:
                    impact_type = 'reduce'
                
                if impact_type not in ['reduce', 'increase']:
                    print("reduce 또는 increase를 입력해주세요.")
                    return
                
                print("\n분석 중...")
                results = self.calculate_economic_impact(sector_code, amount, impact_type)
                self.display_results(results)
                
                input("\n계속하려면 Enter를 누르세요...")
                
            except ValueError:
                print("올바른 숫자를 입력해주세요.")
                
        except Exception as e:
            print(f"검색 중 오류 발생: {str(e)}")

def main():
    """Main function to run the Coal Impact Analyzer CLI."""
    try:
        analyzer = CoalImpactAnalyzerCLI()
        analyzer.interactive_analysis()
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        print("필요한 파일들이 iotable 폴더에 있는지 확인해주세요.")

if __name__ == "__main__":
    main()