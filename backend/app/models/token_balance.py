from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship

from app.core.database import Base


class TokenBalance(Base):
    __tablename__ = "token_balances"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), index=True)
    token_id = Column(Integer, ForeignKey("tokens.id"), index=True)
    balance = Column(
        Numeric(precision=36, scale=18)  # Large precision for wei values
    )
    balance_usd = Column(Numeric(precision=18, scale=2), nullable=True)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    wallet = relationship("Wallet", back_populates="token_balances")
    token = relationship("Token", back_populates="balances")

    class Config:
        orm_mode = True

    def __repr__(self):
        return f"<TokenBalance wallet_id={self.wallet_id} \
            token_id={self.token_id}>"
