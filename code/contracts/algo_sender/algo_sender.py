from pyteal import *

# Main router class
router = Router(
  # Name of the contract
  "ALGO sender",
  # What to do for each on-complete type when no arguments are passed (bare call)
  BareCallActions(
    # On create only, just approve
    no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE),
    # Always let creator update/delete but only by the creator of this contract
    update_application=OnCompleteAction.never(),
    delete_application=OnCompleteAction.never(),
    # No local state, don't bother handling it. 
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

if __name__ == "__main__":
  # Compile the program
  approval_program, clear_program, contract = router.compile_program(version=6)

  # print out the results
  print(approval_program)
  print(clear_program)

  import json
  print(json.dumps(contract.dictify()))