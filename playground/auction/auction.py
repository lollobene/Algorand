from typing import Final
from beaker import *
from pyteal import *
#import os
#import json

MIN_FEE = Int(1000)                                         # minimum fee on Algorand is currently 1000 microAlgos



##############
# Application State
##############

# Declare Application state, marking `Final` here so the python class var doesn't get changed
# Marking a var `Final` does _not_ change anything at the AVM level

##############
# Global State
##############

class AuctionState:
    # Global Bytes (2)
    owner: Final[GlobalStateValue] = GlobalStateValue(
        stack_type = TealType.bytes,
        key = Bytes("o"),
        default = Global.creator_address(),
        descr = "The current owner of this contract, allowed to do admin type actions"
    )

    highest_bidder: Final[GlobalStateValue] = GlobalStateValue(
        stack_type = TealType.bytes,
        default = Bytes("")
    )

    # Global Ints (4)
    highest_bid: Final[GlobalStateValue] = GlobalStateValue(
        stack_type = TealType.uint64,
        default = Int(0)
    )

    nft_id: Final[GlobalStateValue] = GlobalStateValue(
        stack_type = TealType.uint64,
        default = Int(0)
    )

    auction_start: Final[GlobalStateValue] = GlobalStateValue(
        stack_type = TealType.uint64,
        default = Int(0)
    )

    auction_end: Final[GlobalStateValue] = GlobalStateValue(
        stack_type = TealType.uint64,
        default = Int(0)
    )

app = Application("Auction", descr="Auction App", state=AuctionState())
##############
# Administrative actions
##############

@app.external(authorize = Authorize.only(app.state.owner))
def set_owner(new_owner: abi.Account, *, output: abi.Byte) -> Expr:
    """sets the owner of the contract, may only be called by the current owner"""
    app.state.owner.set(new_owner.address())
    return output.set(app.state.owner.get())


##############
# Application Create
##############

@app.create
def create():
    return app.initialize_global_state()


##############
# Start auction
##############

@app.external(authorize = Authorize.only(app.state.owner))
def setup(payment: abi.PaymentTransaction, starting_price: abi.Uint64, nft: abi.Asset, start_offset: abi.Uint64, duration: abi.Uint64):
    payment = payment.get()
    Seq(
        # Set global state
        app.state.highest_bid.set(starting_price.get()),
        app.state.nft_id.set(nft.asset_id()),
        app.state.auction_start.set(Global.latest_timestamp() + start_offset.get()),
        app.state.auction_end.set(Global.latest_timestamp() + start_offset.get() + duration.get()),
        Assert(
            And(
                Global.latest_timestamp() < app.state.auction_start.get(),
                app.state.auction_start.get() < app.state.auction_end.get(),
                payment.type_enum() == TxnType.Payment,
                payment.sender() == Txn.sender(),
                payment.receiver() == Global.current_application_address(),
                #payment.close_remainder_to() == Global.zero_address(),                     <<<---
                #payment.rekey_to: Global.zero_address()                                    <<<---
            )
        ),
        do_opt_in(app.state.nft_id)
    )


##############
# Bidding
##############

@app.external
def bid(payment: abi.PaymentTransaction, previous_bidder: abi.Account):
    payment = payment.get()
    auction_end = app.state.auction_end.get()
    highest_bidder = app.state.highest_bidder.get()
    highest_bid = app.state.highest_bid.get()

    Seq(
        Assert(                                                                 # CHIAMARE PIU' ASSERT E' COSTOSO?  <<<---
            And(
                Global.latest_timestamp() < auction_end,
                payment.amount() > highest_bid,
                Txn.sender() == payment.sender()
            )
        ),
        # Return money to previous bidder
        If(highest_bidder != Bytes(""), Seq(Assert(highest_bidder == previous_bidder.address()), pay_bidder(highest_bidder, highest_bid))),
        # Set global state
        app.state.highest_bid.set(payment.amount()),
        app.state.highest_bidder.set(payment.sender())
    )


##############
# End auction
##############

