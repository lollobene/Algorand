from pyteal import *
from beaker import *
from typing import Final

class SimpleToken(Application):

  # Application states
  total_supply: Final[ApplicationStateValue] = ApplicationStateValue(
    stack_type=TealType.uint64,
    descr="Total supply",
  )

  reserve: Final[ApplicationStateValue] = ApplicationStateValue(
    stack_type=TealType.uint64,
    descr="Reserve",
  )

  paused: Final[ApplicationStateValue] = ApplicationStateValue(
    stack_type=TealType.uint64,
    descr="Paused",
  )

  # Account states
  contract_admin: Final[AccountStateValue] = AccountStateValue(
    stack_type=TealType.uint64,
    descr="Contract admin"
  )

  transfer_admin: Final[AccountStateValue] = AccountStateValue(
    stack_type=TealType.uint64,
    descr="Transfer admin"
  )

  balance: Final[AccountStateValue] = AccountStateValue(
    stack_type=TealType.uint64,
    descr="Balance"
  )

  frozen: Final[AccountStateValue] = AccountStateValue(
    stack_type=TealType.uint64,
    descr="Frozen"
  )

  @internal
  def is_contract_admin(self):
    return self.contract_admin[Txn.sender()].exists()
  
  @internal
  def is_transfer_admin(self):
    return self.transfer_admin[Txn.sender()].exists()

  @internal
  def is_any_admin(self):
    return Or(
      self.is_contract_admin(),
      self.is_transfer_admin()
    )

  @external
  def pause(self, new_pause_value: abi.Uint64):
    return Seq(
      Assert(self.is_any_admin()),
      self.paused.set(new_pause_value.get()),
    )
  
  @external
  def freeze(self, new_freeze_value: abi.Uint64):
    return Seq(
      Assert(
        And(
          Txn.application_args.length() == Int(2),
          Txn.accounts.length() == Int(1),
          self.is_any_admin()
        )
      ),
      self.frozen.set(new_freeze_value.get())
    )

  @external
  def set_admin(self, new_admin: abi.Uint64, new_admin_type: abi.String):
    return Seq(
      Assert(
        And(
          self.is_contract_admin(),
          Txn.application_args.length() == Int(3),
          Or(
            new_admin_type.get() == Bytes("contract admin"),
            new_admin_type.get() == Bytes("transfer admin"),
          ),
          Txn.accounts.length() == Int(1),
        )
      ),
      If(
        new_admin_type.get() == Bytes("contract admin"),
        self.contract_admin.set(new_admin.get()),
        self.contract_admin.set(new_admin.get())
      )
    )
  
  @external
  def mint(self, amount: abi.Uint64):
    return Seq(
      Assert(
        And(
          self.is_contract_admin(),
          Txn.application_args.length() == Int(2),
          Txn.accounts.length() == Int(1),
          amount.get() <= self.reserve.get()
        )
      ),
      self.reserve.set(self.reserve.get() - amount.get()),
      self.balance.set(self.balance.get() + amount.get()),
    )

  @external
  def transfer(self, amount: abi.Uint64, receiver):
    return

if __name__ == "__main__":
    import json

    token = SimpleToken()
    print(token.approval_program)
    print(token.clear_program)
    print(json.dumps(token.contract.dictify()))