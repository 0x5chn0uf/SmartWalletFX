import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text

from . import Base


class PortfolioSnapshotCache(Base):
    __tablename__ = "portfolio_snapshot_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_address = Column(String(64), index=True, nullable=False)
    from_ts = Column(BigInteger, nullable=False)
    to_ts = Column(BigInteger, nullable=False)
    interval = Column(String(16), nullable=False)
    limit = Column(Integer, nullable=False)
    offset = Column(Integer, nullable=False)
    response_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
