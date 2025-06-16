from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Group(Base):
    """
    SQLAlchemy model for a group of wallets.
    Represents a logical grouping of wallets for organization or access
    control.
    """

    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    # wallets = relationship(
    #     "Wallet",
    #     secondary="wallet_groups",
    #     back_populates="groups",
    # )

    def __repr__(self):
        """
        Return a string representation of the group instance.
        """
        return f"<Group name={self.name} user_id={self.user_id}>"
