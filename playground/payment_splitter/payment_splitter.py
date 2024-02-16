import beaker
import pyteal as pt

class PaymentSplitterState:

    total_shares = beaker.GlobalStateValue(
        stack_type=pt.TealType.uint64,
        default=pt.Int(0),
    )

    total_released = beaker.GlobalStateValue(
        stack_type=pt.TealType.uint64,
        default=pt.Int(0),
    )
    
    payee_shares = beaker.LocalStateValue(
        stack_type=pt.TealType.uint64,
        default=pt.Int(0),
    )

    payee_released = beaker.LocalStateValue(
        stack_type=pt.TealType.uint64,
        default=pt.Int(0),
    )

    payees = beaker.ReservedGlobalStateValue(
        stack_type=pt.TealType.bytes,
        max_keys=32
    )

    payees_extension = beaker.ReservedGlobalStateValue(
        stack_type=pt.TealType.bytes,
        max_keys=32
    )

app = beaker.Application("PaymentSplitter", state=PaymentSplitterState())

@app.create
def create(keys: pt.abi.StaticArray, values: pt.abi.StaticArray) -> pt.Expr:
    # TODO write it better
    i = ScratchVar(TealType.uint64)
    actual_sum = ScratchVar(TealType.uint64)
    tmp_value = abi.Uint64()
    return Seq(
        For(i.store(Int(0)), i.load() < array.length(), i.store(i.load() + Int(1))).Do(
            If(i.load() <= Int(5))
            # Both branches of this If statement are equivalent
            .Then(
                # This branch showcases how to use `store_into`
                Seq(
                    array[i.load()].store_into(tmp_value),
                    actual_sum.store(actual_sum.load() + tmp_value.get()),
                )
            ).Else(
                # This branch showcases how to use `use`
                array[i.load()].use(
                    lambda value: actual_sum.store(actual_sum.load() + value.get())
                )
            )
        ),
        Assert(actual_sum.load() == expected_sum),
    )





