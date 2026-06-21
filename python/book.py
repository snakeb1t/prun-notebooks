import prun_data_frames as prundf
import polars as pl
import sqlite3 as sql
import os
from pathlib import Path
from config import Config

config = Config(__file__)
connection_uri = config.get_connection_uri

orders = prundf.PrunOrders()
bids = prundf.PrunBids()

orders.source_df.write_database(
    table_name="orders",
    connection=connection_uri,
    if_table_exists="append"  # Options: 'fail', 'replace', 'append'
)

bids.source_df.write_database(
    table_name="bids",
    connection=connection_uri,
    if_table_exists="append"  # Options: 'fail', 'replace', 'append'
)

connection = sql.connect(config.get_dbpath)

cursor = connection.cursor()
cursor.execute("DELETE FROM orders WHERE timestamp < datetime('now', '-7 days');")
cursor.execute("DELETE FROM bids WHERE timestamp < datetime('now', '-7 days');")
connection.commit()

connection.close()
