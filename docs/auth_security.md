# Authentication Security Guidelines

## Password Hashing Strategy

We employ **bcrypt** via Passlib for password hashing. A centralised `PasswordHasher` utility wraps `passlib.context.CryptContext` to provide a simple, consistent API for hashing and verifying passwords across the entire backend.

### Configuration
| Setting | Default | Description |
|---------|---------|-------------|
| `BCRYPT_ROUNDS` | **12** | Cost factor for bcrypt. Increase for higher security, decrease in CI to speed up tests (minimum `4`). |

`BCRYPT_ROUNDS` is loaded from environment variables (via `app.core.config.Settings`) and validated by `SecurityValidator.bcrypt_rounds` to ensure values remain above the minimum safety threshold.

**Example `.env` snippet:**
```env
# Production – strong security
BCRYPT_ROUNDS=12

# CI (fast tests)
# export BCRYPT_ROUNDS=4
```

### Usage
```python
from app.utils.security import PasswordHasher

hashed = PasswordHasher.hash_password("StrongPass1!")
assert PasswordHasher.verify_password("StrongPass1!", hashed)
```

Legacy helpers `get_password_hash` / `verify_password` delegate to `PasswordHasher` for backward compatibility.

### Updating Cost Factor
1. Increase `BCRYPT_ROUNDS` in the environment for production.
2. Existing hashes remain valid; newly created or updated passwords will be hashed with the stronger factor.
3. Optionally detect `PasswordHasher.needs_update()` during login and re-hash old passwords transparently.

---

## Password Strength Validation
Passwords must satisfy the following regex (see `app.utils.security._PASSWORD_REGEX`):
* Minimum 8 characters
* At least one digit `0-9`
* At least one symbol `!@#$%^&*()_+=-`

Failure to meet these requirements results in `422 Unprocessable Entity` on registration.

---

## Testing Considerations
Property tests involving bcrypt can be slow. To maintain robust coverage without long runtimes:
* Set `BCRYPT_ROUNDS=4` in test environments.
* Limit Hypothesis `max_examples` and increase `deadline` (~500 ms).

See `backend/tests/unit/auth/test_password_hasher.py` for an example configuration.

---

## Future Enhancements
* **Argon2 Support:** Passlib makes swapping algorithms trivial; an internal enum in `PasswordHasher` could toggle between schemes.
* **Pepper Support:** Introduce application-level secret pepper for additional security.
* **Automatic Hash Upgrade:** Detect `PasswordHasher.needs_update()` and re-hash on successful login to transparently move users to stronger hashes.
* **Rate Limiting:** Combine with authentication middleware to block brute-force attempts.

---

_Updated: 2025-06-17_ 