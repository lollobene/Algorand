from typing import Final
from beaker import *
from pyteal import *
#import os
#import json

MIN_FEE: Final[int] = 1000

class AuctionState:
    # Global Bytes (2)
    owner = GlobalStateValue(
        stack_type = TealType.bytes,
        key = Bytes("o"),
        default = Global.creator_address(),
    )

    highest_bidder = GlobalStateValue(
        stack_type = TealType.bytes,
        default = Bytes("")
    )

    # Global Ints (4)
    highest_bid = GlobalStateValue(
        stack_type = TealType.uint64,
        default = Int(0)
    )

    nft_id = GlobalStateValue(
        stack_type = TealType.uint64,
        default = Int(0)
    )

    auction_start = GlobalStateValue(
        stack_type = TealType.uint64,
        default = Int(0)
    )

    auction_end = GlobalStateValue(
        stack_type = TealType.uint64,
        default = Int(0)
    )

app = (Application("Auction", descr="Auction App", state=AuctionState()))
       #.apply(unconditional_create_approval, initialize_global_state=True))


# @app.external()
# def set_owner(new_owner: abi.Account):
#     return app.state.owner.set(new_owner.address())

@app.create
def create() -> Expr:
    return app.initialize_global_state()

@app.external
def bid(bidPayment: abi.PaymentTransaction) -> Expr:

    return Seq(
        Assert(
            bidPayment.get().amount() > app.state.highest_bid.get(),
            bidPayment.get().receiver() == Global.current_application_address()
        ),
        
        # Return money to previous bidder
        If(bidPayment.get().amount() > Int(0), 
           Seq(
                pay_bidder(app.state.highest_bidder, app.state.highest_bid)
            )
        ),

        # Set global state
        app.state.highest_bid.set(bidPayment.get().amount()),
        app.state.highest_bidder.set(Txn.sender())
    )

@app.external
def bid2(bidPayment2: abi.PaymentTransaction, bidPayment3: abi.PaymentTransaction) -> Expr:

    return Seq(
        Assert(
            bidPayment2.get().amount() > app.state.highest_bid.get(),
            bidPayment2.get().receiver() == Global.current_application_address()
        ),
        
        # Return money to previous bidder
        If(bidPayment3.get().amount() > Int(0), 
           Seq(
                pay_bidder(app.state.highest_bidder, app.state.highest_bid)
            )
        ),

        # Set global state
        app.state.highest_bid.set(bidPayment3.get().amount()),
        app.state.highest_bidder.set(Txn.sender())
    )


@app.external
def double_val(value: abi.Uint64, *, output: abi.Uint64) -> Expr:
    return output.set(value.get()+value.get())

##############
# End auction
##############

# @app.external
# def end_auction(highest_bidder: abi.Account, nft: abi.Asset):
#     auction_end = app.state.auction_end.get()
#     highest_bid = app.state.highest_bid.get()
#     owner = app.state.owner.get()
#     highest_bidder = app.state.highest_bidder.get()

#     Seq(
#         Assert(Global.latest_timestamp() > auction_end),
#         do_aclose(highest_bidder, app.state.nft_id, Int(1)),
#         pay_owner(owner, highest_bid)
#     )


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
                TxnField.fee: Global.min_txn_fee(),                                 #it seems to be a bit more expensive if set
#                    TxnField.close_remainder_to: Global.zero_address(),                    # SERVE?        <<<---
#                    TxnField.rekey_to: Global.zero_address()                               # SERVE?        <<<---
            }
        ),
        InnerTxnBuilder.Submit()
    )

@Subroutine(TealType.none)
def place_bid(amount: Expr):
    return Seq(
        InnerTxnBuilder.Begin(),                           
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.sender: Txn.sender(),
                TxnField.receiver: Global.current_application_address(),
                TxnField.amount: amount - Global.min_txn_fee(),
                TxnField.fee: Int(0),
                TxnField.fee: Global.min_txn_fee(),                                 #it seems to be a bit more expensive if set
#                    TxnField.close_remainder_to: Global.zero_address(),                    # SERVE?        <<<---
#                    TxnField.rekey_to: Global.zero_address()                               # SERVE?        <<<---
            }
        ),
        InnerTxnBuilder.Submit()
    )


# Send total amount of smart contract back to the owner and close the account
# @Subroutine(TealType.none)
# def pay_owner(receiver: Expr, amount: Expr):
#     return Seq(
#         InnerTxnBuilder.Begin(),                            #Inner transactions are only available in AVM version 5 or higher   <<<--- CHECK    (source: https://pyteal.readthedocs.io/en/stable/accessing_transaction_field.html)
#         InnerTxnBuilder.SetFields(
#             {
#                 TxnField.type_enum: TxnType.Payment,
#                 TxnField.receiver: receiver,
#                 TxnField.amount: amount,
#                 TxnField.fee: MIN_FEE,
# #                    TxnField.fee: Int(0),
#                 TxnField.close_remainder_to: Global.creator_address(),
# #                    TxnField.rekey_to: Global.zero_address()                               # SERVE?        <<<---
#             }
#         ),
#         InnerTxnBuilder.Submit()
#     )


# # Asset opt-in for the smart contract
# @Subroutine(TealType.none)
# def do_opt_in(asset_id):
#     do_axfer(Global.current_application_address(), asset_id, Int(0))        


# # Asset transfer to the smart contract
# @Subroutine(TealType.none)
# def do_axfer(receiver, asset_id, amount):
#     InnerTxnBuilder.Execute(
#         {
#             TxnField.type_enum: TxnType.AssetTransfer,
#             TxnField.xfer_asset: asset_id,
#             TxnField.asset_amount: amount,
#             TxnField.asset_receiver: receiver,
#             TxnField.fee: MIN_FEE
#         }
#     )


# # Asset close out from the smart contract to the receiver
# @Subroutine(TealType.none)
# def do_aclose(receiver, asset_id, amount):
#     return InnerTxnBuilder.Execute(
#         {
#             TxnField.type_enum: TxnType.AssetTransfer,
#             TxnField.xfer_asset: asset_id,
#             TxnField.asset_amount: amount,
#             TxnField.asset_receiver: receiver,
#             TxnField.fee: MIN_FEE,
#             TxnField.asset_close_to: receiver
#         }
#     )


# Reject updates
#    @update(TealType.none)
#    def update_contract(self):
#        return Reject()




if __name__ == "__main__":
    app_spec = app.build()
    print(app_spec.approval_program)
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
