from algosdk.transaction import AssetConfigTxn, wait_for_confirmation
from utils import get_algod_client, print_tx_information
from from_mnemonic import get_alice_account, get_bob_account
from algosdk.util import algos_to_microalgos

alice = get_alice_account()
bob = get_bob_account()

algod_client = get_algod_client()

params = algod_client.suggested_params()

unsigned_tx = AssetConfigTxn(
  sender=alice['address'],
  sp=params,
  total=algos_to_microalgos(10**6), # 1 million on Tokens
  default_frozen=False,
  unit_name="CFC",
  asset_name="Ca' Foscari Coin",
  manager=alice['address'],
  reserve=alice['address'],
  freeze=alice['address'],
  clawback=alice['address'],
  decimals=6
)

# Sign with secret key of creator
signed_tx = unsigned_tx.sign(alice['private_key'])

try:
  # Send the transaction to the network and retrieve the txid.
  tx_id = algod_client.send_transaction(signed_tx)
  print("Signed transaction with tx ID: {}".format(tx_id))
  # Wait for the transaction to be confirmed
  confirmed_tx = wait_for_confirmation(algod_client, tx_id, 4)
  print("Tx ID: {}".format(tx_id))
  print("Result confirmed in round: {}".format(confirmed_tx['confirmed-round']))
   
except Exception as err:
  print(err)

print_tx_information(confirmed_tx)