"""Aave protocol adapter implementation."""
from typing import Optional

from web3 import Web3

from app.schemas.defi import DeFiAccountSnapshot
from app.usecase.defi_aave_usecase import AaveUsecase

from .base import ProtocolAdapter


class AaveContractAdapter(ProtocolAdapter):
    """Adapter that delegates to :pyfunc:`AaveUsecase.get_user_snapshot`."""

    name = "aave"

    async def fetch_snapshot(self, address: str) -> Optional[DeFiAccountSnapshot]:
        w3 = Web3(Web3.HTTPProvider("https://ethereum-rpc.publicnode.com"))
        usecase = AaveUsecase(w3)
        return await usecase.get_user_snapshot(address)
