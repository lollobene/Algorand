import base64

from algosdk import transaction, mnemonic, account
from algosdk.v2client import algod
from pyteal import *
from sandbox import Sandbox

sender_mnemonic = ""
sender_address = "LR5ICEO5QAA4KRJ5H4PYHZZXCFVNHUZ5OQDVW7PJFRSSW2QUBITW7LLBV4"
receiver_public_key = "UFAGBH5BHBAKDSSSBKP6LAZ7VFIA3ETNK7LVNEH6KXRRNTYE6WYHTEMEGU"
algod_address = "http://localhost:4001"
algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

def compile_smart_signature(client, source_code):
    compile_response = client.compile(source_code)
    return compile_response['result'], compile_response['hash']

def wait_for_confirmation(client, transaction_id, timeout):
    start_round = client.status()["last-round"] + 1
    current_round = start_round

    while current_round < start_round + timeout:
        try:
            pending_txn = client.pending_transaction_info(transaction_id)
        except Exception:
            return
        if pending_txn.get("confirmed-round", 0) > 0:
            return pending_txn
        elif pending_txn["pool-error"]:
            raise Exception('pool error: {}'.format(pending_txn["pool-error"]))
        client.status_after_block(current_round)
        current_round += 1
    raise Exception('pending tx not found in timeout rounds, timeout value = {}'.format(timeout))

def donation_escrow(benefactor):
    Fee = Int(1000)

    #Only the benefactor account can withdraw from this escrow
    program = And(
        Txn.type_enum() == TxnType.Payment,
        Txn.fee() <= Fee,
        Txn.receiver() == Addr(benefactor),
        Global.group_size() == Int(1),
        Txn.rekey_to() == Global.zero_address()
    )
    return compileTeal(program, Mode.Signature, version=5)

def payment_transaction(sender_address, amt, rcv, algod_client):
    params = algod_client.suggested_params()
    key = Sandbox.from_public_key(sender_address).private_key
    add = sender_address
    unsigned_txn = transaction.PaymentTxn(add, params, rcv, amt)
    signed = unsigned_txn.sign(key)
    txid = algod_client.send_transaction(signed)
    pmtx = wait_for_confirmation(algod_client, txid, 5)
    return pmtx

def lsig_payment_txn(escrowProg, escrow_address, amt, rcv, algod_client):
    params = algod_client.suggested_params()
    unsigned_txn = transaction.PaymentTxn(escrow_address, params, rcv, amt)
    encodedProg = escrowProg.encode()
    program = base64.decodebytes(encodedProg)
    lsig = transaction.LogicSig(program)
    stxn = transaction.LogicSigTransaction(unsigned_txn, lsig)
    tx_id = algod_client.send_transaction(stxn)
    try:
        pmtx = transaction.wait_for_confirmation(algod_client, tx_id, 10)
        print("TXID: ", tx_id)
        print("Result confirmed in round: {}".format(pmtx['confirmed-round']))
    except Exception as err:
        print(err)
        return
    # pmtx = wait_for_confirmation(algod_client, tx_id, 10)
    return pmtx

def main():
    algod_client = algod.AlgodClient(algod_token, algod_address)

    print("--------------------------------------------")
    print("Compiling Donation Smart Signature ...")
    stateless_program_teal = donation_escrow(receiver_public_key)
    escrow_result, escrow_address = compile_smart_signature(algod_client, stateless_program_teal)
    print("Program:", escrow_result)
    print("Contract Address:", escrow_address)

    print("--------------------------------------------")
    print("Sending Fund to Donation Smart Signature ...")
    amt = 2001000
    payment_transaction(sender_address, amt, escrow_address, algod_client)

    print("--------------------------------------------")
    print("Withdraw from Donation Smart Signature ...")
    withdrawal_amt = 800000
    lsig_payment_txn(escrow_result, escrow_address, withdrawal_amt, receiver_public_key, algod_client)

if __name__ == "__main__":
    main()