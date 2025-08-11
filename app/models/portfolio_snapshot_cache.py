from datetime import datetime
from uuid import uuid4

from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from . import Base


class PortfolioSnapshotCache(Base):
    __tablename__ = "portfolio_snapshot_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_address = Column(String(64), index=True, nullable=False)
    from_ts = Column(BigInteger, nullable=False)
    to_ts = Column(BigInteger, nullable=False)
    interval = Column(String(16), nullable=False)
    limit = Column(Integer, nullable=False)
    offset = Column(Integer, nullable=False)
    response_json = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
