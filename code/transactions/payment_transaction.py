import os
from dotenv import load_dotenv

from algosdk import transaction

from utils import get_algod_client, print_account_info, print_tx_information
from from_mnemonic import get_alice_account, get_bob_account

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
FROM_ADDRESS = os.getenv('ADDRESS')

alice = get_alice_account()
bob = get_bob_account()

def build_payment_tx(algod_client, from_address, receiver):
  params = algod_client.suggested_params()
  note = "Hello World".encode()
  amount = 1*10**6
  unsigned_txn = transaction.PaymentTxn(from_address, params, receiver, amount, None, note)
  return unsigned_txn

def sign_tx(unsigned_tx, secret_key):
  return unsigned_tx.sign(secret_key)

def send_tx(signed_tx, algod_client):
  txid = algod_client.send_transaction(signed_tx)
  try:
    confirmed_tx = transaction.wait_for_confirmation(algod_client, txid, 4)
    return confirmed_tx
  except Exception as err:
    print(err)
    return

def main():
  algod_client = get_algod_client()
  print_account_info(algod_client, FROM_ADDRESS)
  unsigned_tx = build_payment_tx(algod_client, alice['address'], bob['address'])
  signed_tx = sign_tx(unsigned_tx, alice['private_key'])
  confirmed_tx = send_tx(signed_tx, algod_client)
  print_tx_information(confirmed_tx)

main()
