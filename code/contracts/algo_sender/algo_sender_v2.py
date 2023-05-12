from pyteal import *

router = Router(
  "ALGO sender",
  BareCallActions(
    no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE),
    update_application=OnCompleteAction.never(),
    delete_application=OnCompleteAction.never(),
    close_out=OnCompleteAction.never(),
    opt_in=OnCompleteAction.never(),
    clear_state=OnCompleteAction.never(),
  ),
)

@router.method
def send_algo(receiver: abi.Account, amount: abi.Uint64) -> Expr:
  return InnerTxnBuilder.Execute(
    {
      TxnField.fee: Int(0),
      TxnField.type_enum: TxnType.Payment,
      TxnField.receiver: receiver.address(),
      TxnField.amount: amount.get(),
    }
  )
