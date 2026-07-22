from python_ntfy import NtfyClient
from dotenv import load_dotenv
from config import Config
import polars as pl
import os
import prun_data_frames as pdf

# get ntfy topic from .env file
load_dotenv()
topic = os.getenv("ORDERS_TOPIC")
company_code = os.getenv("COMPANY_CODE")
table_name = f"lower_orders_{company_code}"

dbconfig = Config(__file__)
uri = dbconfig.get_connection_uri()

client = NtfyClient(topic=topic)

orders = pdf.PrunOrders(dbconfig)
lower_orders_df = (orders.source_df.filter((pl.col("CompanyCode") == f"{company_code}").any().over("CXTicker"))
                                    .with_columns(pl.col("ItemCost").min().over("CXTicker").alias("LowestCost"))
                                    .with_columns(pl.col("CompanyCode").get(pl.col("rank").arg_max()).over("CXTicker").alias("LowestCompany"))
                                    .filter((pl.col("CompanyCode") == f"{company_code}") & (pl.col("ItemCost") > pl.col("LowestCost")))
                                    .drop("timestamp"))
if lower_orders_df.is_empty():
    print("no lower orders found, exiting")
    exit(0)

db_history_df = pl.DataFrame()
try:
    db_history_df = pl.read_database_uri(
        query = f"select * from {table_name}",
        uri = uri
    )
except RuntimeError:
    print("table doesn't exist yet, making one and exiting")
    lower_orders_df.write_database(
        table_name=table_name,
        connection=uri,
        if_table_exists="replace"
    )
    exit(0)

delta = lower_orders_df.join(db_history_df, on=["MaterialTicker","LowestCost"], how="anti")
lines = [f"{row['LowestCompany']} made a cheaper order ({row['LowestCost']}) than your price ({row['ItemCost']}) for {row['CXTicker']}" for row in delta.to_dicts()]

message = "\n\n".join(lines)
if message:
    print("Sending message")
    client.send(message)

lower_orders_df.write_database(
    table_name=table_name,
    connection=uri,
    if_table_exists="replace"
)