@app.external
def end_auction(highest_bidder: abi.Account, nft: abi.Asset):             # nft: abi.Asset SERVE?     <<<---
    auction_end = app.state.auction_end.get()
    highest_bid = app.state.highest_bid.get()
    owner = app.state.owner.get()
    highest_bidder = app.state.highest_bidder.get()

    Seq(
        Assert(Global.latest_timestamp() > auction_end),
        do_aclose(highest_bidder, app.state.nft_id, Int(1)),
        pay_owner(owner, highest_bid)
    )


##############
# Smart Contract inner transactions
##############

# Refund previous bidder
@Subroutine(TealType.none)
def pay_bidder(receiver: Expr, amount: Expr):
    return Seq(
        InnerTxnBuilder.Begin(),                           
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.receiver: receiver,
                TxnField.amount: amount - Global.min_txn_fee(),
                TxnField.fee: Int(0),
#                    TxnField.fee: MIN_FEE,                                 #it seems to be a bit more expensive if set
#                    TxnField.close_remainder_to: Global.zero_address(),                    # SERVE?        <<<---
#                    TxnField.rekey_to: Global.zero_address()                               # SERVE?        <<<---
            }
        ),
        InnerTxnBuilder.Submit()
    )


# Send total amount of smart contract back to the owner and close the account
@Subroutine(TealType.none)
def pay_owner(receiver: Expr, amount: Expr):
    return Seq(
        InnerTxnBuilder.Begin(),                            #Inner transactions are only available in AVM version 5 or higher   <<<--- CHECK    (source: https://pyteal.readthedocs.io/en/stable/accessing_transaction_field.html)
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.receiver: receiver,
                TxnField.amount: amount,
                TxnField.fee: MIN_FEE,
#                    TxnField.fee: Int(0),
                TxnField.close_remainder_to: Global.creator_address(),
#                    TxnField.rekey_to: Global.zero_address()                               # SERVE?        <<<---
            }
        ),
        InnerTxnBuilder.Submit()
    )


# Asset opt-in for the smart contract
@Subroutine(TealType.none)
def do_opt_in(asset_id):
    return do_axfer(Global.current_application_address(), asset_id, Int(0))        


# Asset transfer to the smart contract
@Subroutine(TealType.none)
def do_axfer(receiver, asset_id, amount):
    return InnerTxnBuilder.Execute(
        {
            TxnField.type_enum: TxnType.AssetTransfer,
            TxnField.xfer_asset: asset_id,
            TxnField.asset_amount: amount,
            TxnField.asset_receiver: receiver,
            TxnField.fee: MIN_FEE
        }
    )


# Asset close out from the smart contract to the receiver
@Subroutine(TealType.none)
def do_aclose(receiver, asset_id, amount):
    return InnerTxnBuilder.Execute(
        {
            TxnField.type_enum: TxnType.AssetTransfer,
            TxnField.xfer_asset: asset_id,
            TxnField.asset_amount: amount,
            TxnField.asset_receiver: receiver,
            TxnField.fee: MIN_FEE,
            TxnField.asset_close_to: receiver
        }
    )


# Reject updates
#    @update(TealType.none)
#    def update_contract(self):
#        return Reject()




if __name__ == "__main__":
    app_spec = app.build()
    print(app_spec.global_state_schema.dictify())
#    Auction().dump("artifacts")

#    if os.path.exists("approval.teal"):
#        os.remove("approval.teal")

#    if os.path.exists("approval.teal"):
#        os.remove("clear.teal")

#    if os.path.exists("abi.json"):
#        os.remove("abi.json")

#    if os.path.exists("app_spec.json"):
#        os.remove("app_spec.json")

#    with open("approval.teal", "w") as f:
#        f.write(app.approval_program)

#    with open("clear.teal", "w") as f:
#        f.write(app.clear_program)

#    with open("abi.json", "w") as f:
#        f.write(json.dumps(app.contract.dictify(), indent=4))

#    with open("app_spec.json", "w") as f:
#        f.write(json.dumps(app.application_spec(), indent=4))
