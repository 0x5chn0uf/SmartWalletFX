from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), index=True)
    hash = Column(String, unique=True, index=True)
    token_id = Column(Integer, ForeignKey("tokens.id"), nullable=True, index=True)
    type = Column(String, index=True)  # IN, OUT, SWAP, etc.
    amount = Column(Numeric(precision=36, scale=18))
    usd_value = Column(Numeric(precision=18, scale=2), nullable=True)
    timestamp = Column(DateTime, index=True)
    from_address = Column(String, index=True)
    to_address = Column(String, index=True)
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    wallet = relationship("Wallet", back_populates="transactions")
    token = relationship("Token")

    def __repr__(self):
        return f"<Transaction hash={self.hash} wallet_id={self.wallet_id} type={self.type}>" 