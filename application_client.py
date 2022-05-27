import base64
from typing import List, Tuple

from algosdk.algod import AlgodClient
from application import Application
from pyteal import OptimizeOptions
from algosdk.abi import Method
from algosdk.account import address_from_private_key
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    AccountTransactionSigner,
    TransactionWithSigner,
)
from algosdk.future.transaction import (
    logic,
    wait_for_confirmation,
    PaymentTxn,
    ApplicationCreateTxn,
    ApplicationDeleteTxn,
    OnComplete,
)
from algosdk.v2client.algod import AlgodClient


class ApplicationClient:
    def __init__(self, client: AlgodClient, app: Application):
        self.client = client
        self.app = app

        approval, clear, contract = self.app.router.compile_program(
            version=7,
            assembleConstants=True,
            optimize=OptimizeOptions(scratch_slots=True),
        )
        self.approval = approval
        self.clear = clear
        self.contract = contract

        methods = {}
        for m in self.contract.methods:
            caller = self._get_caller(m)
            setattr(self, m.name, caller)
            methods[m.name] = m

        setattr(self, "methods", methods)

    def _get_caller(self, m):
        def call(signer, args, **kwargs):
            return self.call(signer, m, args, **kwargs)

        return call

    def create(
        self, signer: AccountTransactionSigner, seed_amt: int = 0
    ) -> Tuple[int, str]:
        approval_result = self.client.compile(self.approval)
        approval_program = base64.b64decode(approval_result["result"])

        clear_result = self.client.compile(self.clear)
        clear_program = base64.b64decode(clear_result["result"])

        sp = self.client.suggested_params()

        sender = address_from_private_key(signer.private_key)
        ctx = AtomicTransactionComposer()
        ctx.add_transaction(
            TransactionWithSigner(
                ApplicationCreateTxn(
                    sender,
                    sp,
                    OnComplete.NoOpOC,
                    approval_program,
                    clear_program,
                    self.app.global_schema(),
                    self.app.local_schema(),
                ),
                signer,
            )
        )
        result = ctx.execute(self.client, 2)

        tx_result = self.client.pending_transaction_info(result.tx_ids[0])
        self.app_id = tx_result["application-index"]
        self.app_addr = logic.get_application_address(self.app_id)

        if seed_amt > 0:
            ptxn = PaymentTxn(sender, sp, self.app_addr, seed_amt)
            txid = self.client.send_transaction(ptxn.sign(signer.private_key))
            wait_for_confirmation(self.client, txid, 2)

        return self.app_id, self.app_addr

    def delete(self, signer: AccountTransactionSigner):
        sp = self.client.suggested_params()

        ctx = AtomicTransactionComposer()
        ctx.add_transaction(
            TransactionWithSigner(
                ApplicationDeleteTxn(
                    address_from_private_key(signer.private_key), sp, self.app_id
                ),
                signer,
            )
        )
        return ctx.execute(self.client, 2)

    def compose(
        self,
        signer: AccountTransactionSigner,
        method: Method,
        args: List[any],
        ctx: AtomicTransactionComposer,
        **kwargs
    ):
        sp = self.client.suggested_params()
        addr = address_from_private_key(signer.private_key)
        ctx.add_method_call(
            self.app_id,
            method,
            addr,
            sp,
            signer,
            method_args=args,
            **kwargs,
        )

    def call(
        self,
        signer: AccountTransactionSigner,
        method: Method,
        args: List[any],
        **kwargs
    ):
        ctx = AtomicTransactionComposer()
        sp = self.client.suggested_params()
        addr = address_from_private_key(signer.private_key)
        ctx.add_method_call(
            self.app_id,
            method,
            addr,
            sp,
            signer,
            method_args=args,
            **kwargs,
        )
        result = ctx.execute(self.client, 2)
        # for res in result.abi_results:
        #    if 'logs' in res.tx_info:
        #        print([base64.b64decode(l) for l in res.tx_info['logs']])

        return result.abi_results[0].return_value
