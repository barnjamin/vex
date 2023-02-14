import random
from beaker import sandbox, client
from beaker.client.api_providers import Sandbox, Network
from vex import Vex


def demo():
    # TODO: can the App tell us which boxes it wants?
    boxes = [
        (0, Vex.ask_queue._box_name),
        (0, Vex.bid_queue._box_name),
        (0, ""),
        (0, ""),
        (0, ""),
        (0, ""),
        (0, ""),
        (0, ""),
    ]

    # Setup
    algod_client = Sandbox(network=Network.SandNet).algod()

    acct = sandbox.kmd.get_accounts().pop()

    app_client = client.ApplicationClient(algod_client, Vex(), signer=acct.signer)

    app_id, _, _ = app_client.create()

    print(f"CREATED APP ID: {app_id}")

    app_client.fund(int(1e7))
    app_client.call(Vex.boostrap, boxes=boxes)

    # Simulate incoming orders
    orders = 200
    mid = 50
    for x in range(orders):
        bid = x % 2 == 0
        side = "bid" if bid else "ask"

        start, stop = mid - 3, mid + 5
        if bid:
            start, stop = mid - 5, mid + 3

        price, size = random.randint(start, stop), random.randint(1, 10) * 10
        result = app_client.call(
            Vex.new_order, is_bid=bid, price=price, size=size, boxes=boxes
        )
        print("{} Filled {}".format(side, result.return_value))

    return app_id


if __name__ == "__main__":
    app_id = demo()
