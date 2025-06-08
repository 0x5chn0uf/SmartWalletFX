import re
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, unique=True, index=True)
    name = Column(String, nullable=True, default="Unnamed Wallet")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    token_balances = relationship("TokenBalance", back_populates="wallet")
    historical_balances = relationship("HistoricalBalance", back_populates="wallet")

    def __repr__(self):
        return f"<Wallet {self.address}>"

    def validate_address(self):
        """Validate the wallet address."""
        # Example regex for EVM address validation
        evm_address_regex = r"^0x[a-fA-F0-9]{40}$"
        if re.match(evm_address_regex, self.address):
            return True
        # Add additional validation for non-EVM addresses here
        return False
