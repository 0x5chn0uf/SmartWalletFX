from uuid import uuid4

from sqlalchemy import JSON, BigInteger, Column, Float, String
from sqlalchemy.dialects.postgresql import UUID

from . import Base


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_address = Column(String(64), index=True, nullable=False)
    timestamp = Column(BigInteger, index=True, nullable=False)
    total_collateral = Column(Float, nullable=False)
    total_borrowings = Column(Float, nullable=False)
    total_collateral_usd = Column(Float, nullable=False)
    total_borrowings_usd = Column(Float, nullable=False)
    aggregate_health_score = Column(Float, nullable=True)
    aggregate_apy = Column(Float, nullable=True)
    collaterals = Column(JSON, nullable=False)
    borrowings = Column(JSON, nullable=False)
    staked_positions = Column(JSON, nullable=False)
    health_scores = Column(JSON, nullable=False)
    protocol_breakdown = Column(JSON, nullable=False)
