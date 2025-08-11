"""Utilities for promoting and retiring JWT signing keys.

This module implements the *pure* state-machine logic that decides which keys
should be promoted to *active* status and which should be retired based on the
current time and the configured grace-period.  All I/O side-effects (e.g.
updating settings, persisting to disk, emitting audit logs) are handled by the
Celery task layer.  Keeping this logic pure makes it trivial to write fast,
reliable unit and property-based tests.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional, Set

from pydantic import BaseModel, Field, field_validator

__all__ = [
    "Key",  # Pydantic model representing a single signing key
    "KeySet",  # Current key-set state
    "KeySetUpdate",  # Calculated changes to apply (promote / retire)
    "promote_and_retire_keys",  # Pure helper deciding promotion / retirement
]


class Key(BaseModel):
    """Simple representation of a signing key and its metadata."""

    kid: str = Field(..., description="Key identifier")
    value: str = Field(..., description="PEM-encoded key material or secret")
    retired_at: Optional[datetime] = Field(
        None,
        description="When the key should be considered untrusted.  Tokens signed "
        "with this key are rejected once *now* >= retired_at.",
    )

    @field_validator("retired_at")
    def _ensure_tz(cls, v: Optional[datetime]) -> Optional[datetime]:  # noqa: N805
        if v and v.tzinfo is None:
            # Always treat naive datetimes as UTC for consistency
            return v.replace(tzinfo=timezone.utc)
        return v


class KeySet(BaseModel):
    """Represents the full JWT key-set at a given point in time."""

    keys: Dict[str, Key]
    active_kid: str = Field(
        ..., description="kid of the key used for signing new tokens"
    )
    next_kid: Optional[str] = Field(
        None,
        description=(
            "kid that will become active once *active_kid* is retired. " "May be None."
        ),
    )
    grace_period_seconds: int = Field(
        3600,
        description="How long an old active key remains valid after rotation (seconds)",
    )


class KeySetUpdate(BaseModel):
    """Return value for :func:`promote_and_retire_keys`"""

    new_active_kid: Optional[str] = None  # kid to promote; None = no change
    keys_to_retire: Set[str] = Field(default_factory=set)

    def is_noop(self) -> bool:  # noqa: D401 – simple helper
        """Return *True* when the update contains no changes."""

        return self.new_active_kid is None and not self.keys_to_retire


# ---------------------------------------------------------------------------
# Core decision function – *pure*, no I/O.
# ---------------------------------------------------------------------------


def promote_and_retire_keys(
    current_keys: KeySet, now: datetime
) -> KeySetUpdate:  # noqa: C901
    """Decide which keys to retire / promote.

    Parameters
    ----------
    current_keys:
        Snapshot of the current key-set state.
    now:
        Current UTC time.  Tests should pass in a frozen value for determinism.

    Returns
    -------
    KeySetUpdate
        Instructions describing which keys to retire and whether a new key
        should be promoted to *active* status.  The function performs *no* I/O
        or mutation – callers are responsible for applying the changes.
    """

    # Convert *now* to timezone-aware UTC datetime to simplify comparisons
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    update = KeySetUpdate()

    # 1. Identify keys whose *retired_at* timestamp has passed.
    expired: Set[str] = {
        kid
        for kid, key in current_keys.keys.items()
        if key.retired_at and now >= key.retired_at
    }

    # 2. Determine whether we need to promote *next_kid*.
    #    Promotion occurs only when the *active* key is scheduled for retirement
    #    AND either (a) its retirement time has passed or (b) it has already been
    #    flagged for retirement via update.keys_to_retire.
    active_key = current_keys.keys.get(current_keys.active_kid)
    if not active_key:
        # Should never happen but guard against inconsistent state – do nothing
        return update

    active_retired = (
        active_key.retired_at is not None and now >= active_key.retired_at
    ) or (current_keys.active_kid in expired)

    if active_retired and current_keys.next_kid:
        candidate = current_keys.keys.get(current_keys.next_kid)
        # Promote only if candidate exists and is *not* expired
        if candidate and not (candidate.retired_at and candidate.retired_at <= now):
            update.new_active_kid = candidate.kid

    # 3. Finalise retire set – never retire the key we're about to promote
    update.keys_to_retire = expired
    if update.new_active_kid:
        update.keys_to_retire.discard(update.new_active_kid)

    return update
