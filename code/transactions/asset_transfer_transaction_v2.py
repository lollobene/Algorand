from algosdk.transaction import AssetTransferTxn
from utils import get_algod_client
from from_mnemonic import get_alice_account, get_bob_account

ASSET_ID = "64"

alice = get_alice_account()
bob = get_bob_account()

algod_client = get_algod_client()

params = algod_client.suggested_params()

unsigned_tx = AssetTransferTxn(
  sender=bob['address'],
  sp=params,
  receiver=bob['address'],
  amt=0,
  index=ASSET_ID
)

signed_tx = unsigned_tx.sign(bob['private_key'])

tx_id = algod_client.send_transaction(signed_tx)

unsigned_tx = AssetTransferTxn(
  sender=alice['address'],
  sp=params,
  receiver=bob['address'],
  amt=10*10**6,
  index=ASSET_ID)

signed_tx = unsigned_tx.sign(alice['private_key'])
tx_id = algod_client.send_transaction(signed_tx)