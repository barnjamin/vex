from algosdk import *
from algosdk.v2client import algod
from algosdk.future.transaction import *
from algosdk.atomic_transaction_composer import *
from pyteal import Mode, OptimizeOptions, compileTeal
from deploy import *
from contract import router

host = "http://localhost:4001"
token = "a" * 64

client = algod.AlgodClient(token, host)

accts = get_sandbox_accounts()
addr, sk = accts[-1]
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

    sp = client.suggested_params()
    atc = AtomicTransactionComposer()
    atc.add_method_call(app_id, meth, addr, sp, signer, [])
    result = atc.execute(client, 2)
    for res in result.abi_results:
        print(res.__dict__)


def call_new_order(app_id: int):
    meth = get_method("order")

    sp = client.suggested_params()
    atc = AtomicTransactionComposer()
    atc.add_method_call(app_id, meth, addr, sp, signer, [])
    result = atc.execute(client, 2)

    for res in result.abi_results:
        print(res.__dict__)


if __name__ == "__main__":
    app_id, app_addr = create()
    call_bootstrap(app_id)
    call_new_order(app_id)
    delete(app_id)
