from uuid import uuid4

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class WalletGroup(Base):
    """
    SQLAlchemy model for the association between wallets and groups.
    Represents the many-to-many relationship between wallets and groups.
    """

    __tablename__ = "wallet_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id"), index=True)
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"), index=True)
