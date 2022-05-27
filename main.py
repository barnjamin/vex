from algosdk.v2client import algod
from algosdk.future.transaction import BoxReference, logic
from algosdk.atomic_transaction_composer import AccountTransactionSigner

from sandbox import get_sandbox_accounts
from vex import vex, ask_pq, bid_pq
from application_client import ApplicationClient

host = "http://localhost:4001"
token = "a" * 64

client = ApplicationClient(algod.AlgodClient(token, host), vex)

accts = get_sandbox_accounts()
addr, sk = accts[-1]
signer = AccountTransactionSigner(sk)

boxes = [BoxReference(0, ask_pq.box_name_str), BoxReference(0, bid_pq.box_name_str)]

if __name__ == "__main__":

    app_id, app_addr = client.create(signer, int(4e8))
    print(f"Created {app_id} with app address {app_addr}")

    result = client.bootstrap(signer, [], boxes=boxes)
    print(result)

    import random

    orders = 500
    for x in range(orders):
        price, size = random.randint(50, 100), 10
        bid = x % 2 == 0
        print(
            "{} Filled {}".format(
                "bid" if bid else "ask",
                client.new_order(signer, [(bid, price, size)], boxes=boxes),
            )
        )
