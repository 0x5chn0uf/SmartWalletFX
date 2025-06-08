import re
from datetime import datetime

from app.core.database import Base
from sqlalchemy import Column, DateTime, Integer, Numeric, String
from sqlalchemy.orm import relationship


class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, unique=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    decimals = Column(Integer, default=18)
    current_price_usd = Column(Numeric(precision=18, scale=8), nullable=True)
    last_price_update = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    balances = relationship("TokenBalance", back_populates="token")
    historical_prices = relationship("TokenPrice", back_populates="token")
    historical_balances = relationship("HistoricalBalance", back_populates="token")

    def __repr__(self):
        return f"<Token {self.symbol}>"

    def validate_address(self):
        """Validate the token address."""
        evm_address_regex = r"^0x[a-fA-F0-9]{40}$"
        if re.match(evm_address_regex, self.address):
            return True
        return False

    def validate_symbol(self):
        """Ensure the symbol is uppercase and not empty."""
        return self.symbol.isupper() and len(self.symbol) > 0

    def validate_decimals(self):
        """Ensure decimals are within a valid range."""
        return 0 <= self.decimals <= 18

    def validate_price(self):
        """Ensure the current price is positive if provided."""
        return self.current_price_usd is None or self.current_price_usd > 0
