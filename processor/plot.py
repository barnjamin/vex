import algosdk
import base64
import matplotlib.pyplot as plt  # type: ignore
from matplotlib.animation import FuncAnimation  # type: ignore
import numpy as np  # type: ignore

from model import OrderBookSide

# The dom at a current time
# dom == depth of market
Dom = tuple[OrderBookSide, OrderBookSide]
Round = int
Records = dict[Round, Dom]


def chart_current_dom(app_id: int, algod_client: algosdk.v2client.algod.AlgodClient):
    bb = algod_client.application_box_by_name(app_id, b"bid_book")
    bbs = OrderBookSide.from_bytes("bid", base64.b64decode(bb["value"]))

    bb = algod_client.application_box_by_name(app_id, b"ask_book")
    abs = OrderBookSide.from_bytes("ask", base64.b64decode(bb["value"]))

    chart_dom(abs, bbs)


def chart_dom(
    ask: OrderBookSide,
    bid: OrderBookSide,
    name: str = "dom",
    ax: plt.Axes | None = None,
):
    bid_x, bid_height = bid.dom()
    ask_x, ask_height = ask.dom()
    if ax is None:
        plt.clf()
        plt.bar(bid_x, bid_height, color="red")
        plt.bar(ask_x, ask_height, color="blue")
        plt.savefig(f"{name}.png")
    else:
        ax.cla()
        ax.bar(bid_x, bid_height, color="red")
        ax.bar(ask_x, ask_height, color="blue")


def chart_history(records: Records):
    rnds = list(records.keys())
    min_rnd, max_rnd = rnds[0], rnds[-1]

    fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(10, 5))

    def animate(rnd):
        ask, bid = records[rnd]
        axes.set_title(f"Round: {rnd}")
        chart_dom(ask, bid, ax=axes)

    ani = FuncAnimation(
        fig,
        animate,
        frames=np.linspace(min_rnd, max_rnd, max_rnd - min_rnd + 1),
    )

    axes.set_ylim(0, 1000)
    axes.set_xlim(30, 70)

    ani.save("ani.gif", fps=250)
