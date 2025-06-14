from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Transaction(Base):
    """
    SQLAlchemy model for a blockchain transaction.
    Represents a transaction associated with a wallet.
    """

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), index=True)
    hash = Column(String, unique=True, index=True)
    token_id = Column(Integer, ForeignKey("tokens.id"), nullable=True, index=True)
    type = Column(String, index=True)  # IN, OUT, SWAP, etc.
    amount = Column(Numeric(precision=18, scale=8), nullable=False)
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
        """
        Return a string representation of the transaction instance.
        """
        return (
            f"<Transaction hash={self.hash} wallet_id={self.wallet_id} "
            f"type={self.type}>"
        )
