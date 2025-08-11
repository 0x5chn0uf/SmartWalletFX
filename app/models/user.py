from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Column, DateTime, String
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

    email_verified = Column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    # Role-based access control fields
    roles = Column(JSON, nullable=True, doc="List of user roles for RBAC")
    attributes = Column(
        JSON, nullable=True, doc="User attributes for ABAC (geo, portfolio_value, etc.)"
    )

    # Profile management fields
    profile_picture_url = Column(
        String(500), nullable=True, doc="URL to user's profile picture"
    )
    first_name = Column(String(100), nullable=True, doc="User's first name")
    last_name = Column(String(100), nullable=True, doc="User's last name")
    bio = Column(String(1000), nullable=True, doc="User's bio/description")
    timezone = Column(String(50), nullable=True, doc="User's preferred timezone")
    preferred_currency = Column(
        String(10), nullable=True, default="USD", doc="User's preferred currency"
    )
    notification_preferences = Column(
        JSON, nullable=True, doc="User notification preferences"
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
