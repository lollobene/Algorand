import json
import base64
from algosdk.v2client import algod

def get_algod_client():
  algod_address = "http://localhost:4001"
  algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  algod_client = algod.AlgodClient(algod_token, algod_address)
  return algod_client

def print_account_info(algod_client, address):
  account_info = algod_client.account_info(address)
  print("Account balance: {} microAlgos".format(account_info.get('amount')))

def print_tx_information(confirmed_tx):
  print("Transaction information: {}".format(json.dumps(confirmed_tx, indent=4)))
  if "note" in confirmed_tx["txn"]["txn"]:
    print("Decoded note: {}".format(base64.b64decode(
      confirmed_tx["txn"]["txn"]["note"]).decode()))

#   Utility function used to print asset holding for account and assetid
def print_asset_holding(algod_client, address, assetid):
    # note: if you have an indexer instance available it is easier to just use this
    # response = myindexer.accounts(asset_id = assetid)
    # then loop thru the accounts returned and match the address you are looking for
    account_info = algod_client.account_info(address)
    idx = 0
    for my_account_info in account_info['assets']:
        scrutinized_asset = account_info['assets'][idx]
        idx = idx + 1        
        if (scrutinized_asset['asset-id'] == assetid):
            print("Asset ID: {}".format(scrutinized_asset['asset-id']))
            print(json.dumps(scrutinized_asset, indent=4))
            break
