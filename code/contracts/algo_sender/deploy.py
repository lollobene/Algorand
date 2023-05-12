from pyteal import *
import base64
from utils import get_algod_client
from from_mnemonic import get_alice_account, get_bob_account
from algo_sender import router
from algosdk import transaction, account

# helper function to compile program source
def compile_program(client, source_code):
  compile_response = client.compile(source_code)
  return base64.b64decode(compile_response['result'])

# create new application
def create_app(client, private_key, approval_program, clear_program, global_schema, local_schema):
  # define sender as creator
  sender = account.address_from_private_key(private_key)

  # declare on_complete as NoOp
  on_complete = transaction.OnComplete.NoOpOC

  # get node suggested parameters
  params = client.suggested_params()

  # create unsigned transaction
  txn = transaction.ApplicationCreateTxn(
    sender, 
    params, 
    transaction.OnComplete.NoOpOC, 
    approval_program, 
    clear_program,
    transaction.StateSchema(0, 0),
    transaction.StateSchema(0, 0))

  # sign transaction
  signed_txn = txn.sign(private_key)
  tx_id = signed_txn.transaction.get_txid()

  # send transaction
  client.send_transaction(signed_txn)

  # wait for confirmation
  try:
    transaction_response = transaction.wait_for_confirmation(client, tx_id, 4)
    print("TXID: ", tx_id)
    print("Result confirmed in round: {}".format(transaction_response['confirmed-round']))

  except Exception as err:
    print(err)
    return

  # display results
  transaction_response = client.pending_transaction_info(tx_id)
  app_id = transaction_response['application-index']
  print("Created new app-id:", app_id)

  return app_id

# helper function that formats global state for printing
def format_state(state):
  formatted = {}
  for item in state:
    key = item['key']
    value = item['value']
    formatted_key = base64.b64decode(key).decode('utf-8')
    if value['type'] == 1:
      # byte string
      if formatted_key == 'voted':
        formatted_value = base64.b64decode(value['bytes']).decode('utf-8')
      else:
        formatted_value = value['bytes']
      formatted[formatted_key] = formatted_value
    else:
      # integer
      formatted[formatted_key] = value['uint']
  return formatted

# helper function to read app global state
def read_global_state(client, app_id):
  app = client.application_info(app_id)
  global_state = app['params']['global-state'] if "global-state" in app['params'] else []
  return format_state(global_state)

def main() :
  # initialize an algodClient
  algod_client = get_algod_client()

  # define private keys
  creator_private_key = get_alice_account()['private_key']

  # declare application state storage (immutable)
  local_ints = 0
  local_bytes = 0
  global_ints = 0
  global_bytes = 0
  global_schema = transaction.StateSchema(global_ints, global_bytes)
  local_schema = transaction.StateSchema(local_ints, local_bytes)

  approval_program, clear_program, contract = router.compile_program(version=6)

  # compile program to TEAL assembly
  with open("./approval.teal", "w") as f:
    f.write(approval_program)

  # compile program to TEAL assembly
  with open("./clear.teal", "w") as f:
    f.write(clear_program)

  # compile program to binary
  approval_program_compiled = compile_program(algod_client, approval_program)

  # compile program to binary
  clear_state_program_compiled = compile_program(algod_client, clear_program)

  print("--------------------------------------------")
  print("Deploying application......")

  # create new application
  app_id = create_app(algod_client, creator_private_key, approval_program_compiled, clear_state_program_compiled, global_schema, local_schema)

  # read global state of application
  print("Global state:", read_global_state(algod_client, app_id))

if __name__ == "__main__":
  main()