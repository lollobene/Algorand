import os
from dotenv import load_dotenv
from algosdk.transaction import PaymentTxn, wait_for_confirmation
from utils import get_algod_client, print_account_info, print_tx_information

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
FROM_ADDRESS = os.getenv('ADDRESS')

algod_client = get_algod_client()
print_account_info(algod_client, FROM_ADDRESS)

# Build transction
params = algod_client.suggested_params()

unsigned_tx = PaymentTxn(
  sender=FROM_ADDRESS, 
  sp=params, 
  receiver="HZ57J3K46JIJXILONBBZOHX6BKPXEM2VVXNRFSUED6DKFD5ZD24PMJ3MVA", 
  amt=1000000, 
  note="Alice sends 1 ALGO to Bob".encode())

# Sign transaction
signed_tx = unsigned_tx.sign(SECRET_KEY)

try:
  # Send transaction
  tx_id = algod_client.send_transaction(signed_tx)
  print("Signed transaction with txID: {}".format(tx_id))
  # Wait for the transaction to be confirmed
  confirmed_tx = wait_for_confirmation(algod_client, tx_id, 4)
  print("Tx ID: {}".format(tx_id))
  print("Result confirmed in round: {}".format(confirmed_tx['confirmed-round']))

except Exception as err:
  print(err)

print_tx_information(confirmed_tx)


