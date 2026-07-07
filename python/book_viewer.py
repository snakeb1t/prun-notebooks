from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.containers import HorizontalGroup
from textual.widgets import Placeholder, Header, Footer, Label, Select, Static
import prun_data_frames as pdf
from config import Config

config = Config(__file__)
bids = pdf.PrunBids(config=config)
orders = pdf.PrunOrders(config=config)

timestamps = bids.timestamps()

mats = pdf.PrunMaterials().source_df["Ticker"].to_list()
mat_options = [(mat, mat) for mat in mats]

cx_options = [(cx.name, cx.name) for cx in pdf.CX]

class AskTable(Placeholder):
    pass

class BidTable(Placeholder):
    pass

class TimeLabel(Label):
    pass

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

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        yield AskTable("Ask Table")
        yield BidTable("Bid Table")
        with HorizontalGroup():
            yield Select(id="material", options=mat_options, value="SF", prompt="Material", name="Material")
            yield Select(id="cx", options=cx_options, value="CI1", prompt="CX", name="CX")
            yield Label("<", id="left")
            yield TimeLabel(timestamps[self.hour], id="time")
            yield Label(">", id="right", classes="end")
        yield Footer(id="Footer")

if __name__ == "__main__":
    app = BookViewerApp()
    app.run()