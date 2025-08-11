from __future__ import annotations

from abc import ABC, abstractmethod


class PasswordHasherInterface(ABC):
    """Interface for password hashing utilities."""

    @abstractmethod
    def hash_password(self, plain: str) -> str:
        """Hash a plain-text password."""

    @abstractmethod
    def verify_password(self, plain: str, hashed: str) -> bool:
        """Verify a password against its hash."""
