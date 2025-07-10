"""API endpoints package."""

from importlib import import_module
from typing import List

__all__: List[str] = []

for _module in [
    "admin_db",
    "auth",
    "defi",
    "health",
    "jwks",
    "oauth",
    "password_reset",
    "email_verification",
    "users",
    "wallets",
]:
    module = import_module(f"{__name__}.{_module}")
    globals()[_module] = module
    __all__.append(_module)
