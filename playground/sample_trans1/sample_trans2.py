# Sample Hello World Beaker smart contract - the most basic starting point for an Algorand smart contract
import beaker
import pyteal as pt

app = beaker.Application("SampleTrans2")

@pt.Subroutine(pt.TealType.uint64)
def f(x: pt.Expr) -> pt.Expr:
    return pt.Minus(x, pt.Int(2))

@app.external
def entry() -> pt.Expr:
    res = pt.abi.make(pt.abi.Uint64)
    return res.set(f(pt.Int(98)))
