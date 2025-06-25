import re
from uuid import uuid4

from sqlalchemy import Column, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Token(Base):
    """
    SQLAlchemy model for a blockchain token.
    Represents a token with address, symbol, decimals, and price.
    """

    __tablename__ = "tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    address = Column(String, unique=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    decimals = Column(Integer, default=18)
    current_price_usd = Column(Numeric(precision=18, scale=8), nullable=True)

    # Relationships
    balances = relationship("TokenBalance", back_populates="token")
    historical_prices = relationship("TokenPrice", back_populates="token")
    # transactions = relationship("Transaction", back_populates="token")

    def __repr__(self):
        """
        Return a string representation of the token instance.
        """
        return f"<Token {self.address} {self.symbol}>"

    def validate_address(self):
        """
        Validate the token contract address format (EVM or other).
        Returns:
            bool: True if the address is valid, False otherwise.
        """
        evm_address_regex = r"^0x[a-fA-F0-9]{40}$"
        if re.match(evm_address_regex, self.address):
            return True
        return False

    def validate_symbol(self):
        """
        Validate the token symbol format.
        Returns:
            bool: True if the symbol is valid, False otherwise.
        """
        return self.symbol.isupper() and len(self.symbol) > 0

    def validate_decimals(self):
        """
        Validate the decimals value for the token.
        Returns:
            bool: True if the decimals are valid, False otherwise.
        """
        return 0 <= self.decimals <= 18

    def validate_price(self):
        """
        Validate the price value for the token.
        Returns:
            bool: True if the price is valid, False otherwise.
        """
        return self.current_price_usd is None or self.current_price_usd > 0
