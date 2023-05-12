from algosdk.atomic_transaction_composer import *
from algosdk import transaction, account
from utils import get_algod_client
from from_mnemonic import get_alice_account, get_bob_account
from algo_sender import router


# call application
def call_app(client, private_key, index, app_address, contract) :
  # get sender address
  sender = account.address_from_private_key(private_key)
  # create a Signer object 
  signer = AccountTransactionSigner(private_key)

  # get node suggested parameters
  sp = client.suggested_params()
  sp.flatFee = True
  sp.fee = 2*sp.min_fee


  # Create an instance of AtomicTransactionComposer
  atc = AtomicTransactionComposer()
  atc.add_transaction(
    TransactionWithSigner(transaction.PaymentTxn(sender, sp, app_address, 10**6), signer)
  )
  atc.add_method_call(
    app_id=index,
    method=contract.get_method_by_name("send_algo"),
    sender=sender,
    sp=sp,
    signer=signer,
    method_args=[get_bob_account()["address"], 10**6], # No method args needed here
  )

  # send transaction
  results = atc.execute(client, 2)

  # wait for confirmation
  print("TXID: ", results.tx_ids[0])
  print("Result confirmed in round: {}".format(results.confirmed_round))
  
def main():
  algod_client = get_algod_client()
  creator_private_key = get_alice_account()['private_key']
  app_id = 58
  app_address = "CSIKTDXTULOE5NTSS7YSH5FBVRVEU4YDRWNGSU2HM2KEO2W4KQTHKQJUOM"

  approval_program, clear_program, contract = router.compile_program(version=6)


  call_app(algod_client, creator_private_key, app_id, app_address, contract)

main()
