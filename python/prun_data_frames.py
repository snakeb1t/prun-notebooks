import polars as pl
from datetime import datetime
from enum import Enum, auto
from config import Config
import requests

class CX(Enum):
    CI1 = auto()
    CI2 = auto()
    NC1 = auto()
    NC2 = auto()
    AI1 = auto()
    IC1 = auto()

class Currency(Enum):
    CIS = auto()
    AIC = auto()
    ICA = auto()
    NCC = auto()

CXtoCurrency = {
    CX.CI1: Currency.CIS,
    CX.CI2: Currency.CIS,
    CX.NC1: Currency.NCC,
    CX.NC2: Currency.NCC,
    CX.AI1: Currency.AIC,
    CX.IC1: Currency.ICA
}

# decorator that caches the return value of a method so it's not recalculated each time it's called
class lazyproperty:
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls):
        if instance is None:
            return self
        else:
            value = self.func(instance)
            setattr(instance, self.func.__name__, value)
            return value

class PrunFrame:
    source = ""
    table_name = "none"
    schema_len = 10000
    def __init__(self, config: Config | None = None):
        self.config = config
    @lazyproperty
    def source_df(self):
        return pl.read_csv(self.source, infer_schema_length=self.schema_len)
    def history_df(self, hour: int | None = None):
        if self.config == None:
            return None
        query = f"SELECT * FROM {self.table_name}"
        if hour != None:
            if hour < 0:
                return None
            hour = hour + 1
            query = query + f" WHERE timestamp > datetime('now', 'localtime', '-{hour} hours') AND timestamp < datetime('now', 'localtime', '-{hour-1} hours')"
        df = pl.read_database_uri(
            query = query,
            uri = self.config.get_connection_uri()
        )
        return df
    def timestamps(self):
        if self.config == None:
            return None
        df = pl.read_database_uri(
            query = f"SELECT DISTINCT(timestamp) AS ts FROM {self.table_name} ORDER BY ts DESC",
            uri = self.config.get_connection_uri()
        )
        return df["ts"].cast(pl.String).to_list()

class PrunBuildings(PrunFrame):
    source = "https://rest.fnar.net/csv/buildings"
    costs_source = "https://rest.fnar.net/csv/buildingcosts"
    recipes_source = "https://rest.fnar.net/csv/buildingrecipes"
    workforces_source = "https://rest.fnar.net/csv/buildingworkforces"
    @lazyproperty
    def costs_df(self):
        return pl.read_csv(self.costs_source, infer_schema_length=self.schema_len)
    @lazyproperty
    def recipes_df(self):
        return pl.read_csv(self.recipes_source, infer_schema_length=self.schema_len)
    @lazyproperty
    def workforces_df(self):
        return pl.read_csv(self.workforces_source, infer_schema_length=self.schema_len)

class PrunPrices(PrunFrame):
    source = "https://rest.fnar.net/csv/prices"

class PrunMaterials(PrunFrame):
    source = "https://rest.fnar.net/csv/materials"

class PrunOrders(PrunFrame):
    source = "https://rest.fnar.net/csv/orders"
    table_name = "orders"
    @lazyproperty
    def source_df(self):
        df = super().source_df
        return (df.with_row_index("id")
            .with_columns(pl.concat_str([pl.col("MaterialTicker"),pl.col("ExchangeCode")], separator=".").alias("CXTicker"))
            .with_columns(pl.col("id").rank(descending=True,method="ordinal").over("CXTicker").alias("rank"))
            .drop("id")
            .with_columns(timestamp = datetime.now())
            .with_columns(pl.col("timestamp").dt.truncate("1h").alias("timestamp")))

class PrunBids(PrunFrame):
    source = "https://rest.fnar.net/csv/bids"
    table_name = "bids"
    @lazyproperty
    def source_df(self):
        df = super().source_df
        return (df.with_row_index("id")
            .with_columns(pl.concat_str([pl.col("MaterialTicker"),pl.col("ExchangeCode")], separator=".").alias("CXTicker"))
            .with_columns(pl.col("id").rank(method="ordinal").over("CXTicker").alias("rank"))
            .drop("id")
            .with_columns(timestamp = datetime.now())
            .with_columns(pl.col("timestamp").dt.truncate("1h").alias("timestamp")))

class PrunCXPCTicker(PrunFrame):
    def __init__(self, ticker: str, cx: CX):
        self.ticker = ticker
        self.cx = cx
        self.source = f"https://rest.fnar.net/csv/cxpc/{ticker}.{cx.name}"
        self.schema = {
            "Interval": pl.String,
            "TimeEpochMs": pl.Int64,
            "Open": pl.Float64,
            "Close": pl.Float64,
            "Volume": pl.Float64,
            "Traded": pl.Int64
        }
    @lazyproperty
    def source_df(self):
        df = super().source_df
        df = df.cast(self.schema)
        return (df.with_columns(pl.from_epoch(pl.col("TimeEpochMs").cast(pl.Int64),time_unit="ms").alias("ts"))
                .filter(pl.col("Interval") == "DAY_ONE")
                .drop("Interval","TimeEpochMs")
                .with_columns(pl.lit(f"{self.ticker}").alias("Ticker"))
                .with_columns(pl.lit(f"{self.cx.name}").alias("CX")))

