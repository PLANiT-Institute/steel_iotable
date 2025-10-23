import pandas as pd
import numpy as np

class RASAnalyzer:
    def __init__(self, basic_matrix_file: str = 'data/iotableforcasting_v3.xlsx', target_sum_file: str = 'data/iotableforcasting_v3.xlsx'):
        self.basic_matrix_file = basic_matrix_file
        self.target_sum_file = target_sum_file
        self.df_basic = None
        self.df_target_sum = None
        self.common_sectors = None
        self._load_base_data() # 초기화 시 기본 데이터 로딩

    def _format_code(self, code):
        """내부에서 사용할 코드 포맷 함수"""
        try:
            return f"{int(float(code)):04d}"
        except (ValueError, TypeError):
            return str(code).strip()

    def _load_base_data(self):
        """기본 행렬과 목표 합계 파일을 로드하고 정리합니다."""
        print("Loading and cleaning base data...")
        # --- basic_matrix (producerprice) 로드 및 정리 ---
        self.df_basic = pd.read_excel(self.basic_matrix_file, sheet_name='producerprice', header=0, index_col=0)
        self.df_basic.index = self.df_basic.index.map(self._format_code)
        self.df_basic.columns = self.df_basic.columns.map(self._format_code)
        # 유효한 코드만 필터링
        basic_rows_cleaned = self.df_basic.index[self.df_basic.index.str.isdigit()]
        basic_cols_cleaned = self.df_basic.columns[self.df_basic.columns.str.isdigit()]
        self.df_basic = self.df_basic.loc[basic_rows_cleaned, basic_cols_cleaned] # 유효한 부분만 남김

        # --- target_sum (integrated) 로드 및 정리 ---
        self.df_target_sum = pd.read_excel(self.target_sum_file, sheet_name='integrated', index_col=0)
        self.df_target_sum.index = self.df_target_sum.index.map(self._format_code)
        if 'code' in self.df_target_sum.index:
            self.df_target_sum = self.df_target_sum.drop('code')
        target_sum_idx_cleaned = self.df_target_sum.index[self.df_target_sum.index.str.isdigit()]
        self.df_target_sum = self.df_target_sum.loc[target_sum_idx_cleaned] # 유효한 부분만 남김

        # --- 공통 섹터 찾기 ---
        common = set(self.df_basic.index) & set(self.df_basic.columns) & set(self.df_target_sum.index)
        if not common:
            raise ValueError("No common sectors found between base matrix and target sums.")
        self.common_sectors = sorted(list(common))
        print(f"Found {len(self.common_sectors)} common sectors.")
        # 공통 섹터 기준으로 데이터 다시 정렬 및 필터링
        self.df_basic = self.df_basic.loc[self.common_sectors, self.common_sectors].fillna(0)
        self.df_target_sum = self.df_target_sum.loc[self.common_sectors]


    def prepare_ras_inputs(self, target_year):
        """특정 목표 연도에 대한 RAS 입력값(A_0, u_1, v_1)을 준비합니다."""
        print(f"\n--- Preparing RAS inputs for target year: {target_year} ---")
        A_0 = self.df_basic.values.astype(float) # 저장된 기본 행렬 사용

        # 단일 레벨 컬럼 이름 정의 (형식: "yyyy_변수명")
        year_str = str(target_year)
        col_interim_demand = f"{year_str}_중간수요계"
        col_final_demand = f"{year_str}_최종수요계"
        col_total_demand = f"{year_str}_총수요계"
        col_interim_input = f"{year_str}_중간투입계(행합)"
        col_value_added = f"{year_str}_부가가치계"

        required_cols = [col_interim_demand, col_final_demand, col_total_demand,
                        col_interim_input, col_value_added]

        # 컬럼 존재 확인
        missing_cols = [col for col in required_cols if col not in self.df_target_sum.columns]
        if missing_cols:
            print(f"Error: Missing required columns: {missing_cols}")
            print(f"Available columns: {[col for col in self.df_target_sum.columns if str(target_year) in str(col)]}")
            raise KeyError(f"Missing required columns for year {target_year}: {missing_cols}")

        # 데이터 추출 및 숫자 변환
        df_target_year = pd.DataFrame(index=self.common_sectors)
        for col in required_cols:
            df_target_year[col] = pd.to_numeric(self.df_target_sum[col], errors='coerce')

        df_target_year = df_target_year.fillna(0)

        # u_1, v_1 계산
        u_1 = df_target_year[col_interim_demand].values.astype(float)
        v_1 = df_target_year[col_interim_input].values.astype(float)
        #v_1 = (df_target_year[col_total_demand] - df_target_year[col_value_added]).values.astype(float)

        # 음수 처리 (오류 가능성 1st priority)
        u_1[u_1 < 0] = 0
        v_1[v_1 < 0] = 0

        print(f"Prepared inputs: A_0 shape {A_0.shape}, u_1 len {len(u_1)}, v_1 len {len(v_1)}")
        return A_0, u_1, v_1

    def ras_algorithm(self, A_0, u_1, v_1, tolerance=1e-6, max_iterations=10000):
        """RAS 알고리즘 (기존 함수와 동일, 클래스 메소드로 편입)"""
        A = A_0.copy()
        A[A == 0] = 1e-10
        print(f"Running RAS for target year... Base matrix shape: {A.shape}")
        # ... (RAS 반복 로직은 동일) ...
        for i in range(max_iterations):
            # Row adjustment
            row_sums = A.sum(axis=1)
            row_sums[row_sums == 0] = 1e-10
            r = u_1 / row_sums
            A = A * r[:, np.newaxis]
            # Column adjustment
            col_sums = A.sum(axis=0)
            col_sums[col_sums == 0] = 1e-10
            s = v_1 / col_sums
            A = A * s
            # Check convergence
            row_error = np.sum(np.abs(A.sum(axis=1) - u_1))
            col_error = np.sum(np.abs(A.sum(axis=0) - v_1))
            total_error = row_error + col_error
            if total_error < tolerance:
                print(f"RAS algorithm converged in {i + 1} iterations.")
                break
        else:
            print(f"Warning: RAS did not converge after {max_iterations} iterations. Total error: {total_error}")
        return A

    def run_analysis_for_year(self, target_year):
        """특정 연도에 대한 RAS 분석을 실행하고 결과를 반환합니다."""
        A_0, u_1, v_1 = self.prepare_ras_inputs(target_year)
        A_1_np = self.ras_algorithm(A_0, u_1, v_1)
        # 결과를 DataFrame으로 변환 (인덱스와 컬럼 이름 사용)
        A_1_df = pd.DataFrame(A_1_np, index=self.common_sectors, columns=self.common_sectors)
        print(f"Successfully generated matrix for {target_year}.")
        return A_1_df

