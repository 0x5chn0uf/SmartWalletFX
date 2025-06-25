from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class HistoricalBalance(Base):
    __tablename__ = "historical_balances"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    wallet_id = Column(
        UUID(as_uuid=True), ForeignKey("wallets.id"), index=True, nullable=False
    )
    token_id = Column(UUID(as_uuid=True), ForeignKey("tokens.id"), index=True)
    balance = Column(Numeric(precision=36, scale=18))
    balance_usd = Column(Numeric(precision=18, scale=2))
    timestamp = Column(DateTime, index=True)

    # Relationships
    wallet = relationship("Wallet", back_populates="historical_balances")
    token = relationship("Token")

    def __repr__(self):
        return f"""
            <HistoricalBalance wallet_id={self.wallet_id}
            token_id={self.token_id} timestamp={self.timestamp}>
        """
