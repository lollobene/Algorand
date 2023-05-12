import os
from dotenv import load_dotenv
from algosdk import mnemonic, account
load_dotenv()

MNEMONIC_1=os.getenv("MNEMONIC_1")
MNEMONIC_2=os.getenv("MNEMONIC_2")

SECRET_KEY_1=mnemonic.to_private_key(MNEMONIC_1)
SECRET_KEY_2=mnemonic.to_private_key(MNEMONIC_2)

address_1 = account.address_from_private_key(SECRET_KEY_1)
address_2 = account.address_from_private_key(SECRET_KEY_2)

# print(SECRET_KEY_1)
# print(SECRET_KEY_2)

# print(address_1)
# print(address_2)

def get_alice_account():
  return {"private_key": SECRET_KEY_1, "address": address_1}

def get_bob_account():
  return {"private_key": SECRET_KEY_2, "address": address_2}

if __name__ == "__main__":
  print("Alice address: ", address_1)
  print("Bob address: ", address_2)