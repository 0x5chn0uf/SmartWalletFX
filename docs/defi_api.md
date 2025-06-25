# DeFi Tracker API Documentation

The DeFi Tracker API provides endpoints for retrieving real-time user data from multiple DeFi protocols (Aave, Compound, Radiant) and aggregated portfolio metrics. All endpoints use standard HTTP verbs and return JSON responses.

## Base Path

```
/api/v1
```

---

## Authentication

Most endpoints in this module are **public** (no authentication required) except:

* `GET /defi/aggregate/{address}` – Requires a valid JWT (`Authorization: Bearer <token>`)

Authentication follows the same JWT scheme defined in Task 4.

---

## Endpoints

### 1. Health Check

| Method | Path | Auth | Response |
|--------|------|------|----------|
| GET | `/defi/health` | None | `{ "status": "ok" }` |

Simple liveness probe.

---

### 2. Protocol-Specific Snapshot

Retrieve the latest on-chain snapshot for a wallet from a specific protocol.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/defi/aave/{address}` | Aave V2 positions (supply / borrow) |
| GET | `/defi/compound/{address}` | Compound V2 positions |
| GET | `/defi/radiant/{address}` | Radiant Capital positions (Arbitrum) |

**Path Params**

| Name | Type | Description |
|------|------|-------------|
| `address` | `string` | EVM wallet address (0x…40 hex) |

**Response 200** – `DeFiAccountSnapshot`

```jsonc
{
  "protocol": "aave",
  "collateral": [
    {
      "asset": "USDC",
      "amount": 1250.0,
      "usd_value": 1250.0,
      "apy": 0.0311
    }
  ],
  "borrows": [ ... ],
  "health_factor": 1.92
}
```

**Response 404** – `{"detail":"User data not found on …"}`

---

### 3. Aggregated Portfolio Metrics

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/defi/portfolio/{address}` | None | Aggregate metrics across all supported protocols |

Returns `PortfolioMetrics`:

```jsonc
{
  "tvl": 2410.23,
  "total_borrowings": 592.4,
  "aggregate_apy": 0.045,
  "positions": [ ... ]
}
```

---

### 4. Historical Timeline

| Method | Path | Description |
|--------|------|-------------|
| GET | `/defi/timeline/{address}?from_ts=…&to_ts=…` | Historical snapshots with optional aggregation interval |

Query Parameters:

* `from_ts` / `to_ts` – Unix timestamps (required)
* `limit`, `offset` – Pagination
* `interval` – `none` (default), `daily`, `weekly`
* `raw` – If `true`, return raw list instead of wrapper object

---

### 5. Secure Aggregate Metrics (with Redis cache)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/defi/aggregate/{address}` | **JWT** | Cached, persisted aggregate metrics |

This endpoint:

1. Checks Redis cache (TTL 5 minutes)
2. Falls back to database
3. Calculates fresh metrics if needed and stores them in cache & DB

---

### 6. Admin – Trigger Snapshot Collection

| Method | Path | Auth | Description |
|--------|------|-------------|
| POST | `/defi/admin/trigger-snapshot` | **JWT (Admin)** | Triggers background Celery task to persist snapshots |

---

## Error Codes

| Code | Meaning |
|------|---------|
| 422 | Invalid address format |
| 404 | Data not found |
| 500 | Internal server error |

---

## Rate Limiting

* Public endpoints are rate-limited to **60 requests/minute** per IP.
* Authenticated endpoints inherit user-level limits (see Task 4).

---

## Caching Strategy

* Per-wallet aggregate metrics are cached in Redis under `defi:aggregate:{wallet}` for **5 minutes**.
* Cache is automatically refreshed on new aggregation.

---

## Contact

For questions please open an issue or contact the backend team. 