import base64
from pydoc import cli
from algosdk import *
from algosdk.v2client import algod
from algosdk.future.transaction import *
from pyteal import Mode, OptimizeOptions, compileTeal
from algosdk.kmd import KMDClient
from box_contract import router

host = "http://localhost:4001"
token = "a"*64

KMD_ADDRESS = "http://localhost:4002"
KMD_TOKEN = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

KMD_WALLET_NAME = "unencrypted-default-wallet"
KMD_WALLET_PASSWORD = ""

def get_sandbox_accounts():
    kmd = KMDClient(KMD_TOKEN, KMD_ADDRESS)
    wallets = kmd.list_wallets()

    walletID = None
    for wallet in wallets:
        if wallet["name"] == KMD_WALLET_NAME:
            walletID = wallet["id"]
            break

    if walletID is None:
        raise Exception("Wallet not found: {}".format(KMD_WALLET_NAME))

    walletHandle = kmd.init_wallet_handle(walletID, KMD_WALLET_PASSWORD)

    try:
        addresses = kmd.list_keys(walletHandle)
        privateKeys = [
            kmd.export_key(walletHandle, KMD_WALLET_PASSWORD, addr)
            for addr in addresses
        ]
        kmdAccounts = [(addresses[i], privateKeys[i]) for i in range(len(privateKeys))]
    finally:
        kmd.release_wallet_handle(walletHandle)

    return kmdAccounts




def create_app(
    client: algod.AlgodClient, addr: str, pk: str, approval: str, clear: str
) -> int:
    # Get suggested params from network
    sp = client.suggested_params()

    print("Compiling approval program")
    # Read in approval teal source && compile
    app_result = client.compile(approval)
    app_bytes = base64.b64decode(app_result["result"])

    print("Compiling clear program")
    # Read in clear teal source && compile
    clear_result = client.compile(clear)
    clear_bytes = base64.b64decode(clear_result["result"])

    # We dont need no stinkin storage
    schema = StateSchema(0, 0)

    # Create the transaction
    create_txn = ApplicationCreateTxn(
        addr,
        sp,
        0,
        app_bytes,
        clear_bytes,
        schema,
        schema,
    )

    # Sign it
    signed_txn = create_txn.sign(pk)

    # Ship it
    txid = client.send_transaction(signed_txn)

    print("App create sent, waiting for confirmation")
    # Wait for the result so we can return the app id
    result = wait_for_confirmation(client, txid, 4)

    app_id = result["application-index"]
    app_addr = logic.get_application_address(app_id)

    # Send some Algos to the app address so it can do stuff
    sp = client.suggested_params()
    ptxn = PaymentTxn(addr, sp, app_addr, int(5e6))
    txid = client.send_transaction(ptxn.sign(sk))
    print("Payment sent, waiting for confirmation")
    wait_for_confirmation(client, txid, 4)

    return app_id, app_addr


def update_app(
    client: algod.AlgodClient, addr: str, pk: str, id: int, approval: str, clear: str
) -> int:
    # Get suggested params from network
    sp = client.suggested_params()

    print("Cmmpiling approval contract")
    # Read in approval teal source && compile
    app_result = client.compile(approval)
    app_bytes = base64.b64decode(app_result["result"])

    print("Compiling clear contract")
    # Read in clear teal source && compile
    clear_result = client.compile(clear)
    clear_bytes = base64.b64decode(clear_result["result"])

    # Create the transaction
    update_txn = ApplicationUpdateTxn(addr, sp, id, app_bytes, clear_bytes)

    # Sign it
    signed_txn = update_txn.sign(pk)

    # Ship it
    txid = client.send_transaction(signed_txn)

    print("Updating sent, waiting for confirmation")
    # Wait for the result
    result = wait_for_confirmation(client, txid, 4)
    print("Confirmed in round: {}".format(result["confirmed-round"]))


def call_app(client: algod.AlgodClient, addr: str, sk: str, id: int):
    sp = client.suggested_params()
    box_name = "test"
    sel = bytes.fromhex("978c398a")
    txn = ApplicationCallTxn(addr, sp, id, OnComplete.NoOpOC, boxes=[BoxReference(0, box_name)], app_args=[sel, abi.StringType().encode(box_name)])
    signed = txn.sign(sk)
    #print(dir(signed))
    txid = client.send_transaction(signed)
    #encoded = encoding.msgpack_encode(signed)
    #decoded = encoding.future_msgpack_decode(encoded)
    #print(encoded, decoded.transaction)
    print(wait_for_confirmation(client, txid, 2))


if __name__ == "__main__":
    approval, clear, iface = router.build_program()

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

    # with open("approval.teal", "r") as f:
    #    approval = f.read()

    # with open("clear.teal", "r") as f:
    #    clear = f.read()

    client = algod.AlgodClient(token, host)

    accts = get_sandbox_accounts()
    addr, sk = accts[0]
    print(addr, sk)

    app_id = 1
    app_addr = logic.get_application_address(app_id)

    #app_id, app_addr = create_app(client, addr, sk, approval, clear)
    #print(f"Created {app_id} with app address {app_addr}")

    update_app(client, addr, sk, app_id, approval, clear)

    #sp = client.suggested_params()
    #ptxn = PaymentTxn(addr, sp, app_addr, int(5e6))
    #txid = client.send_transaction(ptxn.sign(sk))
    #print("Payment sent, waiting for confirmation")
    #wait_for_confirmation(client, txid, 4)

    call_app(client, addr, sk, app_id)
