import prun_data_frames as prun
import polars as pl
import polars.selectors as cs
from enum import Enum, auto

class PriceType(Enum):
    BUY = auto()
    SELL = auto()

class PriceOverride:
    """
    specifies price overrides for the given ticker
    """
    def __init__(self, ticker: str, cx: prun.CX, price: float, price_type: PriceType):
        self.ticker = ticker
        self.cx = cx.name
        self.price = price
        self.price_type = price_type

    @prun.lazyproperty
    def get(self):
        return (self.ticker, self.cx, self.price, self.price_type.name)

class EvaluatedPrice:
    def __init__(self, price_source: prun.PrunPrices, cx: prun.CX, overrides: list[PriceOverride] = []):
        self.price_source = price_source
        self.cx = cx
        self.override_tuples = [item.get for item in overrides]
    @prun.lazyproperty
    def df(self):
        """
        returns a polars df with the schema ["Ticker", "CX", "BuyPrice", "SellPrice"].
        the buy and sell price can be overridden by the list of overrides passed into the class
        """
        override_df = pl.DataFrame(self.override_tuples, schema={
            "Ticker": pl.String,
            "CX": pl.String,
            "OverridePrice": pl.Float16,
            "OverrideType": pl.String})
        return (self.price_source.source_df.select("Ticker",cs.starts_with(self.cx.name))
                .drop(cs.ends_with("Amt"),cs.ends_with("Avail"),cs.ends_with("Price"))
                .with_columns(pl.lit(["BUY","SELL"]).alias("OverrideType"))
                .explode("OverrideType")
                .join(override_df, on=["Ticker","OverrideType"],how="full",coalesce=True)
                # make a column called "FinalBuyPrice" that has the override buy price if present, otherwise use average price
                .with_columns(pl.when(pl.col("OverridePrice").is_not_null()
                                   .and_(pl.col("OverrideType").eq("BUY")
                                         .or_(pl.col("OverrideType").eq("BOTH"))))
                           .then(pl.col("OverridePrice"))
                           .otherwise(pl.when(pl.col("OverrideType").eq("BUY"))
                                      .then(pl.col(f"{self.cx.name}-Average"))
                                      .otherwise(None))
                           .alias("FinalBuyPrice"))
                # make a column called "FinalSellPrice" that has the override sell price if present, otherwise use average price
                .with_columns(pl.when(pl.col("OverridePrice").is_not_null()
                                      .and_(pl.col("OverrideType").eq("SELL")
                                           .or_(pl.col("OverrideType").eq("BOTH"))))
                            .then(pl.col("OverridePrice"))
                            .otherwise(pl.when(pl.col("OverrideType").eq("SELL"))
                                       .then(pl.col(f"{self.cx.name}-Average"))
                                       .otherwise(None))
                            .alias("FinalSellPrice"))
                .group_by("Ticker","CX")
                .agg(pl.col("FinalBuyPrice").drop_nulls().unique().alias("BuyPrice"),
                     pl.col("FinalSellPrice").drop_nulls().unique().alias("SellPrice"))
                .explode("BuyPrice")
                .explode("SellPrice")
                .with_columns(pl.lit(f"{self.cx.name}").alias("CX"))
                .sort("Ticker"))

if __name__ == "__main__":
    prices = prun.PrunPrices()
    print(EvaluatedPrice(prices, cx=prun.CX.CI1, overrides=[PriceOverride("AR", prun.CX.CI1, "20", PriceType.BUY),PriceOverride("AR", prun.CX.CI1, "100", PriceType.SELL)]).df)
    print(EvaluatedPrice(prices, cx=prun.CX.CI1).df)