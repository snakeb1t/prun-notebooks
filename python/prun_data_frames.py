import polars as ps
from datetime import datetime
from enum import Enum, auto

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
        return ps.read_csv(self.source, infer_schema_length=self.schema_len)

class PrunBuildings(PrunFrame):
    source = "https://rest.fnar.net/csv/buildings"
    costs_source = "https://rest.fnar.net/csv/buildingcosts"
    recipes_source = "https://rest.fnar.net/csv/buildingrecipes"
    workforces_source = "https://rest.fnar.net/csv/buildingworkforces"
    @lazyproperty
    def costs_df(self):
        return ps.read_csv(self.costs_source, infer_schema_length=self.schema_len)
    @lazyproperty
    def recipes_df(self):
        return ps.read_csv(self.recipes_source, infer_schema_length=self.schema_len)
    @lazyproperty
    def workforces_df(self):
        return ps.read_csv(self.workforces_source, infer_schema_length=self.schema_len)

class PrunPrices(PrunFrame):
    source = "https://rest.fnar.net/csv/prices"

class PrunMaterials(PrunFrame):
    source = "https://rest.fnar.net/csv/materials"

class PrunOrders(PrunFrame):
    source = "https://rest.fnar.net/csv/orders"
    @lazyproperty
    def source_df(self):
        df = super().source_df
        return df.with_columns(ps.concat_str([ps.col("MaterialTicker"),ps.col("ExchangeCode")], separator=".").alias("CXTicker")) \
            .with_columns(timestamp = datetime.now())

class PrunBids(PrunFrame):
    source = "https://rest.fnar.net/csv/bids"
    @lazyproperty
    def source_df(self):
        df = super().source_df
        return df.with_columns(ps.concat_str([ps.col("MaterialTicker"),ps.col("ExchangeCode")], separator=".").alias("CXTicker")) \
            .with_columns(timestamp = datetime.now())

if __name__ == "__main__":
    pass