from __future__ import annotations

"""Abstract base classes and types for DeFi protocol adapters.

Each concrete adapter should implement :class:`ProtocolAdapter` and wrap
whatever data-source (on-chain RPC, REST API, etc.) is
required to materialise a :class:`DeFiAccountSnapshot` for a user address.

Adapters **MUST NOT** perform any heavy post-processing – they should focus
on retrieving raw protocol-specific data and mapping it to the agnostic
schema defined in :pymod:`app.schemas.defi`.
"""

from abc import ABC, abstractmethod
from typing import Optional, Protocol, runtime_checkable

from app.schemas.defi import DeFiAccountSnapshot

__all__ = ["ProtocolAdapter"]


@runtime_checkable
class _AsyncCallable(Protocol):
    async def __call__(self, address: str) -> Optional[DeFiAccountSnapshot]:
        ...


class ProtocolAdapter(ABC):
    """Base class all protocol adapters must inherit from."""

    #: Unique protocol name identifier (e.g. "aave", "compound").
    name: str

    #: Human-readable protocol display name (optional, defaults to ``name``).
    display_name: str | None = None

    # ------------------------------------------------------------------
    # Primary API surface
    # ------------------------------------------------------------------
    @abstractmethod
    async def fetch_snapshot(self, address: str) -> Optional[DeFiAccountSnapshot]:
        """Return an aggregated snapshot for *address*.

        Concrete implementations are free to query multiple endpoints and do
        minimal mapping, but should avoid expensive computations. They should
        raise exceptions on fatal errors – the caller is expected to handle
        them and decide whether to fail fast or continue with partial data.
        """

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    async def __call__(self, address: str) -> Optional[DeFiAccountSnapshot]:
        """Allow adapter instances to be called like a function."""
        return await self.fetch_snapshot(address)

    # ------------------------------------------------------------------
    # Repr / str helpers for debugging
    # ------------------------------------------------------------------
    def __repr__(self) -> str:  # pragma: no cover
        return f"<{self.__class__.__name__} name={self.name!r}>"
