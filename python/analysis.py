import prun_data_frames as prundf
from prun_data_frames import CX, Currency
from price import EvaluatedPrices, PriceOverride
import polars as pl

class BuildingAnalysis:
    def __init__(self, cx: CX, buildings: prundf.PrunBuildings, prices: EvaluatedPrices, materials: prundf.PrunMaterials):
        self.buildings = buildings
        self.prices = prices
        self.materials = materials
        self.cx = cx
        self.currency = prundf.CXtoCurrency[cx]

        print(buildings.source_df)
        print(buildings.costs_df)
        print(buildings.recipes_df
              .with_columns(pl.col("Key").str.split(by=":").list.last().alias("Recipe"))
              .drop("Key")
              #.drop("Name")
              .with_columns(pl.col("Recipe").alias("Recipe_copy").str.split(by="=>").list.to_struct(fields=["RecipeInputs", "RecipeOutputs"]))
              .unnest("Recipe_copy")
              # make a row per input material
              .with_columns(pl.col("RecipeInputs").str.split(by="-").list.eval(pl.element().str.split_exact(by="x",n=1).struct.rename_fields(["InputQuantity", "InputMaterial"])))
              .explode(pl.col("RecipeInputs"))
              .unnest("RecipeInputs")
              .join(prices.df, left_on="InputMaterial",right_on="Ticker")
              .drop("SellPrice", "CX")
              .with_columns(pl.col("InputQuantity").str.to_integer(strict=False))
              .filter(pl.col("InputQuantity").is_not_null())
              # calculate input costs per run
              .with_columns((pl.col("BuyPrice")*pl.col("InputQuantity")).alias("InputCostPerRun"))
              .group_by("Building", "Duration", "RecipeOutputs", "Recipe")
              .agg(pl.col("InputCostPerRun").sum())
              # make a row per output material
              .with_columns(pl.col("RecipeOutputs").str.split(by="-").list.eval(pl.element().str.split_exact(by="x",n=1).struct.rename_fields(["OutputQuantity","OutputMaterial"])))
              .explode("RecipeOutputs")
              .unnest("RecipeOutputs")
              .join(prices.df, left_on="OutputMaterial",right_on="Ticker")
              .drop("BuyPrice", "CX")
              .with_columns(pl.col("OutputQuantity").str.to_integer(strict=False))
              .filter(pl.col("OutputQuantity").is_not_null())
              # calculate revenue per run
              .with_columns((pl.col("SellPrice")*pl.col("OutputQuantity")).alias("RevenuePerRun"))
              .group_by("Building", "Duration", "InputCostPerRun", "Recipe")
              .agg(pl.col("RevenuePerRun").sum())
              .with_columns((pl.col("RevenuePerRun")*((60*60*24)/pl.col("Duration"))).alias("RevenuePerDay"))
              .with_columns((pl.col("InputCostPerRun")*((60*60*24)/pl.col("Duration"))).alias("InputCostPerDay")))
              #.filter(pl.col("Recipe").str.contains("SF").and_(pl.col("Building") == "REF")))

if __name__ == "__main__":
    prices = prundf.PrunPrices()
    evaluated_prices = EvaluatedPrices(prices, CX.CI1)
    BuildingAnalysis(cx=CX.CI1, buildings=prundf.PrunBuildings(), prices=evaluated_prices, materials=prundf.PrunMaterials())
        