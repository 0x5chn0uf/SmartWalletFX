from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, JSON, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """
    SQLAlchemy model for a user entity.
    Represents a user of the wallet tracking application.
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)

    email_verified = Column(Boolean, nullable=False, default=False, server_default="false")
    verification_deadline = Column(DateTime(timezone=True), nullable=True)

    # Role-based access control fields
    roles = Column(JSON, nullable=True, doc="List of user roles for RBAC")
    attributes = Column(
        JSON, nullable=True, doc="User attributes for ABAC (geo, portfolio_value, etc.)"
    )

    created_at = Column(
        DateTime, default=datetime.utcnow, nullable=False, doc="Creation timestamp."
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        doc="Last update timestamp.",
    )

    wallets = relationship("Wallet", back_populates="user")

    def __repr__(self):
        """
        Return a string representation of the user instance.
        """
        return f"<User username={self.username} email={self.email} roles={self.roles}>"
