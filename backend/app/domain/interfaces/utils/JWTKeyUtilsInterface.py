from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict

from app.domain.schemas.jwks import JWK


class JWTKeyUtilsInterface(ABC):
    """Interface for JWT key utilities."""

    @abstractmethod
    def get_verifying_keys(self) -> Dict[str, JWK]:
        """Return a mapping of kid to verifying keys."""

    @abstractmethod
    def get_signing_key(self) -> JWK:
        """Return the active signing key."""
