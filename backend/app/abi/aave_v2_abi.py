AAVE_LENDING_POOL_V2_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
        "name": "getUserAccountData",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "totalCollateralETH",
                "type": "uint256",
            },
            {
                "internalType": "uint256",
                "name": "totalDebtETH",
                "type": "uint256",
            },
            {
                "internalType": "uint256",
                "name": "availableBorrowsETH",
                "type": "uint256",
            },
            {
                "internalType": "uint256",
                "name": "currentLiquidationThreshold",
                "type": "uint256",
            },
            {
                "internalType": "uint256",
                "name": "ltv",
                "type": "uint256",
            },
            {
                "internalType": "uint256",
                "name": "healthFactor",
                "type": "uint256",
            },
        ],
        "stateMutability": "view",
        "type": "function",
    }
]


AAVE_POOL_ADDRESS_PROVIDER_ABI = [
    {
        "inputs": [],
        "name": "getPool",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
]
