from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class TokenBalance(Base):
    """
    SQLAlchemy model for a token balance associated with a wallet.
    Represents the amount of a specific token held by a wallet.
    """

    __tablename__ = "token_balances"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id"), index=True)
    token_id = Column(UUID(as_uuid=True), ForeignKey("tokens.id"), index=True)
    balance = Column(Numeric(precision=36, scale=18))  # Large precision for wei values
    balance_usd = Column(Numeric(precision=18, scale=2), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    wallet = relationship("Wallet", back_populates="token_balances")
    token = relationship("Token", back_populates="balances")

    class Config:
        orm_mode = True

    def __repr__(self):
        """
        Return a string representation of the token balance instance.
        """
        return f"<TokenBalance wallet_id={self.wallet_id} \
            token_id={self.token_id}>"
