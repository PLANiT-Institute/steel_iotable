import os
import random
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# from libs.io_analyzer import IOTableAnalyzer
# from libs.hydrogen_analyzer import HydrogenTableAnalyzer
# from scenario_analyzer import ScenarioAnalyzer

plt.rc('font', family='AppleGothic')  # for windows: family='Malgun Gothic'
plt.rc('font', family='NanumGothic')   
plt.rc('axes', unicode_minus=False)  # 마이너스 부호 깨짐 방지
sns.set_theme(style="whitegrid", font="Malgun Gothic")

# class visualiser:
#     def __init__(self, output_dir="chart_outputs"):
#         """분석기들을 초기화하고 결과물 저장 폴더를 설정합니다."""
#         print("분석기(Analyzers)를 초기화합니다...")
#         self.output_dir = output_dir
#         os.makedirs(self.output_dir, exist_ok=True)
#         self.io_analyzer = IOTableAnalyzer()
#         self.h2_analyzer = HydrogenTableAnalyzer()
#         self.scenario_analyzer = ScenarioAnalyzer()
#         print("분석기 초기화 완료.")

# def run_scenario_visualisation(self):

#     # if not self.scenario_analyzer:
#     #     print("시나리오 분석기가 초기화되지 않아 시각화를 건너뜁니다.")
#     #     return

#     # try:
#     self.scenario_analyzer.run_all_scenario()
#     aggregated_results = self.scenario_analyzer.aggregated_results
#     self.plot_1_
#     print("시나리오 분석 완료.")

