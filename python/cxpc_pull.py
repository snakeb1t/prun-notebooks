from prun_data_frames import CX, Currency, PrunCXPCTicker, PrunMaterials
import polars as pl
import polars.selectors as cs
import os
from pathlib import Path
from config import Config

connection_uri = Config(__file__).get_connection_uri()

materials_df = PrunMaterials().source_df

# really don't want to hammer on the api for all cxes
cx = CX.CI1

dfs = [PrunCXPCTicker(ticker,cx).source_df for ticker in materials_df["Ticker"].to_list()]

all_cxpc_df = pl.concat(dfs, how="vertical")

all_cxpc_df.write_database(
    table_name="cxpc",
    connection=connection_uri,
    if_table_exists="replace"
)