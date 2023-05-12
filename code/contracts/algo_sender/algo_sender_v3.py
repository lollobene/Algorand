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
  payment_cond = And(
    Gtxn[0].type_enum() == TxnType.Payment,
    Gtxn[0].amount() == amount.get(),
    Gtxn[0].receiver() == Global.current_application_address()
  )

  return Seq(
    Assert(payment_cond),
    InnerTxnBuilder.Execute(
      {
        TxnField.fee: Int(0),
        TxnField.type_enum: TxnType.Payment,
        TxnField.receiver: receiver.address(),
        TxnField.amount: amount.get(),
      }
    )
  )

@router.method
def send_asa(
    asa_id: Expr,
    asset_amount: Expr,
    asset_sender: Expr,
    asset_receiver: Expr,
) -> Expr:
  return InnerTxnBuilder.Execute(
    {
      TxnField.fee: Int(0),
      TxnField.type_enum: TxnType.AssetTransfer,
      TxnField.xfer_asset: asa_id,
      TxnField.asset_amount: asset_amount,
      TxnField.asset_sender: asset_sender,
      TxnField.asset_receiver: asset_receiver,
    }
  )

if __name__ == "__main__":
  # Compile the program
  approval_program, clear_program, contract = router.compile_program(version=6)

  # print out the results
  print(approval_program)
  print(clear_program)

  import json
  print(json.dumps(contract.dictify()))