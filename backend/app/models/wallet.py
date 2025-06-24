import re
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Wallet(Base):
    """
    Represents a wallet in the database.
    - `id`: Primary key.
    - `address`: EVM wallet address.
    - `name`: User-defined wallet name.
    - `created_at`: Timestamp of creation.
    - `updated_at`: Timestamp of last update.
    - `is_active`: Flag for active status.
    - `balance_usd`: Cached balance in USD.
    """

    __tablename__ = "wallets"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the wallet.",
    )
    address = Column(
        String,
        nullable=False,
        index=True,
        doc="EVM wallet address.",
    )
    name = Column(String, nullable=True, doc="User-defined wallet name.")
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        doc="Foreign key to the users table.",
    )

    created_at = Column(
        DateTime,
        default=func.now(),
        nullable=False,
        doc="Timestamp of wallet creation.",
    )
    updated_at = Column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp of last wallet update.",
    )
    is_active = Column(
        Boolean, default=True, nullable=False, doc="Flag for active status."
    )
    balance_usd = Column(
        Float, default=0.0, nullable=True, doc="Cached balance in USD."
    )

    # One-to-many – time-series of token balances
    historical_balances = relationship(
        "HistoricalBalance",
        back_populates="wallet",
        cascade="all, delete-orphan",
    )

    # One-to-many relationship with TokenBalance
    token_balances = relationship(
        "TokenBalance",
        back_populates="wallet",
        cascade="all, delete-orphan",
    )

    # One-to-many relationship with Transaction
    transactions = relationship(
        "Transaction",
        back_populates="wallet",
        cascade="all, delete-orphan",
    )

    user = relationship("User", back_populates="wallets")

    __table_args__ = (
        UniqueConstraint("user_id", "address", name="uq_wallet_user_address"),
    )

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
