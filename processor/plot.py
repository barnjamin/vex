import algosdk
import base64
import matplotlib.pyplot as plt  # type: ignore
from model import OrderBookSide


def chart_current_dom(app_id: int, algod_client: algosdk.v2client.algod.AlgodClient):
    bb = algod_client.application_box_by_name(app_id, b"bid_book")
    bbs = OrderBookSide.from_bytes("bid", base64.b64decode(bb["value"]))

    bb = algod_client.application_box_by_name(app_id, b"ask_book")
    abs = OrderBookSide.from_bytes("ask", base64.b64decode(bb["value"]))

    chart_dom(abs, bbs)


def chart_dom(ask: OrderBookSide, bid: OrderBookSide, name: str = "dom"):
    plt.bar(*bid.dom())
    plt.bar(*ask.dom())
    plt.savefig(f"{name}.png")
