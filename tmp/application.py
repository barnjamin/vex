from typing import Dict, Union
from pyteal import *


class GlobalStorageValue:

    key: str
    t: abi.BaseType
    immutable: bool

    def __init__(self, key: str, t: abi.BaseType, immutable=False):
        self.key = Bytes(key)
        self.t = t
        self.immutable = immutable  # TODO make final

    def set_default(self) -> Expr:
        stack_type = self.t.type_spec().storage_type()
        if stack_type == TealType.uint64:
            return App.globalPut(self.key, Itob(Int(0)))
        else:
            return App.globalPut(self.key, Bytes(""))

    def set(self, val: abi.BaseType) -> Expr:
        if isinstance(abi.BaseType, val):
            return App.globalPut(self.key, val.encode())
        else:
            return App.globalPut(self.key, val.encode())

    def get(self) -> Expr:
        return App.globalGet(self.key)

    def getElse(self, val: Expr) -> Expr:
        return Seq(
            v := App.globalGetEx(Int(0), self.key), If(v.hasValue(), v.value(), val)
        )


class LocalStorageValue:
    def __init__(self, key: str, t: abi.BaseType):
        self.key = key
        self.t = t

    def set(self, acct: abi.Account, val: Union[abi.BaseType, Bytes]) -> Expr:
        if isinstance(abi.BaseType, val):
            return App.localPut(self.key, acct.encode(), val.encode())
        else:
            return App.localPut(self.key, acct.encode(), val.encode())

    def get(self, acct: abi.Account) -> Expr:
        return self.t.decode(App.localGet(self.key, acct.encode()))

    def getElse(self, acct: abi.Address, val: Expr) -> Expr:
        return self.t.decode(
            Seq(
                v := App.localGetEx(Int(0), acct.encode(), self.key),
                If(v.hasValue(), v.value(), val),
            )
        )


class AppState:
    Global: Dict[str, GlobalStorageValue]
    Local: Dict[str, LocalStorageValue]

    def init_globals(self):
        return Seq(*[v.set_default() for v in self.Global.values()])
