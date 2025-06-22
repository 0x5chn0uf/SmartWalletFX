# Wallet & Portfolio API

This document provides a comprehensive overview of the wallet and portfolio analysis endpoints available in the Wallet Tracker API. All endpoints require authentication via JWT Bearer token.

## Wallet Management

### Create Wallet

- **Endpoint**: `POST /wallets`
- **Description**: Creates a new wallet associated with the authenticated user.
- **Request Body**:
  ```json
  {
    "address": "string (valid EVM address)",
    "name": "string (optional)"
  }
  ```
- **Response**: `201 Created`
  ```json
  {
    "id": "uuid",
    "user_id": "uuid",
    "address": "string",
    "name": "string",
    "created_at": "datetime",
    "updated_at": "datetime",
    "is_active": "boolean",
    "balance_usd": "float"
  }
  ```

### List Wallets

- **Endpoint**: `GET /wallets`
- **Description**: Retrieves a list of all wallets owned by the authenticated user.
- **Response**: `200 OK` (Array of WalletResponse objects)

### Delete Wallet

- **Endpoint**: `DELETE /wallets/{address}`
- **Description**: Deletes a wallet by its address. The user must be the owner of the wallet.
- **Response**: `204 No Content`

---

## Portfolio Analysis

### Get Portfolio Metrics

- **Endpoint**: `GET /wallets/{address}/portfolio/metrics`
- **Description**: Retrieves aggregated real-time portfolio metrics for a specific wallet, including token breakdown, health scores, and APY.
- **Response**: `200 OK` (PortfolioMetrics object)
  ```json
  {
    "user_address": "string",
    "total_collateral_usd": "float",
    "total_borrowings_usd": "float",
    "aggregate_health_score": "float | null",
    "aggregate_apy": "float | null",
    "collaterals": "[Collateral]",
    "borrowings": "[Borrowing]",
    "staked_positions": "[StakedPosition]",
    "health_scores": "[HealthScore]",
    "protocol_breakdown": "{...}",
    "timestamp": "datetime"
  }
  ```

### Get Portfolio Timeline

- **Endpoint**: `GET /wallets/{address}/portfolio/timeline`
- **Description**: Retrieves historical portfolio data for trend analysis and visualization.
- **Query Parameters**:
  - `interval` (string, optional, default: "daily"): The time interval for aggregation.
  - `limit` (integer, optional, default: 30): The number of data points to return.
  - `offset` (integer, optional, default: 0): The number of data points to skip.
- **Response**: `200 OK`
  ```json
  {
    "timestamps": "[integer (unix timestamp)]",
    "collateral_usd": "[float]",
    "borrowings_usd": "[float]"
  }
  ``` 