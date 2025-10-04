import pandas as pd
from typing import Dict

class DemandChangeAnalyzer:
    def __init__(self, data_file: str = 'data/scenarios.xlsx'):
        self.data_file = data_file
        self.demand_change_df = None
        self.load_data()

    def load_data(self):
        self.demand_change_df = pd.read_excel(self.data_file, sheet_name='Scenario1')
        #print(self.demand_change_df.head())
        print(f"Loaded demand change data with {len(self.demand_change_df)} scenarios")

    def get_scenario(self, sector: str, year: int):
        return self.demand_change_df[self.demand_change_df['sector'] == sector][year]

if __name__ == "__main__":
    analyzer = DemandChangeAnalyzer()
    my_sector = input("Please enter the sector: ")
    my_year = int(input("Please enter the year: "))

    print(analyzer.get_scenario(my_sector, my_year).item())

