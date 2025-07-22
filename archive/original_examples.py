"""
Archive of original example functions and development code.
These functions were used during development but are not needed for the main analysis.
"""

def example_pig_iron_analysis():
    """Example usage of pig iron employment impact analysis."""
    
    # Initialize calculator with employment table and basic IO table
    calculator = EmploymentCalculator(
        'iotable/2020지역_부속표_고용표_통합중분류.xlsx',
        'iotable/(표)(2020실측)투입산출표_생산자가격_기본부문.xlsx'
    )
    
    print("=== 선철(Pig Iron) 산업 고용 영향 분석 ===\n")
    
    # Example: 1000억원 decrease in pig iron demand (representing industrial decline)
    pig_iron_demand_change = -1000  # -1000 billion won
    
    # Analyze employment impact across all regions
    regional_impacts = calculator.analyze_pig_iron_employment_impact(
        pig_iron_demand_change=pig_iron_demand_change,
        target_regions=['전지역', '경기', '충남', '울산', '강원', '경북']
    )
    
    # Summarize results
    summary = calculator.summarize_pig_iron_analysis(regional_impacts, pig_iron_demand_change)
    
    print(f"선철 수요 변화: {summary['pig_iron_demand_change_billion_won']:,.0f}억원")
    print(f"총 고용 변화: {summary['total_employment_change']:,.0f}명")
    print(f"고용 집약도: {summary['employment_intensity_per_billion_won']:.2f}명/천억원")
    print(f"영향받는 지역 수: {summary['affected_regions']}개")
    
    print("\n=== 지역별 고용 영향 ===")
    for region, total_impact in summary['regional_totals'].items():
        if abs(total_impact) > 1:  # Show only significant impacts
            print(f"{region}: {total_impact:,.0f}명")
    
    print("\n=== 주요 지역 상세 영향 (부문별) ===")
    for region in ['전지역', '경기', '충남', '울산']:
        if region in regional_impacts:
            print(f"\n{region}:")
            for sector, impact in regional_impacts[region].items():
                if abs(impact) > 1:
                    print(f"  {sector}: {impact:,.0f}명")
    
    return calculator, summary

def example_usage():
    """Example usage of the EmploymentCalculator."""
    
    calculator = EmploymentCalculator('iotable/2020지역_부속표_고용표_통합중분류.xlsx')
    
    # Debug: Check data structure
    print("Data shape:", calculator.employment_coefficients.shape)
    print("Regions:", calculator.regions)
    print("First 10 sectors:", calculator.sectors[:10])
    
    # Find sectors related to steel, semiconductors, and automobiles
    search_results = calculator.find_sectors(['철강', '반도체', '자동차'])
    print("\nAvailable sectors:")
    for term, matches in search_results.items():
        print(f"{term}: {matches}")
    
    # Example calculation with actual sectors
    if search_results['철강'] and search_results['자동차']:
        sector_demands = {
            search_results['철강'][0]: -1000,   # 100억원 increase in steel
            search_results['자동차'][0]: 50   # 50억원 decrease in automobiles
        }
        
        regional_impacts = calculator.calculate_direct_employment_impact(
            sector_demands, 
            region='경기'
        )
        
        summary = calculator.summarize_employment_impact(regional_impacts)
        
        print("\n고용 영향 분석 결과:")
        print(f"총 일자리 창출: {summary['total_job_creation']:.0f}명")
        print(f"총 일자리 감소: {summary['total_job_loss']:.0f}명")
        print(f"순 고용 변화: {summary['net_employment_change']:.0f}명")
    
    return calculator

def example_usage():
    """Example usage of the EmploymentCalculator."""
    
    calculator = EmploymentCalculator('iotable/2020지역_부속표_고용표_통합중분류.xlsx')
    
    # Debug: Check data structure
    print("Data shape:", calculator.employment_coefficients.shape)
    print("Regions:", calculator.regions)
    print("First 10 sectors:", calculator.sectors[:10])
    
    # Find sectors related to steel, semiconductors, and automobiles
    search_results = calculator.find_sectors(['철강', '반도체', '자동차'])
    print("\nAvailable sectors:")
    for term, matches in search_results.items():
        print(f"{term}: {matches}")
    
    # Example calculation with actual sectors
    if search_results['철강'] and search_results['자동차']:
        sector_demands = {
            search_results['철강'][0]: -1000,   # 100억원 increase in steel
            search_results['자동차'][0]: 50   # 50억원 decrease in automobiles
        }
        
        regional_impacts = calculator.calculate_direct_employment_impact(
            sector_demands, 
            region='경기'
        )
        
        summary = calculator.summarize_employment_impact(regional_impacts)
        
        print("\n고용 영향 분석 결과:")
        print(f"총 일자리 창출: {summary['total_job_creation']:.0f}명")
        print(f"총 일자리 감소: {summary['total_job_loss']:.0f}명")
        print(f"순 고용 변화: {summary['net_employment_change']:.0f}명")
    
    return calculator