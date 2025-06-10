import os

from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

ARBITRUM_RPC_URL = os.getenv("ARBITRUM_RPC_URL")

if not ARBITRUM_RPC_URL:
    print("Error: ARBITRUM_RPC_URL not set in environment.")
    exit(1)

w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC_URL))

try:
    block_number = w3.eth.block_number
    print(f"Connected to Arbitrum! Latest block: {block_number}")
except Exception as e:
    print(f"Failed to connect to Arbitrum RPC: {e}")
    exit(1)
