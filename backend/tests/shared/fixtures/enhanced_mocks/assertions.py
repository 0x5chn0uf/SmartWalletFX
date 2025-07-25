# Mock assertion helpers
from .base import StatefulMock


class MockAssertions:
    """Utilities for asserting mock behaviors."""

    @staticmethod
    def assert_called_once_with(mock: StatefulMock, func_name: str, *args, **kwargs):
        """Assert that a function was called exactly once with specific arguments."""
        calls = mock.get_calls(func_name)
        assert (
            len(calls) == 1
        ), f"Expected {func_name} to be called once, got {len(calls)} calls"

        call = calls[0]
        assert call.args == args, f"Expected args {args}, got {call.args}"
        assert call.kwargs == kwargs, f"Expected kwargs {kwargs}, got {call.kwargs}"

    @staticmethod
    def assert_not_called(mock: StatefulMock, func_name: str):
        """Assert that a function was not called."""
        calls = mock.get_calls(func_name)
        assert (
            len(calls) == 0
        ), f"Expected {func_name} not to be called, got {len(calls)} calls"

    @staticmethod
    def assert_call_count(mock: StatefulMock, func_name: str, expected_count: int):
        """Assert specific call count for a function."""
        calls = mock.get_calls(func_name)
        assert (
            len(calls) == expected_count
        ), f"Expected {expected_count} calls, got {len(calls)}"

