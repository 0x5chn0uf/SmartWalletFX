from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from app.utils.jwt_rotation import Key


class JWTKeyUtilsInterface(ABC):
    """Interface for JWT key utilities."""

    @abstractmethod
    def get_verifying_keys(self) -> list[Key]:
        """Return all keys that are currently valid for verifying signatures."""

    @abstractmethod
    def get_signing_key(self) -> tuple[str, str]:
        """Get the active signing key and algorithm."""

    @abstractmethod
    def format_public_key_to_jwk(
        self, public_key_pem: str | bytes, kid: str, *, alg: str = "RS256"
    ) -> Dict[str, Any]:
        """Convert an RSA public key to a JWK dictionary conforming to RFC-7517."""
