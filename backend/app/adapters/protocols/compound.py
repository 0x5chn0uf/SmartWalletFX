"""Compound protocol adapter leveraging."""
from typing import Optional

from web3 import Web3

from app.schemas.defi import DeFiAccountSnapshot
from app.usecase.defi_compound_usecase import CompoundUsecase

from .base import ProtocolAdapter


class CompoundContractAdapter(ProtocolAdapter):
    """Adapter delegating to Compound snapshot usecase."""

    name = "compound"

    async def fetch_snapshot(self, address: str) -> Optional[DeFiAccountSnapshot]:
        w3 = Web3(Web3.HTTPProvider("https://ethereum-rpc.publicnode.com"))
        usecase = CompoundUsecase(w3)
        return await usecase.get_user_snapshot(address)
