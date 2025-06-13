"""Aave protocol adapter implementation using The Graph subgraph."""
from typing import Optional

from app.schemas.defi import DeFiAccountSnapshot
from app.usecase.defi_aave_usecase import AaveUsecase
from web3 import Web3

from .base import ProtocolAdapter


class AaveContractAdapter(ProtocolAdapter):
    """Adapter that delegates to :pyfunc:`AaveUsecase.get_user_snapshot`."""

    name = "aave"
    display_name = "Aave"

    async def fetch_snapshot(self, address: str) -> Optional[DeFiAccountSnapshot]:
        w3 = Web3(Web3.HTTPProvider('https://ethereum-rpc.publicnode.com'))
        usecase = AaveUsecase(w3)
        return await usecase.get_user_snapshot(address)