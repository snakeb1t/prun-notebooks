import prun_data_frames as prundf
from prun_data_frames import CX, Currency
import polars as ps

class BuildingAnalysis:
    def __init__(self, cx: CX, buildings: prundf.PrunBuildings, prices: prundf.PrunPrices, materials: prundf.PrunMaterials):
        self.buildings = buildings
        self.prices = prices
        self.materials = materials
        self.cx = cx
        self.currency = prundf.CXtoCurrency[cx]

        print(buildings.source_df)
        print(buildings.costs_df)
        print(buildings.recipes_df
              .join(buildings.source_df, left_on="Building", right_on="Ticker")
              .with_columns(ps.col("Key").str.split(by=":").list.last().alias("Recipe"))
              .drop("Key")
              .drop("Name")
              .with_columns(ps.col("Recipe").alias("Recipe_copy").str.split(by="=>").list.to_struct(fields=["RecipeInputs", "RecipeOutputs"]))
              .unnest("Recipe_copy")
              .with_columns(ps.col("RecipeInputs").str.split(by="-").list.eval(ps.element().str.split_exact(by="x",n=1).struct.rename_fields(["InputQuantity", "InputMaterial"])))
              # explode creates a row per element of list
              .explode(ps.col("RecipeInputs"))
              # unnest creates a column per element in struct
              .unnest("RecipeInputs")
              .with_columns(ps.col("InputQuantity").str.to_integer(strict=False))
              .filter(ps.col("InputQuantity").is_not_null())
              .group_by(ps.col("Building"),ps.col("Duration"),ps.col("Area"),ps.col("Expertise"),ps.col("RecipeOutputs"))
              .agg(ps.struct("InputQuantity","InputMaterial").alias("RecipeInputs"))
              .with_columns(ps.col("RecipeOutputs").str.split(by="-").list.eval(ps.element().str.split_exact(by="x",n=1).struct.rename_fields(["OutputQuantity","OutputMaterial"])))
              .explode(ps.col("RecipeOutputs"))
              .unnest(ps.col("RecipeOutputs"))
              .with_columns(ps.col("OutputQuantity").str.to_integer(strict=False))
              .filter(ps.col("OutputQuantity").is_not_null())
              .group_by(ps.col("Building"),ps.col("Duration"),ps.col("Area"),ps.col("Expertise"),ps.col("RecipeInputs"))
              .agg(ps.struct("OutputQuantity","OutputMaterial").alias("RecipeOutputs")))



if __name__ == "__main__":
    BuildingAnalysis(cx=CX.CI1, buildings=prundf.PrunBuildings(), prices=prundf.PrunPrices, materials=prundf.PrunMaterials)
        