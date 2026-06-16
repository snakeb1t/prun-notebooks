import polars as ps
from datetime import datetime

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

class PrunPrices(PrunFrame):
    source = "https://rest.fnar.net/csv/prices"

class PrunMaterials(PrunFrame):
    source = "https://rest.fnar.net/csv/materials"

class PrunRecipes(PrunFrame):
    source = "https://rest.fnar.net/csv/buildingrecipes"

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
    print("foo")
