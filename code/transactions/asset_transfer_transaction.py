import json
from algosdk.v2client import algod
from algosdk.transaction import AssetConfigTxn, AssetTransferTxn, AssetFreezeTxn, wait_for_confirmation
import os
from dotenv import load_dotenv
from utils import get_algod_client, print_tx_information, print_asset_holding
from from_mnemonic import get_alice_account, get_bob_account

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
FROM_ADDRESS = os.getenv('ADDRESS')

# Asset ID configuration
ASSET_ID = "58"

alice = get_alice_account()
bob = get_bob_account()

algod_client = get_algod_client()

params = algod_client.suggested_params()

# receiver = "HZ57J3K46JIJXILONBBZOHX6BKPXEM2VVXNRFSUED6DKFD5ZD24PMJ3MVA"
receiver = bob['address']

print(receiver)
# OPT-IN
account_info = algod_client.account_info(receiver)
holding = None
idx = 0
for my_account_info in account_info['assets']:
    scrutinized_asset = account_info['assets'][idx]
    idx = idx + 1    
    if (scrutinized_asset['asset-id'] == ASSET_ID):
        holding = True
        break
if not holding:
    # Use the AssetTransferTxn class to transfer assets and opt-in
    print("Opting in for Asset")
    unsigned_tx = AssetTransferTxn(
        sender=receiver,
        sp=params,
        receiver=receiver,
        amt=0,
        index=ASSET_ID)
    signed_tx = unsigned_tx.sign(bob['private_key'])
    # Send the transaction to the network and retrieve the txid.
    try:
        tx_id = algod_client.send_transaction(signed_tx)
        print("Signed transaction with txID: {}".format(tx_id))
        # Wait for the transaction to be confirmed
        confirmed_txn = wait_for_confirmation(algod_client, tx_id, 4) 
        print("TX id: ", tx_id)
        print("Result confirmed in round: {}".format(confirmed_txn['confirmed-round']))    
    except Exception as err:
        print(err)
    # Now check the asset holding for that account.
    # This should now show a holding with a balance of 0.
    print_asset_holding(algod_client, receiver, ASSET_ID)

unsigned_tx = AssetTransferTxn(
  sender=alice['address'],
  sp=params,
  receiver=receiver,
  amt=10*10**6,
  index=ASSET_ID)

# Sign with secret key of owner
signed_tx = unsigned_tx.sign(alice['private_key'])

try:
  # Send the transaction to the network and retrieve the txid.
  print("Sending asset to Bob")
  tx_id = algod_client.send_transaction(signed_tx)
  print("Signed transaction with tx ID: {}".format(tx_id))
  # Wait for the transaction to be confirmed
  confirmed_tx = wait_for_confirmation(algod_client, tx_id, 4) 
  print("Tx ID: {}".format(tx_id))
  print("Result confirmed in round: {}".format(confirmed_tx['confirmed-round']))

except Exception as err:
  print(err)

# The balance should now be 10.
print_asset_holding(algod_client, receiver, ASSET_ID)