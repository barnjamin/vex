from algosdk.v2client import algod
from algosdk.future.transaction import BoxReference, logic
from algosdk.atomic_transaction_composer import AccountTransactionSigner

from sandbox import get_sandbox_accounts
from vex import vex
from application_client import ApplicationClient

host = "http://localhost:4001"
token = "a" * 64

client = ApplicationClient(algod.AlgodClient(token, host), vex)

accts = get_sandbox_accounts()
addr, sk = accts[-1]
signer = AccountTransactionSigner(sk)

boxes = [BoxReference(0, "ask_book"), BoxReference(0, "bid_book")]

if __name__ == "__main__":

    app_id, app_addr = client.create(signer, int(4e6))
    print(f"Created {app_id} with app address {app_addr}")

    result = client.bootstrap(signer, [], boxes=boxes)
    print(result.__dict__)

    price, size = 500, 10
    result = client.new_order(signer, [(price, size)], boxes=boxes)
    print(result.__dict__)

    result = client.fill_root(signer, [], boxes=boxes)
    print(result.__dict__)
