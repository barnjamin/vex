from sre_parse import State
from typing import List, Union, Tuple
from pyteal import *
from algosdk.future.transaction import StateSchema


class Application:
    globals: List["GlobalStorageValue"]
    locals: List["LocalStorageValue"]
    router: Router

    def __init__(self):

        for gv in self.globals:
            setattr(self, gv.name, gv)

    def initialize_globals(self):
        return Seq(*[g.set_default() for g in self.globals if not g.immutable])

    def local_schema(self) -> StateSchema:
        return StateSchema(
            len([l for l in self.locals if l.stack_type == TealType.uint64]),
            len([l for l in self.locals if l.stack_type == TealType.bytes]),
        )

    def global_schema(self) -> StateSchema:
        return StateSchema(
            len([g for g in self.globals if g.stack_type == TealType.uint64]),
            len([g for g in self.globals if g.stack_type == TealType.bytes]),
        )


class GlobalStorageValue(Expr):
    name: str
    key: Bytes
    stack_type: TealType
    immutable: bool

    def __init__(self, key: str, stack_type: TealType, immutable: bool = False):
        self.name = key
        self.key = Bytes(key)
        self.stack_type = stack_type
        self.immutable = immutable

    def has_return(self) -> bool:
        return super().has_return()

    def type_of(self) -> TealType:
        return self.stack_type

    def __teal__(self, options: "CompileOptions"):
        return self.get().__teal__(options)

    def __str__(self) -> str:
        return f"GlobalStorage {self.name}"

    def __call__(self, val: Expr) -> Expr:
        return self.set(val)

    def set_default(self) -> Expr:
        if self.immutable:
            raise Exception("Can't set default on immutable global storage field")

        if self.stack_type == TealType.uint64:
            return App.globalPut(self.key, Int(0))
        else:
            return App.globalPut(self.key, Bytes(""))

    def set(self, val: Expr) -> Expr:
        if self.immutable:
            return Seq(
                v := App.globalGetEx(Int(0), self.key),
                Assert(Not(v.hasValue())),
                App.globalPut(self.key, val),
            )

        return App.globalPut(self.key, val)

    def get(self) -> Expr:
        return App.globalGet(self.key)

    def getElse(self, val: Expr) -> Expr:
        return If((v := App.globalGetEx(Int(0), self.key)).hasValue(), v.value(), val)


class LocalStorageValue:
    name: str
    key: Bytes
    stack_type: TealType

    def __init__(self, key: str, stack_type: TealType):
        self.name = key
        self.key = Bytes(key)
        self.stack_type = stack_type

    def set(self, acct: Expr, val: Union[abi.BaseType, Bytes]) -> Expr:
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