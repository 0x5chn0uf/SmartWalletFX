from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import JSON, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    """Database model for audit trail entries."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True  # store UUID as text
    )
    operation: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True  # store UUID as text
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )
    changes: Mapped[Dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    metadata_: Mapped[Dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )

    def __repr__(self) -> str:  # noqa: D401
        """Return a readable representation for debugging."""

        return (
            f"<AuditLog id={self.id} entity_type={self.entity_type} "
            f"entity_id={self.entity_id} operation={self.operation}>"
        )
