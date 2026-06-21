import prun_data_frames as prundf
from prun_data_frames import CX, Currency
from price import EvaluatedPrices, PriceOverride, PriceType
from labor import EvaluatedLabor
import polars as pl
import polars.selectors as cs

class BuildingAnalysis:
    def __init__(self, cx: CX, buildings: prundf.PrunBuildings, prices: EvaluatedPrices, materials: prundf.PrunMaterials, labor: EvaluatedLabor, buy: PriceType=PriceType.BID, sell: PriceType=PriceType.ASK):
        """
        currently doesn't fully analyze recipes with more than one output. UnitsPerDay isn't accurate but Revenue is, for instance.
        """
        self.buildings = buildings
        self.prices = prices
        self.materials = materials
        self.labor = labor
        self.buy = buy.name.capitalize()
        self.sell = sell.name.capitalize()
        self.cx = cx
        self.currency = prundf.CXtoCurrency[cx]

        self.building_labor_cost_df = (self.buildings.source_df
                                    .join(self.buildings.workforces_df, left_on="Ticker", right_on="Building")
                                    .join(self.labor.df, left_on="Level", right_on="EmployeeType")
                                    .with_columns(((pl.col("Capacity")/100)*pl.col("TotalCostPerDayPer100")).alias("TotalLaborCostPerDay"))
                                    .with_columns(pl.col("Ticker").alias("Building"))
                                    .group_by("Building")
                                    .agg(pl.col("TotalLaborCostPerDay").sum()))

    @prundf.lazyproperty
    def unit_efficiency_df(self) -> pl.DataFrame:
        return (self.buildings.recipes_df
            .with_columns(pl.col("Key").str.split(by=":").list.last().alias("Recipe"))
            .drop("Key")
            .with_columns(pl.col("Recipe").alias("Recipe_copy").str.split(by="=>").list.to_struct(fields=["RecipeInputs", "RecipeOutputs"]))
            .unnest("Recipe_copy")

            # make a row per input material
            .with_columns(pl.col("RecipeInputs").str.split(by="-").list.eval(pl.element().str.split_exact(by="x",n=1).struct.rename_fields(["InputQuantity", "InputMaterial"])))
            .explode(pl.col("RecipeInputs"))
            .unnest("RecipeInputs")

            .join(self.prices.df, left_on="InputMaterial",right_on="Ticker")
            .drop("CX")
            .with_columns(pl.col("InputQuantity").str.to_integer(strict=False))
            .filter(pl.col("InputQuantity").is_not_null())

            # use price based on how we're buying
            .with_columns((pl.col(f"{self.buy}Price")*pl.col("InputQuantity")).alias("InputCostPerRun"))
            .group_by("Building", "Duration", "RecipeOutputs", "Recipe")
            .agg(pl.col("InputCostPerRun").sum())

            # make a row per output material
            .with_columns(pl.col("RecipeOutputs").str.split(by="-").list.eval(pl.element().str.split_exact(by="x",n=1).struct.rename_fields(["OutputQuantity","OutputMaterial"])))
            .explode("RecipeOutputs")
            .unnest("RecipeOutputs")

            .join(self.prices.df, left_on="OutputMaterial",right_on="Ticker")
            .drop("CX")
            .with_columns(pl.col("OutputQuantity").str.to_integer(strict=False))
            .filter(pl.col("OutputQuantity").is_not_null())

            .with_columns((60*60*24/pl.col("Duration")).alias("RunsPerDay"))
            .with_columns((pl.col("RunsPerDay")*pl.col("OutputQuantity")).alias("UnitsPerDay"))

            # use price based on how we're selling
            .with_columns((pl.col(f"{self.sell}Price")*pl.col("OutputQuantity")).alias("RevenuePerRun"))

            .group_by("Building", "Duration", "InputCostPerRun", "Recipe", "RunsPerDay", "UnitsPerDay", "OutputMaterial")
            .agg(pl.col("RevenuePerRun").sum(),pl.col("OutputQuantity").sum())

            .with_columns((pl.col("RevenuePerRun")*pl.col("RunsPerDay")).alias("RevenuePerDay"))
            .with_columns((pl.col("InputCostPerRun")*pl.col("RunsPerDay")).alias("InputCostPerDay"))

            .join(self.building_labor_cost_df, on="Building")
            .with_columns((pl.col("InputCostPerDay")+pl.col("TotalLaborCostPerDay")).alias("TotalCostPerDay"))
            .with_columns((pl.col("TotalCostPerDay")/pl.col("UnitsPerDay")).alias("CostPerUnit"))
            .with_columns((pl.col("RevenuePerDay")-pl.col("TotalCostPerDay")).alias("ProfitPerDay"))
            .drop(cs.ends_with("Price")))

    def df(self, efficiency=1.0) -> pl.DataFrame:
        unit_df = self.unit_efficiency_df
        if efficiency == 1.0:
            return unit_df
        # recalculate duration, then recalculate all columns that rely on duration
        return (unit_df.with_columns((pl.col("Duration")/efficiency).alias("Duration"))
                .with_columns((60*60*24/pl.col("Duration")).alias("RunsPerDay"))
                .with_columns((pl.col("RunsPerDay")*pl.col("OutputQuantity")).alias("UnitsPerDay"))
                .with_columns((pl.col("RevenuePerRun")*pl.col("RunsPerDay")).alias("RevenuePerDay"))
                .with_columns((pl.col("InputCostPerRun")*pl.col("RunsPerDay")).alias("InputCostPerDay"))
                .with_columns((pl.col("InputCostPerDay")+pl.col("TotalLaborCostPerDay")).alias("TotalCostPerDay"))
                .with_columns((pl.col("TotalCostPerDay")/pl.col("UnitsPerDay")).alias("CostPerUnit"))
                .with_columns((pl.col("RevenuePerDay")-pl.col("TotalCostPerDay")).alias("ProfitPerDay")))

if __name__ == "__main__":
    pl.Config.set_tbl_cols(-1)

    prices = prundf.PrunPrices()
    evaluated_prices = EvaluatedPrices(prices, CX.CI1)
    labor = EvaluatedLabor(evaluated_prices)
    analysis = BuildingAnalysis(cx=CX.CI1, buildings=prundf.PrunBuildings(), prices=evaluated_prices, materials=prundf.PrunMaterials(), labor=labor)
    print(analysis.unit_efficiency_df.filter(pl.col("Recipe").str.contains("SF").and_(pl.col("Building") == "REF")))
    print(analysis.df(efficiency=1.25).filter(pl.col("Recipe").str.contains("SF").and_(pl.col("Building") == "REF")))
        