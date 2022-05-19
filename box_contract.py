from pyteal import *


router = Router()
router.add_bare_call(Approve(), OnComplete.NoOp, creation=True)
router.add_bare_call(Approve(), OnComplete.UpdateApplication)
router.add_bare_call(Approve(), OnComplete.DeleteApplication)
router.add_bare_call(Approve(), OnComplete.OptIn)
router.add_bare_call(Approve(), OnComplete.ClearState)
router.add_bare_call(Approve(), OnComplete.CloseOut)

@router.add_method_handler
@ABIReturnSubroutine
def bootstrap(key: abi.String, *, output: abi.String):
    return Seq(
        BoxCreate(key.get(), Int(1024)),
        BoxReplace(key.get(), Int(0), Bytes("abc123")),
        output.set(BoxExtract(key.get(), Int(0), Int(3))),
        BoxDelete(key.get())
    )

if __name__ == "__main__":
    import os
    import json

    path = os.path.dirname(os.path.abspath(__file__))

    approval, clear, spec = router.build_program()

    with open(os.path.join(path, "abi.json"), "w") as f:
        f.write(json.dumps(spec))

    with open(os.path.join(path, "approval.teal"), "w") as f:
        f.write(
            compileTeal(
                approval,
                mode=Mode.Application,
                version=7,
                assembleConstants=True,
                optimize=OptimizeOptions(scratch_slots=True),
            )
        )

    with open(os.path.join(path, "clear.teal"), "w") as f:
        f.write(
            compileTeal(
                clear,
                mode=Mode.Application,
                version=7,
                assembleConstants=True,
                optimize=OptimizeOptions(scratch_slots=True),
            )
        )
