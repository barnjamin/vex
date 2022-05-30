from typing import List
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
        return Seq(*[g.set_default() for g in self.globals if not g.protected])

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
    protected: bool

    def __init__(self, key: str, stack_type: TealType, protected: bool = False):
        self.name = key
        self.key = Bytes(key)
        self.stack_type = stack_type
        self.protected = protected

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
        if self.protected:
            raise Exception("Can't set default on immutable global storage field")

        if self.stack_type == TealType.uint64:
            return App.globalPut(self.key, Int(0))
        else:
            return App.globalPut(self.key, Bytes(""))

    def set(self, val: Expr) -> Expr:
        if self.protected:
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

    def set(self, acct: Expr, val: Expr) -> Expr:
        return App.localPut(self.key, acct, val)

    def get(self, acct: abi.Account) -> Expr:
        return App.localGet(acct, self.key)

    def getElse(self, acct: abi.Address, val: Expr) -> Expr:
        return If(
            (v := App.localGetEx(Int(0), acct.encode(), self.key)).hasValue(),
            v.value(),
            val,
        )
