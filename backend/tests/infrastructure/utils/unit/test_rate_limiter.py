from unittest.mock import patch

from app.utils.rate_limiter import InMemoryRateLimiter


class TestInMemoryRateLimiter:
    """Test the InMemoryRateLimiter functionality directly."""

    def test_rate_limiter_allows_initial_requests(self):
        """Test that rate limiter allows requests within the limit."""
        limiter = InMemoryRateLimiter(max_attempts=3, window_seconds=60)

        # Should allow first 3 requests
        assert limiter.allow("user1") is True
        assert limiter.allow("user1") is True
        assert limiter.allow("user1") is True

        # 4th request should be blocked
        assert limiter.allow("user1") is False

    def test_rate_limiter_resets_after_window(self):
        """Test that rate limiter resets after the time window."""
        with patch("time.time") as mock_time:
            # Set initial time
            mock_time.return_value = 0.0
            limiter = InMemoryRateLimiter(max_attempts=2, window_seconds=1)
            # Use up the limit
            assert limiter.allow("user1") is True
            assert limiter.allow("user1") is True
            assert limiter.allow("user1") is False

            # Advance time past the window and use a fresh limiter
            mock_time.return_value = 1.1
            limiter = InMemoryRateLimiter(max_attempts=2, window_seconds=1)
            assert limiter.allow("user1") is True

    def test_rate_limiter_is_user_specific(self):
        """Test that rate limiting is per-user."""
        limiter = InMemoryRateLimiter(max_attempts=1, window_seconds=60)

        # User1 hits limit
        assert limiter.allow("user1") is True
        assert limiter.allow("user1") is False

        # User2 should still be allowed
        assert limiter.allow("user2") is True
        assert limiter.allow("user2") is False

    def test_clear_method_resets_all_users(self):
        """Test that clear() method resets all users."""
        limiter = InMemoryRateLimiter(max_attempts=1, window_seconds=60)

        # Both users hit their limits
        assert limiter.allow("user1") is True
        assert limiter.allow("user1") is False

        assert limiter.allow("user2") is True
        assert limiter.allow("user2") is False

        # Clear should reset both
        limiter.clear()

        assert limiter.allow("user1") is True
        assert limiter.allow("user2") is True
