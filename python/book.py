import prun_data_frames as prundf
import polars as ps

if __name__ == "__main__":
    orders = prundf.PrunOrders()
    bids = prundf.PrunBids()

    print(orders.source_df)