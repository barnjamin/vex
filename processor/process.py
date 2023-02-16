import os
from model import OrderBookSide
from plot import chart_history

base_path = "/tmp/boxtmp"


def get_app_path(app_id: int):
    return f"{base_path}/{app_id}"


def get_box_path(app_id: int, box_name: str):
    return f"{get_app_path(app_id)}/{box_name}"


def process_app(app_id: int) -> dict[int, tuple[OrderBookSide, OrderBookSide]]:
    box_names = os.listdir(get_app_path(app_id))
    book_names = [(b"ask_book").hex(), (b"bid_book").hex()]

    parsed_contents: dict[str, dict[int, OrderBookSide]] = {}

    all_rounds: set[int] = set([])
    for box_name in box_names:
        if box_name not in book_names:
            continue

        parsed_contents[box_name] = process_boxes(app_id, box_name)
        all_rounds |= set(parsed_contents[box_name].keys())

    dom_by_round: dict[int, tuple[OrderBookSide, OrderBookSide]] = {}
    last_ask: OrderBookSide | None = None
    last_bid: OrderBookSide | None = None
    for round in list(all_rounds):
        if round in parsed_contents[book_names[0]]:
            last_ask = parsed_contents[book_names[0]][round]
        if round in parsed_contents[book_names[1]]:
            last_bid = parsed_contents[book_names[1]][round]

        # if not one side, use last one for that side
        dom_by_round[round] = (last_ask, last_bid)  # type: ignore

    return dom_by_round


def process_boxes(app_id: int, box_name: str) -> dict[int, OrderBookSide]:
    box_name_decoded = bytes.fromhex(box_name).decode()

    box_path = get_box_path(app_id, box_name)
    box_rounds = os.listdir(box_path)
    # make sure we process them in order
    rounds = sorted([int(round) for round in box_rounds])

    book_by_round: dict[int, OrderBookSide] = {}
    for round in rounds:
        # print("Working on round: ", round)
        box_round_path = f"{box_path}/{round}"
        with open(box_round_path, "rb") as f:
            book_by_round[round] = OrderBookSide.from_bytes(box_name_decoded, f.read())

    return book_by_round


if __name__ == "__main__":
    app_id = 1
    order_books = process_app(app_id)
    chart_history(order_books)
