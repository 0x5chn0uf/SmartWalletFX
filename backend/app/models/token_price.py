from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class TokenPrice(Base):
    """
    SQLAlchemy model for a token price record.
    Represents the price of a token at a specific timestamp.
    """

    __tablename__ = "token_prices"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    token_id = Column(UUID(as_uuid=True), ForeignKey("tokens.id"), index=True)
    price_usd = Column(Numeric(precision=18, scale=8))
    timestamp = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    token = relationship("Token", back_populates="historical_prices")

    class Config:
        orm_mode = True

    def __repr__(self):
        """
        Return a string representation of the token price instance.
        """
        return f"""
            <TokenPrice token_id={self.token_id} timestamp={self.timestamp}>
        """
