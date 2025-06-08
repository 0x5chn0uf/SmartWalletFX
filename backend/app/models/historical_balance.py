from datetime import datetime

from app.core.database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship


class HistoricalBalance(Base):
    __tablename__ = "historical_balances"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), index=True)
    token_id = Column(Integer, ForeignKey("tokens.id"), index=True)
    balance = Column(Numeric(precision=36, scale=18))
    balance_usd = Column(Numeric(precision=18, scale=2))
    timestamp = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    wallet = relationship("Wallet", back_populates="historical_balances")
    token = relationship("Token", back_populates="historical_balances")

    class Config:
        orm_mode = True

    def __repr__(self):
        return f"<HistoricalBalance wallet_id={self.wallet_id} token_id={self.token_id} timestamp={self.timestamp}>"
