from algosdk.atomic_transaction_composer import *
from algosdk import transaction, account, util
from utils import get_algod_client
from from_mnemonic import get_alice_account, get_bob_account
from algo_sender import router

alice = get_alice_account()
bob = get_bob_account()
client = get_algod_client()
app_id = 83
app_address = "XEIW2POEHSRMYIJUDVSO223HMM6WXE7HM4EVD7DAAJDRUR3FSJVVKKKDAA"
_, _, contract = router.compile_program(version=6)

sender = account.address_from_private_key(alice['private_key'])

alice_signer = AccountTransactionSigner(alice['private_key'])

params = client.suggested_params()
params.flatFee = True
params.fee = 2*params.min_fee

atc = AtomicTransactionComposer()
atc.add_transaction(
  TransactionWithSigner(
    transaction.PaymentTxn(alice['address'], params, app_address, util.algos_to_microalgos(1)), alice_signer)
)
atc.add_method_call(
  app_id=app_id,
  method=contract.get_method_by_name("send_algo"),
  sender=alice['address'],
  sp=params,
  signer=alice_signer,
  method_args=[bob["address"], util.algos_to_microalgos(1)],
)

results = atc.execute(client, 2)