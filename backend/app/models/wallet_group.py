from sqlalchemy import Column, ForeignKey, Integer

from app.core.database import Base


class WalletGroup(Base):
    """
    SQLAlchemy model for the association between wallets and groups.
    Represents the many-to-many relationship between wallets and groups.
    """

    __tablename__ = "wallet_groups"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), index=True)
