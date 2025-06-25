from __future__ import annotations

"""SQLAlchemy model representing a persisted refresh token (JWT jti hash).

A refresh token is a *rotatable* credential that can be revoked server-side.
Only the SHA-256 hash of the token's ``jti`` is stored so that the raw token
value is never persisted.
"""

import uuid
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class RefreshToken(Base):
    """Refresh token persistence model."""

    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)

    # SHA-256 hash of the JWT ``jti`` claim – 64 hex chars
    jti_hash = Column(String(length=64), unique=True, nullable=False)

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user = relationship("app.models.user.User", backref="refresh_tokens")

    expires_at = Column(DateTime, nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("jti_hash", name="uq_refresh_tokens_jti_hash"),
        Index("ix_refresh_tokens_user_id", "user_id"),
    )

    # ---------------------------------------------------------------------
    # Helper constructors
    # ---------------------------------------------------------------------

    @classmethod
    def from_raw_jti(
        cls, jti: str, user_id: uuid.UUID, ttl: timedelta
    ) -> "RefreshToken":
        """Factory that hashes *jti* and returns :class:`RefreshToken`."""

        import hashlib  # local import to avoid global cost if unused

        now = datetime.now(timezone.utc)
        expires = now + ttl
        jti_hash = hashlib.sha256(jti.encode()).hexdigest()
        return cls(jti_hash=jti_hash, user_id=user_id, expires_at=expires)
