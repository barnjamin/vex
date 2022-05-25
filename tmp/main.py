from algosdk import *
from algosdk.v2client import algod
from algosdk.future.transaction import *
from algosdk.atomic_transaction_composer import *
from algosdk.dryrun_results import *
from pyteal import Mode, OptimizeOptions, compileTeal
from deploy import *
from contract import router

host = "http://localhost:4001"
token = "a" * 64

client = algod.AlgodClient(token, host)

accts = get_sandbox_accounts()
addr, sk = accts[0]
signer = AccountTransactionSigner(sk)

approval, clear, iface = router.build_program()

iface = abi.Interface.undictify(iface)
approval = compileTeal(
    approval,
    mode=Mode.Application,
    version=7,
    assembleConstants=True,
    optimize=OptimizeOptions(scratch_slots=True),
)
clear = compileTeal(
    clear,
    mode=Mode.Application,
    version=7,
    assembleConstants=True,
    optimize=OptimizeOptions(scratch_slots=True),
)


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
    meth = get_method("boostrap")

    boxes = [BoxReference(0, "orders-pages")]

    sp = client.suggested_params()
    atc = AtomicTransactionComposer()
    atc.add_method_call(app_id, meth, addr, sp, signer, [], boxes=boxes)
    result = atc.execute(client, 2)
    for res in result.abi_results:
        print(res.__dict__)


def call_new_order(app_id: int):
    meth = get_method("new_order")

    new_order = (True, 100, 500)

    obox = base64.b64decode("b3JkZXJzAA==").decode("utf-8")
    boxes = [BoxReference(0, obox), BoxReference(0, "orders-pages")]

    sp = client.suggested_params()
    atc = AtomicTransactionComposer()
    atc.add_method_call(app_id, meth, addr, sp, signer, [new_order], boxes=boxes)

    # result = atc.dryrun(client)
    # for res in result.trace.txns:
    #    print(res.app_trace(StackPrinterConfig(max_value_width=0)))

    result = atc.execute(client, 2)
    for res in result.abi_results:
        print(f"Stored order in slot: {res.return_value}")


def call_read_order(app_id: int):
    meth = get_method("read_order")

    slot = 0
    obox = base64.b64decode("b3JkZXJzAA==").decode("utf-8")
    boxes = [BoxReference(0, obox), BoxReference(0, "orders-pages")]

    sp = client.suggested_params()
    atc = AtomicTransactionComposer()
    atc.add_method_call(app_id, meth, addr, sp, signer, [slot], boxes=boxes)

    # result = atc.dryrun(client)
    # for res in result.trace.txns:
    #    print(res.app_trace(StackPrinterConfig(max_value_width=0)))

    result = atc.execute(client, 2)
    for res in result.abi_results:
        print(f"Order at slot {slot}: {res.return_value}")


if __name__ == "__main__":
    app_id, app_addr = create()
    print("Calling bootstrap")
    call_bootstrap(app_id)
    print("Calling new order")
    call_new_order(app_id)
    call_read_order(app_id)
    # print("Deleting app")
    # delete(app_id)
