import prun_data_frames as prun
import polars as pl
from price import EvaluatedPrices

class EvaluatedLabor:
    pioneer_df = pl.DataFrame({
        "EmployeeType": ["PIONEER"] * 5,
        "Provision": ["COF", "DW", "RAT", "OVE", "PWO"],
        "RatePer100": [.5, 4, 4, .5, .2]
    },
    schema={
        "EmployeeType": pl.String,
        "Provision": pl.String,
        "RatePer100": pl.Float16
    })
    settler_df = pl.DataFrame({
        "EmployeeType": ["SETTLER"] * 6,
        "Provision": ["KOM", "DW", "RAT", "EXO", "REP", "PT"],
        "RatePer100": [1, 5, 6, .5, .2, .5]
    },
    schema={
        "EmployeeType": pl.String,
        "Provision": pl.String,
        "RatePer100": pl.Float16
    })
    technician_df = pl.DataFrame({
        "EmployeeType": ["TECHNICIAN"] * 7,
        "Provision": ["ALE", "DW", "RAT", "MED", "SC", "HMS", "SCN"],
        "RatePer100": [1, 7.5, 7, .5, .1, .5, .1]
    },
    schema={
        "EmployeeType": pl.String,
        "Provision": pl.String,
        "RatePer100": pl.Float16
    })
    engineer_df = pl.DataFrame({
        "EmployeeType": ["ENGINEER"] * 7,
        "Provision": ["DW", "MED", "GIN", "FIM", "VG", "HSS", "PDA"],
        "RatePer100": [10, .5, 1, 7, .2, .2, .1]
    },
    schema={
        "EmployeeType": pl.String,
        "Provision": pl.String,
        "RatePer100": pl.Float16
    })
    scientist_df = pl.DataFrame({
        "EmployeeType": ["SCIENTIST"] * 7,
        "Provision": ["DW", "MED", "WIN", "MEA", "NST", "LC", "WS"],
        "RatePer100": [10, .5, 1, 7, .1, .2, .05]
    },
    schema={
        "EmployeeType": pl.String,
        "Provision": pl.String,
        "RatePer100": pl.Float16
    })
    def __init__(self, prices: EvaluatedPrices):
        labor_df = pl.concat([self.pioneer_df, self.settler_df, self.technician_df, self.engineer_df,self.scientist_df], how="vertical")
        print(labor_df)

if __name__ == "__main__":
    prices_source = prun.PrunPrices()
    evaluated_prices = EvaluatedPrices(prices_source, cx=prun.CX.CI1)
    labor = EvaluatedLabor(evaluated_prices)