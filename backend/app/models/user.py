from uuid import uuid4

from sqlalchemy import Column, String
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

    wallets = relationship("Wallet", back_populates="user")

    def __repr__(self):
        """
        Return a string representation of the user instance.
        """
        return f"<User username={self.username} email={self.email}>"
