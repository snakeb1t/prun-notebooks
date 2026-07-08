from textual import on
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.containers import HorizontalGroup
from textual.widgets import Header, Footer, Label, Select, DataTable
import prun_data_frames as pdf
from config import Config
import polars as pl

config = Config(__file__)
bids = pdf.PrunBids(config=config)
orders = pdf.PrunOrders(config=config)

timestamps = bids.timestamps()

mats = pdf.PrunMaterials().source_df["Ticker"].to_list()
mat_options = [(mat, mat) for mat in mats]

cx_options = [(cx.name, cx.name) for cx in pdf.CX]

class AskTable(DataTable):
    pass

class BidTable(DataTable):
    pass

class TimeLabel(Label):
    pass

class PrunSelect(Select):

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        self.app.set_tables()

class BookViewerApp(App):

    CSS_PATH = "book_viewer.tcss"
    hour = 0

    BINDINGS = [
        ("comma", "increase_hour", "Go back one hour"),
        (".", "decrease_hour", "Go forward one hour"),
        ("<", "increase_day", "Go back one day"),
        (">", "decrease_day", "Go forward one day"),
    ]

    def action_increase_hour(self) -> None:
        if len(timestamps) == self.hour + 1:
            return
        self.hour = self.hour + 1
        if len(timestamps) == self.hour + 1:
            # disable left symbol
            self.query_one("#left").add_class("end")
        else:
            self.query_one("#right").remove_class("end")
        self.query_one(TimeLabel).update(timestamps[self.hour])
        self.set_tables()

    def action_decrease_hour(self) -> None:
        if self.hour == 0:
            return
        self.hour = self.hour - 1
        if self.hour == 0:
            # disable right symbol
            self.query_one("#right").add_class("end")
        else:
            self.query_one("#left").remove_class("end")
        self.query_one(TimeLabel).update(timestamps[self.hour])
        self.set_tables()

    def action_increase_day(self) -> None:
        if len(timestamps) == self.hour + 1:
            return
        self.hour = self.hour + 24
        if self.hour > len(timestamps) - 1:
            self.hour = len(timestamps) - 1
            # disable left symbol
            self.query_one("#left").add_class("end")
        else:
            self.query_one("#right").remove_class("end")
        self.query_one(TimeLabel).update(timestamps[self.hour])
        self.set_tables()

    def action_decrease_day(self) -> None:
        if self.hour == 0:
            return
        self.hour = self.hour - 24
        if self.hour < 0:
            self.hour = 0
            # disable right symbol
            self.query_one("#right").add_class("end")
        else:
            self.query_one("#left").remove_class("end")
        self.query_one(TimeLabel).update(timestamps[self.hour])
        self.set_tables()

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        yield AskTable(name="Asks")
        yield BidTable(name="Bids")
        with HorizontalGroup():
            yield PrunSelect(id="material", options=mat_options, value="SF", prompt="Material", name="Material")
            yield PrunSelect(id="cx", options=cx_options, value="CI1", prompt="CX", name="CX")
            yield Label("<", id="left")
            yield TimeLabel(timestamps[self.hour], id="time")
            yield Label(">", id="right", classes="end")
        yield Footer(id="Footer")

    def on_mount(self) -> None:
        self.set_tables()

    def set_tables(self) -> None:
        ask_table = self.query_one(AskTable)
        bid_table = self.query_one(BidTable)

        ask_table.loading = True
        bid_table.loading = True

        self.set_table(ask_table, "ask", "red")
        self.set_table(bid_table, "bid", "green")

        ask_table.loading = False
        bid_table.loading = False

    def set_table(self, table: DataTable, type: str, color: str) -> None:
        ticker = self.query_one("#material").value
        cx = self.query_one("#cx").value

        table.clear(columns=True)
        columns = ("Trader", "Trader Code", "Amount", "Price")

        data_df = bids if type == "bid" else orders
        data_dict_list = (data_df.history_df(self.hour)
                        .filter((pl.col("MaterialTicker").eq(ticker)).and_(pl.col("ExchangeCode").eq(cx)))
                        .with_columns(pl.col("ItemCost").round(3).alias("ItemCost"))
                        .sort(pl.col("rank"))
                        .to_dicts())
        data_tuples = [(
            f"{row['CompanyName']}",
            f"{row['CompanyCode']}",
            f"{row['ItemCount']}",
            f"[{color}]{row['ItemCost']}[/{color}]"
        ) for row in data_dict_list]
        table.add_columns(*columns)
        table.add_rows(data_tuples)

if __name__ == "__main__":
    app = BookViewerApp()
    app.run()