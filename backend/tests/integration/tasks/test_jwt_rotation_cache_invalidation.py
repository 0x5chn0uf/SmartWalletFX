"""Integration tests for JWT rotation cache invalidation."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.tasks.jwt_rotation import (
    _apply_key_set_update,
    _gather_current_key_set,
    promote_and_retire_keys,
)
from app.utils.jwt_rotation import KeySetUpdate


@pytest.fixture
def mock_redis():
    """Create a mocked Redis client for testing."""
    mock = AsyncMock()
    mock.delete.return_value = 1  # Successfully deleted 1 key
    mock.close.return_value = None
    return mock


class TestJwtRotationCacheInvalidation:
    """Test that JWT key rotation invalidates the JWKS cache."""

    def test_key_rotation_invalidates_jwks_cache(self, mock_redis):
        """Test that key rotation invalidates the JWKS cache."""
        # Mock the synchronous cache invalidation wrapper
        with patch(
            "app.utils.jwks_cache.invalidate_jwks_cache_sync", return_value=True
        ) as mock_invalidate:
            # Create a key set update that will trigger cache invalidation
            # We need to create a non-noop update
            update = KeySetUpdate(
                new_active_kid="new-key-id", keys_to_retire=["old-key-id"]
            )

            # Apply the update (this should trigger cache invalidation)
            _apply_key_set_update(update)

            # Verify cache invalidation was called
            mock_invalidate.assert_called_once()

    def test_noop_update_does_not_invalidate_cache(self, mock_redis):
        """Test that no-op updates don't trigger cache invalidation."""
        with patch(
            "app.utils.jwks_cache.invalidate_jwks_cache_sync", return_value=True
        ) as mock_invalidate:
            # Create a no-op update
            update = KeySetUpdate(new_active_kid=None, keys_to_retire=[])

            # Apply the update
            _apply_key_set_update(update)

            # Verify cache invalidation was NOT called
            mock_invalidate.assert_not_called()

    def test_cache_invalidation_failure_does_not_break_rotation(self, mock_redis):
        """Test that cache invalidation failures don't break key rotation."""
        # Mock cache invalidation to raise an exception
        with patch(
            "app.utils.jwks_cache.invalidate_jwks_cache_sync",
            side_effect=Exception("Redis connection failed"),
        ) as mock_invalidate:
            # Create a key set update that will trigger cache invalidation
            update = KeySetUpdate(
                new_active_kid="new-key-id", keys_to_retire=["old-key-id"]
            )

            # Apply the update - this should not raise an exception
            # even though cache invalidation fails
            _apply_key_set_update(update)

            # Verify cache invalidation was attempted
            mock_invalidate.assert_called_once()

    def test_cache_invalidation_false_return_handled(self, mock_redis):
        """Test that cache invalidation returning False is handled correctly."""
        # Mock cache invalidation to return False (failure)
        with patch(
            "app.utils.jwks_cache.invalidate_jwks_cache_sync", return_value=False
        ) as mock_invalidate:
            update = KeySetUpdate(new_active_kid="new-key-id", keys_to_retire=[])

            _apply_key_set_update(update)

            # Verify cache invalidation was called
            mock_invalidate.assert_called_once()

    def test_cache_invalidation_success_metrics(self, mock_redis):
        """Test that successful cache invalidation increments metrics."""
        with patch(
            "app.utils.jwks_cache.invalidate_jwks_cache_sync", return_value=True
        ) as mock_invalidate:
            with patch("app.tasks.jwt_rotation.METRICS") as mock_metrics:
                update = KeySetUpdate(new_active_kid="new-key-id", keys_to_retire=[])

                _apply_key_set_update(update)

                # Verify success metric was incremented at least once
                mock_metrics["cache_invalidation"].inc.assert_called()

                # Verify the cache invalidation function was called
                mock_invalidate.assert_called_once()

    def test_cache_invalidation_failure_metrics(self, mock_redis):
        """Test that failed cache invalidation increments error metrics."""
        with patch(
            "app.utils.jwks_cache.invalidate_jwks_cache_sync", return_value=False
        ) as mock_invalidate:
            with patch("app.tasks.jwt_rotation.METRICS") as mock_metrics:
                update = KeySetUpdate(new_active_kid="new-key-id", keys_to_retire=[])

                _apply_key_set_update(update)

                # Verify error metric was incremented at least once
                mock_metrics["cache_invalidation_error"].inc.assert_called()

                # Verify the cache invalidation function was called
                mock_invalidate.assert_called_once()

    def test_cache_invalidation_with_real_key_set(self):
        """Test cache invalidation with a real key set (integration test)."""
        # This test would require setting up a real key set
        # For now, we'll test the integration point
        with patch(
            "app.utils.jwks_cache.invalidate_jwks_cache_sync", return_value=True
        ) as mock_invalidate:
            # Get the current key set
            key_set = _gather_current_key_set()

            # Create an update based on the current state
            update = promote_and_retire_keys(key_set, datetime.now(timezone.utc))

            # Apply the update if it's not a no-op
            if not update.is_noop():
                _apply_key_set_update(update)

                # Verify cache invalidation was called
                mock_invalidate.assert_called_once()
            else:
                # If no update was needed, verify cache invalidation was not called
                mock_invalidate.assert_not_called()
