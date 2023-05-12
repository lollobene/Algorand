from pyteal import *
@Subroutine(TealType.none)
def app_create():
  return Seq(
    App.globalPut(Bytes("asset_id"), Btoi(Txn.application_args[0])),
    Approve()
  )

router = Router(
  "Simple dex",
  BareCallActions(
    no_op=OnCompleteAction.create_only(app_create()),
    update_application=OnCompleteAction.never(),
    delete_application=OnCompleteAction.never(),
    close_out=OnCompleteAction.never(),
    opt_in=OnCompleteAction.never(),
    clear_state=OnCompleteAction.never(),
  ),
)

@Subroutine(TealType.none)
def asset_transfer_inner_txn(
    asset_id: Expr,
    asset_amount: Expr,
    asset_sender: Expr,
    asset_receiver: Expr,
) -> Expr:

  return InnerTxnBuilder.Execute(
    {
      TxnField.fee: Int(0),
      TxnField.type_enum: TxnType.AssetTransfer,
      TxnField.xfer_asset: asset_id,
      TxnField.asset_amount: asset_amount,
      TxnField.asset_sender: asset_sender,
      TxnField.asset_receiver: asset_receiver,
    }
  )

@router.method
def buy():
  # TODO checks
  algos = Gtxn[0].amount()
  return asset_transfer_inner_txn(Int(1), algos, Global.current_application_address(), Txn.sender())

@router.method
def sell():
  return

if __name__ == "__main__":
  # Compile the program
  approval_program, clear_program, contract = router.compile_program(version=6)

  # print out the results
  print(approval_program)
  print(clear_program)

  import json
  print(json.dumps(contract.dictify()))