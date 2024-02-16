from pyteal import *

def approval_program():
    on_creation = Seq(
        [
            Assert(Txn.application_args.length() == Int(4)),
            App.globalPut(Bytes("Player1"), (Txn.application_args[0])),
            App.globalPut(Bytes("Player2"), (Txn.application_args[1])),
            App.globalPut(Bytes("Oracle"), (Txn.application_args[2])),
            App.globalPut(Bytes("Deadline"), Btoi(Txn.application_args[3])),
            App.globalPut(Bytes("Stake"), Btoi(Txn.application_args[4])),
            App.globalPut(Bytes("Player1Bet"), Int(0)),
            App.globalPut(Bytes("Player2Bet"), Int(0)),
            Return(Int(1)),
        ]
    )

    is_player1 = Txn.sender() == App.globalGet(Bytes("Player1"))
    is_player2 = Txn.sender() == App.globalGet(Bytes("Player2"))
    is_oracle = Txn.sender() == App.globalGet(Bytes("Oracle"))

    player1_already_bet = App.globalGet(Bytes("Player1Bet")) != Int(0)
    player2_already_bet = App.globalGet(Bytes("Player2Bet")) != Int(0)

    on_join = Seq(
        [
            # Check if sender is player1 or player2
            Assert(
                Or(
                    is_player1,
                    is_player2,
                )
            ),
            # Check transaction parameters
            Assert(
                And(
                    Txn.group_index() == Int(0),
                    Gtxn[1].sender() == Txn.sender(),
                    Gtxn[1].type_enum() == TxnType.Payment,
                    Gtxn[1].amount() == App.globalGet(Bytes("Stake")),
                    Gtxn[1].receiver() == Global.current_application_address(),
                )
            ),
            # Check if player1 is already set
            If(
                is_player1, # if
                If( # then
                    player1_already_bet, # if
                    Return(Int(0)), # then
                    Seq([ # else
                        App.globalPut(Bytes("Player1Bet"), Int(1)),
                        Return(Int(1))
                    ])
                )         
            ),
            # Check if player2 is already set
            If(
                is_player2, # if
                If( # then
                    player2_already_bet, # if
                    Return(Int(0)), # then
                    Seq([ # else
                        App.globalPut(Bytes("Player2Bet"), Int(1)),
                        Return(Int(1))
                    ])
                )         
            ),
            Return(Int(0))
        ]
    )
    winner = Txn.application_args[1]
    on_winner = Seq(
        [
            # assert che il chiamante sia l'oracle
            Assert(is_oracle),
            # assert che il balance dello SC sia corretto
            Assert(
                And(
                    player1_already_bet,
                    player2_already_bet,
                )
            ),
            # assert che il winner sia player1 o player2
            Assert(
                Or(
                    winner == App.globalGet(Bytes("Player1")),
                    winner == App.globalGet(Bytes("Player2")),
                )
            ),
            # mandare i soldi al winner con una inner transaction
            Seq(
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields(
                    {
                        TxnField.type_enum: TxnType.Payment,
                        TxnField.amount: Mul(App.globalGet(Bytes("Stake")), Int(2)),
                        TxnField.receiver: winner,
                    }
                ),
                InnerTxnBuilder.Submit()
            ),
            Return(Int(1))
        ]
    )

    on_timeout = Seq(
        [
            # assert che la deadline sia passata
            Assert(Global.latest_timestamp() > App.globalGet(Bytes("Deadline"))),
            # assert che il balance dello SC sia corretto
            Assert(
                And(
                    player1_already_bet,
                    player2_already_bet,
                )
            ),
            # mandare i soldi al player1 con una inner transaction
            Seq(
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields(
                    {
                        TxnField.type_enum: TxnType.Payment,
                        TxnField.amount: App.globalGet(Bytes("Stake")),
                        TxnField.receiver: App.globalGet(Bytes("Player1")),
                    } 
                ),
                InnerTxnBuilder.Submit()
            ),
            # mandare i soldi al player2 con una inner transaction
            Seq(
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields(
                    {
                        TxnField.type_enum: TxnType.Payment,
                        TxnField.amount: App.globalGet(Bytes("Stake")),
                        TxnField.receiver: App.globalGet(Bytes("Player2")),
                    }
                ),
                InnerTxnBuilder.Submit()
            ),
            Return(Int(1))
        ]
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(Int(0))],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(Int(0))],
        [Txn.on_completion() == OnComplete.CloseOut, Return(Int(0))],
        [Txn.on_completion() == OnComplete.OptIn, Return(Int(0))],
        [Txn.application_args[0] == Bytes("join"), on_join],
        [Txn.application_args[0] == Bytes("winner"), on_winner],
        [Txn.application_args[0] == Bytes("timeout"), on_timeout],
    )

    return program


def clear_state_program():
    program = Return(Int(1))
    return program


if __name__ == "__main__":
    with open("oracle_bet_approval.teal", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=8)
        f.write(compiled)

    with open("oracle_bet__clear_state.teal", "w") as f:
        compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=8)
        f.write(compiled)