class PrunCXPCAll():
    def __init__(self, config: Config):
        self.config = config 
    @lazyproperty
    def source_df(self):
        uri = self.config.get_connection_uri()
        return pl.read_database_uri("select * from cxpc", uri)
    @lazyproperty
    def enhanced_df(self):
        df = (self.source_df.sort("ts",descending=False)
              .with_columns(pl.col("Volume").cast(pl.Int64).alias("Volume")))
        return (df.with_columns(pl.concat_str([pl.col("Ticker"),pl.col("CX")], separator=".").alias("CXTicker"))
                    .with_columns(pl.col("Volume")
                                .rolling_mean_by(pl.col("ts"),window_size="7d")
                                .over("CXTicker")
                                .floor()
                                .alias("7DayAvgVolume"))
                    .with_columns(pl.col("Volume").rolling_mean_by(pl.col("ts"),window_size="30d")
                                .over("CXTicker")
                                .floor()
                                .alias("30DayAvgVolume"))
                    .with_columns(pl.col("Traded").rolling_mean_by(pl.col("ts"),window_size="7d")
                                .over("CXTicker")
                                .floor()
                                .alias("7DayAvgTraded"))
                    .with_columns(pl.col("Traded").rolling_mean_by(pl.col("ts"),window_size="30d")
                                .over("CXTicker")
                                .floor()
                                .alias("30DayAvgTraded"))
                    .with_columns(pl.col("Close").rolling_mean_by(pl.col("ts"),window_size="7d")
                                .over("CXTicker")
                                .round(2)
                                .alias("7DayAvgPrice"))
                    .with_columns(pl.col("Close").rolling_mean_by(pl.col("ts"),window_size="30d")
                                .over("CXTicker")
                                .round(2)
                                .alias("30DayAvgPrice"))
                    #.with_columns((pl.sum("Volume").rolling(index_column="ts",period="7d")/pl.sum("Traded").rolling(index_column="ts",period="7d")).alias("7DayVWAP")))
                    .with_columns((pl.col("7DayAvgVolume")/pl.col("7DayAvgTraded")).alias("7DayVWAP"))
                    .with_columns((pl.col("30DayAvgVolume")/pl.col("30DayAvgTraded")).alias("30DayVWAP"))
                    .with_columns(((pl.col("7DayVWAP").pct_change(n=7).over("CXTicker"))*100).alias("7DayPriceChange"))
                    .with_columns(((pl.col("30DayVWAP").pct_change(n=7).over("CXTicker"))*100).alias("30DayPriceChange")))

class PrunLM():
    def __init__(self, planet: str):
        self.planet = planet
    @lazyproperty
    def source_df(self):
        url = f"https://rest.fnar.net/localmarket/planet/{self.planet}"
        resp_json = None
        try:
            resp_json = requests.get(url=url).json()
        except requests.exceptions.JSONDecodeError:
            # probably empty response due to no ads
            # return empty dataframe
            return pl.DataFrame()
        # don't care about shipping right now
        sell_df = pl.DataFrame()
        if resp_json['SellingAds']:
            sell_df = pl.from_dicts(resp_json['SellingAds']).with_columns(pl.lit("SELL").alias("type"))
        buy_df = pl.DataFrame()
        if resp_json['BuyingAds']:
            buy_df = pl.from_dicts(resp_json['BuyingAds']).with_columns(pl.lit("BUY").alias("type"))
        if sell_df.is_empty():
            return buy_df
        if buy_df.is_empty():
            return sell_df
        return pl.concat([buy_df, sell_df],how="vertical").select("ContractNaturalId", "type",
                                                                  "CreatorCompanyName", "MaterialTicker",
                                                                  "MaterialAmount", "Price")

    
if __name__ == "__main__":
    pl.Config.set_tbl_cols(-1)
    pl.Config.set_tbl_width_chars(-1)
    pl.Config.set_thousands_separator(",")
    pl.Config.set_tbl_rows(20)
    config = Config(__file__)
    cxpc_all = PrunCXPCAll(config)
    bids = PrunBids(config=config)
    #print(cxpc_all.source_df)
    #print(cxpc_all.enhanced_df.filter(pl.col("Ticker") == "AMM").sort("ts", descending=True).head(21))
    print(bids.source_df.sort(["CXTicker", "rank"]).filter(pl.col("MaterialTicker").eq("RAT")))
    print(PrunLM("Coldwell Deep").source_df)