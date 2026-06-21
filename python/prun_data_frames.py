import polars as pl
from datetime import datetime
from enum import Enum, auto
from config import Config

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
    schema_len = 10000
    @lazyproperty
    def source_df(self):
        return pl.read_csv(self.source, infer_schema_length=self.schema_len)

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
    @lazyproperty
    def source_df(self):
        df = super().source_df
        return df.with_columns(pl.concat_str([pl.col("MaterialTicker"),pl.col("ExchangeCode")], separator=".").alias("CXTicker")) \
            .with_columns(timestamp = datetime.now())

class PrunBids(PrunFrame):
    source = "https://rest.fnar.net/csv/bids"
    @lazyproperty
    def source_df(self):
        df = super().source_df
        return df.with_columns(pl.concat_str([pl.col("MaterialTicker"),pl.col("ExchangeCode")], separator=".").alias("CXTicker")) \
            .with_columns(timestamp = datetime.now())

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
    
if __name__ == "__main__":
    config = Config(__file__)
    print(PrunCXPCAll(config).source_df)