# --- 클래스 사용 예시 ---
if __name__ == "__main__":
    BASIC_FILE = 'data/iotableforcasting_v3.xlsx' # 파일 경로 확인 필요
    TARGET_FILE = 'data/iotableforcasting_v3.xlsx' # 파일 경로 확인 필요
    TARGET_YEARS = [2025, 2030, 2040] # 분석할 연도 목록
    OUTPUT_FILE = "ras_estimated_matrix_v2.xlsx"

    try:
        # 1. 분석기 객체 생성 (데이터 로딩 포함)
        analyzer = RASAnalyzer(BASIC_FILE, TARGET_FILE)

        results_to_save = {}
        # 2. 각 연도별로 분석 실행
        for year in TARGET_YEARS:
            estimated_matrix = analyzer.run_analysis_for_year(year)
            results_to_save[year] = estimated_matrix 

        # 3. 결과 저장
        with pd.ExcelWriter(OUTPUT_FILE) as writer:
            for year, df in results_to_save.items():
                df.to_excel(writer, sheet_name=f"IO_Matrix_{year}")
        print(f"\n--- Analysis Complete ---")
        print(f"All estimated matrices saved to '{OUTPUT_FILE}'")

    except Exception as e:
        print(f"\n--- An Error Occurred ---")
        print(f"Error details: {e}")