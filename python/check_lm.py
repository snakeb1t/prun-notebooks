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

# get ntfy topic from .env file
load_dotenv()
topic = os.getenv("LM_TOPIC")

# ntfy.sh is a free service where you can make a topic and send and receive messages from it.
# you want to keep the topic a secret, so give it a readable prefix like prun_lm_ and then add some random characters.
# this script will send messages to a configured topic (see above about putting the topic in a local .env file)
# to receive the messages, go to your phone and download the ntfy app. then subscribe to the topic you configured and
# you'll receive a phone notification when your script sends a message!
client = NtfyClient(topic=topic)
message = ""

print("configured planets:")
print(planets)

for planet in planets:
    ads = pdf.PrunLM(planet=planet).source_df
    if ads.is_empty():
        break

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
    delta = (ads
             .join(last_ads, on="ContractNaturalId", how="anti")
             .with_columns((pl.col("Price")/pl.col("MaterialAmount")).round(2).alias("PPU")))
    if not delta.is_empty():
        lines = [f"{row['MaterialTicker']}: {row['type']} {row['MaterialAmount']} @ {row['Price']} {row['PriceCurrency']} (PPU:{row['PPU']})\n" + 
                    " " * 5 + f"in {row['DeliveryTime']}d from {row['CreatorCompanyName']}" for row in delta.to_dicts()]
        lines = [f"New ads from {planet}:\n"] + lines + ["\n"]
        message = message + "\n".join(lines)
    write_ads(ads, uri, table_name)

if message != "":
    print("Sending message")
    client.send(message)