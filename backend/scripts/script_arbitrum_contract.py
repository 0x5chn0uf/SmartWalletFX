import json
import os

from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

ARBITRUM_RPC_URL = os.getenv("ARBITRUM_RPC_URL")
if not ARBITRUM_RPC_URL:
    print("Error: ARBITRUM_RPC_URL not set in environment.")
    exit(1)

w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC_URL))

# Load ABI
ABI_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "abis", "UIDataProvider.json")
)
try:
    with open(ABI_PATH) as f:
        abi = json.load(f)
except Exception as e:
    print(f"Failed to load ABI: {e}")
    print(f"Tried path: {ABI_PATH}")
    exit(1)

# Contract addresses (use checksum format)
PROVIDER = w3.to_checksum_address(
    "0x454a8daf74b24037ee2fa073ce1be9277ed6160a"
)  # Pool Address Provider
USER_ADDRESS = w3.to_checksum_address(
    "0x48840F6D69c979Af278Bb8259e15408118709F3F"
)  # Your wallet

contract = w3.eth.contract(
    address=w3.to_checksum_address("0x56D4b07292343b149E0c60c7C41B7B1eEefdD733"),
    abi=abi,
)


try:
    result = contract.functions.getUserReservesData(PROVIDER, USER_ADDRESS).call()
    print("getUserReservesData result:")
    print(result)
except Exception as e:
    print(f"Failed to call getUserReservesData: {e}")
    exit(1)
