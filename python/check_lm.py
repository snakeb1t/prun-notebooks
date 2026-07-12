from python_ntfy import NtfyClient
from dotenv import load_dotenv
from config import Config
import polars as pl
import os
import prun_data_frames as pdf

def write_ads(df, uri, table_name):
    if df.is_empty():
        return
    df.write_database(
        table_name=table_name,
        connection=uri,
        if_table_exists="replace"
    )

dbconfig = Config(__file__)

uri = dbconfig.get_connection_uri()

# we get the list of planets we want to track from the local sqlite db
# you will have to insert or delete from that table manually if you want to change the list
planets_df = pl.read_database_uri("select planet from lm_planet_targets", uri)
planets = planets_df["planet"].to_list()

# get topic from .env file
load_dotenv()
topic = os.getenv("LM_TOPIC")

client = NtfyClient(topic=topic)
message = ""

print(planets)

for planet in planets:
    ads = pdf.PrunLM(planet=planet).source_df
    table_name = "lm_" + planet.replace(" ", "_").replace("-", "_")

    last_ads = None
    try:
        last_ads = pl.read_database_uri(
                query = f"select * from {table_name}",
                uri = uri)
    except RuntimeError:
        # table doesn't exist, so make one if there were ads
        write_ads(ads, uri, table_name)
        break
    delta = ads.join(last_ads, on="ContractNaturalId", how="anti")
    if not delta.is_empty():
        lines = [f"{row['MaterialTicker']}: {row['type']} {row['MaterialAmount']} @ {row['Price']} from {row['CreatorCompanyName']}" for row in delta.to_dicts()]
        lines = [f"New ads from {planet}:"] + lines + [""]
        message = message + "\n".join(lines)
    write_ads(ads, uri, table_name)

if message != "":
    print("Sending message")
    client.send(message)