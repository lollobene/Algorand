import beaker
import pyteal as pt


class ExampleState:

    declared_global_value = beaker.GlobalStateValue(
        stack_type=pt.TealType.bytes,
        key="gs",
        default=pt.Bytes(""),
        descr="Bytes array",
    )

app = beaker.Application("StateExample", state=ExampleState())


@app.external
def set_global_state_val(v: pt.abi.String) -> pt.Expr:
    return app.state.declared_global_value.set(v.get())


@app.external(read_only=True)
def get_global_state_val(*, output: pt.abi.String) -> pt.Expr:
    return output.set(app.state.declared_global_value)
