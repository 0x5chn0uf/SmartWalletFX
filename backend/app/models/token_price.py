from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship

from app.core.database import Base


class TokenPrice(Base):
    __tablename__ = "token_prices"

    id = Column(Integer, primary_key=True, index=True)
    token_id = Column(Integer, ForeignKey("tokens.id"), index=True)
    price_usd = Column(Numeric(precision=18, scale=8))
    timestamp = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    token = relationship("Token", back_populates="historical_prices")

    class Config:
        orm_mode = True

    def __repr__(self):
        return f"""
            <TokenPrice token_id={self.token_id} timestamp={self.timestamp}>
        """
