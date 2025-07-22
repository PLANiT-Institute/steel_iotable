import pandas as pd
import os

def get_complete_steel_mapping():
    """Get the complete mapping of steel-related basic sectors to intermediate classification"""
    print("COMPLETE STEEL SECTOR MAPPING ANALYSIS")
    print("=" * 80)
    
    # From the analysis, we found these steel-related basic sectors
    steel_basic_sectors = {
        '2711': '선철 (Pig iron)',
        '2712': '합금철 (Ferroalloys)', 
        '2713': '조강 (Crude steel)',
        '2721': '철근 및 봉강 (Rebar and bar steel)',
        '2722': '형강 (Shaped steel)',
        '2725': '열연강판 (Hot-rolled steel sheets)',
        '2726': '강선 (Steel wire)',
        '2727': '철강관 (Steel pipes)',
        '2730': '냉간압연강재 (Cold-rolled steel)',
        '2791': '표면처리강재 (Surface-treated steel)',
        '2799': '기타 철강1차제품 (Other primary steel products)'
    }
    
    # Intermediate classification
    intermediate_steel_sectors = {
        '27': '철강1차제품 (Primary steel products)',
        '28': '비철금속괴 및 1차제품 (Non-ferrous metal ingots and primary products)'
    }
    
    print("1. BASIC SECTORS (4-digit codes) - Steel Related:")
    print("-" * 50)
    for code, name in steel_basic_sectors.items():
        print(f"   {code}: {name}")
    
    print(f"\n2. INTERMEDIATE CLASSIFICATION (2-digit codes) - Steel Related:")
    print("-" * 60)
    for code, name in intermediate_steel_sectors.items():
        print(f"   {code}: {name}")
    
    print(f"\n3. MAPPING STRUCTURE:")
    print("-" * 30)
    print("   All basic sectors starting with '27' (2711-2799) → Intermediate code '27'")
    print("   - This includes pig iron (2711) and all other primary steel products")
    print("   - The mapping follows the first two digits of the basic sector code")
    print("   - Basic sectors 27xx → Intermediate sector 27")
    
    print(f"\n4. AGGREGATION METHOD:")
    print("-" * 25)
    print("   - Employment data: Simple summation across all basic sectors within each intermediate category")
    print("   - Production data: Simple summation of output values")
    print("   - This follows standard input-output table aggregation practices")
    
    return steel_basic_sectors, intermediate_steel_sectors

def verify_employment_data():
    """Verify employment data for sector 27"""
    print(f"\n5. EMPLOYMENT DATA VERIFICATION:")
    print("-" * 40)
    
    iotable_path = "/Users/sanghyun/github/steel_iotable/iotable"
    employment_file = os.path.join(iotable_path, "2020지역_부속표_고용표_통합중분류.xlsx")
    
    try:
        # Read employment data
        df = pd.read_excel(employment_file, sheet_name='취업자수', header=None)
        
        # Find sector 27 data
        for idx in range(len(df)):
            row = df.iloc[idx]
            if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip() == '27':
                sector_name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else "Unknown"
                print(f"   Sector 27 ({sector_name}) employment data found at row {idx}")
                
                # Show employment by region
                regions = ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종', 
                          '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주', '전지역']
                
                print(f"   Regional employment for sector 27:")
                for col_idx in range(2, min(len(row), 20)):
                    if pd.notna(row.iloc[col_idx]) and col_idx-2 < len(regions):
                        employment = row.iloc[col_idx]
                        if isinstance(employment, (int, float)) and employment > 0:
                            print(f"     {regions[col_idx-2]}: {employment:,.1f} persons")
                break
                
    except Exception as e:
        print(f"   Error reading employment data: {e}")

def create_mapping_summary():
    """Create a final summary of the mapping"""
    print(f"\n6. FINAL MAPPING SUMMARY:")
    print("-" * 35)
    print(f"   QUESTION: Which intermediate classification includes pig iron (basic sector 2711)?")
    print(f"   ANSWER: Intermediate classification code 27 - 철강1차제품 (Primary steel products)")
    print()
    print(f"   RATIONALE:")
    print(f"   - Basic sector 2711 (선철/Pig iron) maps to intermediate sector 27")
    print(f"   - This mapping follows the standard Korean industrial classification structure")
    print(f"   - The first two digits of basic sector codes determine the intermediate classification")
    print(f"   - All steel primary products (codes 2711-2799) are aggregated into code 27")
    print()
    print(f"   OTHER STEEL-RELATED INTERMEDIATE SECTORS:")
    print(f"   - Code 28: 비철금속괴 및 1차제품 (Non-ferrous metal ingots and primary products)")
    print(f"   - Code 29: 금속 주물 (Metal casting)")
    print(f"   - Code 30: 금속가공제품 (Fabricated metal products)")

# Run the complete analysis
steel_basic, steel_intermediate = get_complete_steel_mapping()
verify_employment_data()
create_mapping_summary()

print(f"\n{'='*80}")
print("ANALYSIS COMPLETE")
print(f"{'='*80}")