# Radiant v2 Arbitrum Contract Addresses

Source: [Radiant Capital Docs - Arbitrum Contracts](https://docs.radiant.capital/radiant/contracts-and-security/arbitrum-contracts)

## Core Contracts

- **PoolAddressProvider:** 0x454a8daf74b24037ee2fa073ce1be9277ed6160a
- **LendingPool:** 0xE23B4AE3624fB6f7cDEF29bC8EAD912f1Ede6886
- **PoolAddressesProviderRegistry:** 0x9D36DCe6c66E3c206526f5D7B3308fFF16c1aa5E
- **PoolHelper:** 0xfC05ec21b106E0c1e035Ec4718C1394f098FBb57

## Data Providers

- **UI Pool Data Provider:** 0x56D4b07292343b149E0c60c7C41B7B1eEefdD733
- **Wallet Balance Provider:** 0x6AC30E227468773AF2F70cD0F3A0375520885610
- **Eligibility Data Provider:** 0xd4966DC49a10aa5467D65f4fA4b1449b5d874399

## Tokenization

- **rWBTC:** 0xa366742D785C288EcAD8120D5303Db4EB675c9EC
- **rWETH:** 0xfB6f79Db694Ab6B7bf9Eb71b3e2702191A91dF56
- **rUSDC:** 0xb1D71c15D7c00A1b38C7ad182FA49889A70DB4be
- **vdWBTC:** 0x2cECa734Ae0A437314a73401Db89a2560584b17F
- **vdwETH:** 0x330243dcBd91AcDD99b73a7C73c8A46e47FE386c
- **vdUSDC:** 0x7bF39AF1Dd18D6dAfca6B931589eF850F9D0Be25

## Oracles

- **rizOracleRouter:** 0xacA72b23081f3786159edbca8e5FD2Ae71171C69

## Rewards & Misc

- **chefIncentivesController:** 0xebC85d44cefb1293707b11f707bd3CEc34B4D5fA
- **multiFeeDistribution:** 0xc2054A8C33bfce28De8aF4aF548C48915c455c13
- **wethGateway:** 0x8a8f65cabb82a857fa22289ad0a5785a5e7dbd22

## Method Mapping for User Data Extraction

| Data Needed     | Contract              | Method (ABI)                              | Notes                                                                           |
| --------------- | --------------------- | ----------------------------------------- | ------------------------------------------------------------------------------- |
| Supplied assets | UI Pool Data Provider | `getUserReservesData(poolProvider, user)` | First arg is Pool Address Provider, not LendingPool. Returns all user reserves. |
| Borrowed assets | UI Pool Data Provider | `getUserReservesData(poolProvider, user)` | Includes borrow data                                                            |
| Health factor   | UI Pool Data Provider | `getUserReservesData(poolProvider, user)` | Usually included in return struct                                               |
| APY (rates)     | UI Pool Data Provider | `getReservesData(poolProvider)`           | Returns rates for all assets                                                    |
| Token metadata  | ERC20                 | `symbol()`, `decimals()`                  | Use standard ERC20 ABI                                                          |

> **Note:**
>
> - The first argument to `getUserReservesData` is the Pool Address Provider (`0x454a8daf74b24037ee2fa073ce1be9277ed6160a`), not the LendingPool.
> - The result is a tuple: the first element is a list of reserve tuples (token address, supplied, borrowed, collateral, etc.), the second is the user's health factor or aggregate metric.

### ABI Reference

- **UI Pool Data Provider ABI:** [Etherscan ABI](https://arbiscan.io/address/0x56D4b07292343b149E0c60c7C41B7B1eEefdD733#code)
- **ERC20 ABI:** [OpenZeppelin ERC20 ABI](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/token/ERC20/ERC20.sol)

## Example: Using UI Pool Data Provider with web3.py

```python
from web3 import Web3
import json

# Load ABI
with open("backend/abis/UIDataProvider.json") as f:
    abi = json.load(f)

w3 = Web3(Web3.HTTPProvider("https://arb1.arbitrum.io/rpc"))
contract = w3.eth.contract(address="0x56D4b07292343b149E0c60c7C41B7B1eEefdD733", abi=abi)

# Correct usage: Pool Address Provider as first argument
pool_provider = w3.to_checksum_address("0x454a8daf74b24037ee2fa073ce1be9277ed6160a")
user_address = w3.to_checksum_address("0xYourUserAddress")
user_data = contract.functions.getUserReservesData(pool_provider, user_address).call()
print(user_data)
```

> The result is a tuple: ([reserves...], health_factor). Each reserve tuple contains token address, supplied, borrowed, collateral status, etc. Cross-reference the ABI for exact fields.

---

For the full and latest list, see the [official Radiant docs](https://docs.radiant.capital/radiant/contracts-and-security/arbitrum-contracts).

## How to Update Contract Addresses, ABIs, and Config

- **Contract Addresses:**
  - All Radiant contract addresses are defined in `backend/app/constants/radiant.py`.
  - To update an address, edit this file and redeploy/restart the backend.

- **ABI Files:**
  - ABI JSON files are stored in `backend/abis/` (e.g., `UIDataProvider.json`).
  - To update an ABI, download the latest from Etherscan or the official Radiant repo and replace the file.

- **Arbitrum RPC URL:**
  - The backend connects to Arbitrum via the `ARBITRUM_RPC_URL` environment variable.
  - Set this in your `.env` file for local development and in CI via `.github/workflows/ci-cd.yml`.
  - See `.env.example` for the required variable.

- **Adding New Contracts:**
  - If Radiant adds new contracts, update both the constants file and add the new ABI to `backend/abis/`.
  - Document the change in this file for future reference.

- **Reference:**
  - See `backend/app/adapters/radiant_contract_adapter.py` for how these are used in code.

- **Testing:**
  - Always run tests after updating addresses or ABIs to ensure compatibility.
