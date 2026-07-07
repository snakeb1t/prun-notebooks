from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.containers import HorizontalGroup
from textual.widgets import Placeholder, Header, Footer, Label, Select
import prun_data_frames as pdf

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

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        yield AskTable("Ask Table")
        yield BidTable("Bid Table")
        with HorizontalGroup():
            yield Select(id="material", options=mat_options, value="SF")
            yield Select(id="cx", options=cx_options, value="CI1")
            yield TimeLabel(id="time")
        yield Footer(id="Footer")

if __name__ == "__main__":
    app = BookViewerApp()
    app.run()