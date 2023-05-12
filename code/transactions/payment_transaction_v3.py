from algosdk.transaction import PaymentTxn, wait_for_confirmation
from utils import get_algod_client, print_account_info, print_tx_information
from from_mnemonic import get_alice_account, get_bob_account

alice = get_alice_account()
bob = get_bob_account()

algod_client = get_algod_client()
print_account_info(algod_client, alice['address'])

# Build transction
params = algod_client.suggested_params()

unsigned_tx = PaymentTxn(
  sender=alice['address'], 
  sp=params, 
  receiver=bob['address'], 
  amt=1*10**6, 
  note="Alice sends 1 ALGO to Bob".encode())

# Sign transaction
signed_tx = unsigned_tx.sign(alice['private_key'])

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


