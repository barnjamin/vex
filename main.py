import base64
from algosdk import *
from algosdk.v2client import algod
from algosdk.future.transaction import *
from algosdk.atomic_transaction_composer import *
from algosdk.dryrun_results import *
from pyteal import OptimizeOptions, compileTeal
from deploy import *
from contract import router

host = "http://localhost:4001"
token = "a" * 64

client = algod.AlgodClient(token, host)

accts = get_sandbox_accounts()
addr, sk = accts[-1]
signer = AccountTransactionSigner(sk)

approval, clear, iface = router.compile_program(
    version=7,
    assembleConstants=True,
    optimize=OptimizeOptions(scratch_slots=True),
)

boxes = [BoxReference(0, "ask_book"), BoxReference(0, "bid_book")]


def get_method(name: str) -> abi.Method:
    for m in iface.methods:
        if m.name == name:
            return m
    raise Exception("cant find that method: {}".format(name))


def create():
    app_id, app_addr = create_app(client, addr, sk, approval, clear)
    print(f"Created {app_id} with app address {app_addr}")
    return app_id, app_addr


def update(app_id: int):
    update_app(client, addr, sk, app_id, approval, clear)


def delete(app_id: int):
    delete_app(client, addr, sk, app_id)


def call_bootstrap(app_id: int):
    meth = get_method("bootstrap")

    sp = client.suggested_params()
    atc = AtomicTransactionComposer()
    atc.add_method_call(app_id, meth, addr, sp, signer, [], boxes=boxes)
    atc.execute(client, 2)


def call_new_order(app_id: int, price: int, size: int):
    meth = get_method("new_order")

    sp = client.suggested_params()
    atc = AtomicTransactionComposer()
    atc.add_method_call(app_id, meth, addr, sp, signer, [(price, size)], boxes=boxes)
    result = atc.execute(client, 2)
    for txr in result.abi_results:
        if "logs" in txr.tx_info:
            print([base64.b64decode(l) for l in txr.tx_info["logs"]])


def call_peek_root(app_id: int):
    meth = get_method("peek_root")

    sp = client.suggested_params()
    atc = AtomicTransactionComposer()
    atc.add_method_call(app_id, meth, addr, sp, signer, [], boxes=boxes)

    result = atc.execute(client, 2)
    for res in result.abi_results:
        print(f"Order at root: {res.return_value}")


def call_fill_root(app_id: int):
    meth = get_method("fill_root")

    sp = client.suggested_params()
    atc = AtomicTransactionComposer()
    atc.add_method_call(app_id, meth, addr, sp, signer, [], boxes=boxes)

    result = atc.execute(client, 2)
    for res in result.abi_results:

        if "logs" in res.tx_info:
            print([base64.b64decode(l) for l in res.tx_info["logs"]])

        if res.return_value is not None:
            print(f"Popped root: {res.return_value}")


def call_cancel_order(app_id: int, order_idx: int):

    resting_order = call_read_order(app_id, order_idx)

    meth = get_method("cancel_order")

    sp = client.suggested_params()
    atc = AtomicTransactionComposer()
    atc.add_method_call(app_id, meth, addr, sp, signer, [resting_order], boxes=boxes)
    atc.execute(client, 2)


def call_read_order(app_id: int, order_idx: int):
    meth = get_method("read_order")

    sp = client.suggested_params()
    atc = AtomicTransactionComposer()
    atc.add_method_call(app_id, meth, addr, sp, signer, [order_idx], boxes=boxes)

    result = atc.execute(client, 2)
    for res in result.abi_results:
        if res.return_value is not None:
            return res.return_value


if __name__ == "__main__":
    import random

    app_id, app_addr = create()
    print("Calling bootstrap")

    call_bootstrap(app_id)
    print("Calling new order")

    order_cnt = 5 
    for idx in range(order_cnt):
        # call_new_order(app_id, random.randint(100, 200), random.randint(1, 10) * 100)
        call_new_order(app_id, order_cnt - idx, 100)

    for idx in range(order_cnt):
        print(call_read_order(app_id, idx))

    for idx in range(order_cnt):
        call_fill_root(app_id)
