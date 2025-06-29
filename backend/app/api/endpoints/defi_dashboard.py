from datetime import datetime
from typing import List

from fastapi import APIRouter

from app.schemas.defi_dashboard import DefiKPI, ProtocolBreakdown

router = APIRouter()

# NOTE: This is a simplified placeholder implementation. Replace with real
# aggregation logic once portfolio metrics aggregation is in place.

MOCK_PROTOCOLS: List[ProtocolBreakdown] = [
    ProtocolBreakdown(name="Aave", tvl=534221.12, apy=6.2, positions=12),
    ProtocolBreakdown(name="Compound", tvl=312876.44, apy=5.1, positions=8),
    ProtocolBreakdown(name="Radiant", tvl=407224.89, apy=14.2, positions=5),
]


@router.get("/defi/portfolio/kpi", response_model=DefiKPI, tags=["DeFi"])
async def get_defi_kpi():
    """Return basic KPI metrics for the DeFi dashboard (mock placeholder)."""
    total_tvl = sum(p.tvl for p in MOCK_PROTOCOLS)
    # Simple average APY weighted equally (placeholder)
    avg_apy = round(sum(p.apy for p in MOCK_PROTOCOLS) / len(MOCK_PROTOCOLS), 2)
    return DefiKPI(
        tvl=total_tvl,
        apy=avg_apy,
        protocols=MOCK_PROTOCOLS,
        updated_at=datetime.utcnow(),
    )


@router.get(
    "/defi/portfolio/protocols", response_model=List[ProtocolBreakdown], tags=["DeFi"]
)
async def get_protocol_breakdown():
    """Return protocol-level breakdown for dashboard table (mock placeholder)."""
    return MOCK_PROTOCOLS
