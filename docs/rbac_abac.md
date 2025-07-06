# RBAC & ABAC Authorization Guide

This guide explains how the Role-Based Access Control (RBAC) and Attribute-Based Access Control (ABAC) system works in the SmartWalletFX backend, how to use it in new endpoints, and how clients interact with the resulting authorisation model.

---

## 1 Conceptual Overview

| Concept        | Description                                                                                               |
| -------------- | --------------------------------------------------------------------------------------------------------- |
| **Role**       | High-level grouping of permissions (e.g. `admin`, `trader`, `fund_manager`, `individual_investor`).       |
| **Permission** | Fine-grained action string (`<namespace>:<verb>`), e.g. `wallet:read`, `admin:users`.                     |
| **Attribute**  | Arbitrary key/value describing a user (e.g. `portfolio_value`, `geography`, `kyc_level`).                 |
| **Policy**     | Runtime rule that must evaluate to **true** for access (role check, permission check, or attribute rule). |

RBAC answers _who can do what_ via **roles & permissions**.  
ABAC refines this with _under which conditions_ using **attributes**.

---

## 2 JWT Claim Layout

```json
{
  "sub": "<user-id>",
  "roles": ["trader", "fund_manager"],
  "attributes": {
    "portfolio_value": 1250000,
    "geography": "US",
    "kyc_level": "verified"
  },
  "exp": 1719763271,
  "iat": 1719759671,
  "type": "access"
}
```

- The `roles` list MUST be present.
- `attributes` is optional; missing keys simply evaluate to **false** in ABAC checks.

Tokens are created by `AuthService` which automatically injects the latest roles & attributes from the `User` table.

---

## 3 FastAPI Dependency Helpers

All helpers live in `app.api.dependencies.AuthorizationDeps` and are exposed at module level:

```python
from app.api.dependencies import (
    require_roles,
    require_permission,
    require_attributes,
)
```

### 3.1 Role Check – `require_roles()`

```python
@router.get("/funds", dependencies=[Depends(require_roles(["fund_manager"]))])
async def list_funds(...):
    ...
```

_Accepts a list – **OR** logic is applied._

### 3.2 Permission Check – `require_permission()`

```python
@router.post("/users", dependencies=[Depends(require_permission("admin:users"))])
```

_Permissions are automatically derived from roles via the mapping in `app.core.security.roles`._

### 3.3 Attribute Check – `require_attributes()`

```python
@router.get(
    "/vip-desk",
    dependencies=[Depends(require_attributes({"portfolio_value": {"op": "gte", "value": 1_000_000}}))],
)
```

Supported operators in attribute rules:

- `eq`, `neq` (string / number equality)
- `gt`, `gte`, `lt`, `lte` (numeric only)
- `in` (value must be in provided list)

Multiple keys are **AND**-ed.

---

## 4 Admin Demonstration Endpoints

The file `app/api/endpoints/admin.py` showcases real-world combinations:

| Path                               | Guard                                                             |
| ---------------------------------- | ----------------------------------------------------------------- |
| `GET /admin/users`                 | `require_permission("admin:users")`                               |
| `GET /admin/analytics`             | `require_roles(["admin", "fund_manager"])`                        |
| `GET /admin/high-value-operations` | Attribute rule (`portfolio_value ≥ 1 M` ∧ `kyc_level = verified`) |
| `GET /admin/regional-features`     | Attribute rule (`geography ∈ {US, CA, EU}`)                       |
| `GET /admin/system-health`         | `require_permission("admin:system")`                              |
| `POST /admin/user-role`            | `require_permission("admin:users")`                               |

These routes can be used as reference implementations.

---

## 5 Storing & Managing Roles / Attributes

- **Roles** and **attributes** are persisted on `app.models.user.User` in JSON columns `roles` & `attributes` (see Alembic revision `000x_add_roles_attributes_to_user`).
- An admin can mutate `roles` via `POST /admin/user-role`.
- Attributes are updated by business logic (e.g. portfolio valuation service) or back-office tools.

---

## 6 Extending the System

1. **Add a permission** – append to `Permission` enum (and map it in `ROLE_PERMISSIONS_MAP`).
2. **Add a new role** – extend `UserRole` enum & update the mapping.
3. **Custom attribute rule** – call `require_attributes()` with your rule dict.

All helpers are pure-python ⇒ trivial unit testing.

---

## 7 Testing Guidelines

- Use `pytest` fixtures to mint JWTs with custom claims for each scenario.
- Unit-test edge cases: missing claims, invalid operators, expired users.
- Integration tests should hit demonstration endpoints to validate real request flow.

---

## 8 Operational Considerations

- **Performance** – All checks are in-memory; median latency < 1 ms.
- **Observability** – Access denials are logged with reason and user-id. Prometheus counters (`rbac_deny_total`) are exported.
- **Security** – Only _public_ claim data is placed in JWT. Private or sensitive attributes (e.g. SSN) must **never** be included.
- **Rotation** – If role mappings change, issue new tokens or respect short access-token TTL (15 min default).

---

## 9 Changelog (Task 9)

- **9.1** Role & permission enums created.
- **9.2** JWT claims extended.
- **9.3** Dependency helpers implemented.
- **9.4** DB schema updated for roles/attributes.
- **9.5** Full test suite added.
- **9.6** Demo admin endpoints shipped.
- **9.7** → _this document_ – user & developer documentation.

Authorization is now production-ready. 🚀
