import re
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Wallet(Base):
    """
    SQLAlchemy model for a wallet entity.
    Represents a blockchain wallet with address, user, balances, and metadata.
    """

    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    address = Column(String, unique=True, index=True)
    name = Column(String, nullable=True, default="Unnamed Wallet")
    type = Column(String, nullable=True)  # EVM, BTC, etc.
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_active = Column(Boolean, default=True)
    balance_usd = Column(Numeric(precision=18, scale=2), nullable=True)
    balance = Column(Numeric(precision=18, scale=8), nullable=False)

    # Relationships
    token_balances = relationship("TokenBalance", back_populates="wallet")
    historical_balances = relationship(
        "HistoricalBalance", back_populates="wallet"
    )
    transactions = relationship("Transaction", back_populates="wallet")
    # groups = relationship(
    #     "Group",
    #     secondary="wallet_groups",
    #     back_populates="wallets",
    # )

    def __repr__(self):
        """
        Return a string representation of the wallet instance.
        """
        return f"<Wallet {self.address}>"

    def validate_address(self):
        """
        Validate the wallet address format (EVM or other).
        Returns:
            bool: True if the address is valid, False otherwise.
        """
        # Example regex for EVM address validation
        evm_address_regex = r"^0x[a-fA-F0-9]{40}$"
        if re.match(evm_address_regex, self.address):
            return True
        # Add additional validation for non-EVM addresses here
        return False
