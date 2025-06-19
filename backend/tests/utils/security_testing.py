"""Security testing helpers (stub).

This module will eventually provide utilities for measuring execution time and asserting
constant-time properties to detect timing-attack vectors.

Current implementation is intentionally incomplete and raises NotImplementedError in
order to drive the red phase of the TDD cycle for Subtask 4.14.
"""

from __future__ import annotations

import asyncio
import time
from statistics import mean, stdev
from typing import Any, Callable, Iterable

__all__ = [
    "measure_operation_timing",
    "assert_constant_time_operation",
    "assert_timing_attack_resistant",
    "TimingAttackAssertionError",
    "assert_no_user_enumeration",
    "assert_generic_error_response",
]


async def _maybe_await(
    func: Callable[..., Any], *args: Any, **kwargs: Any
) -> Any:  # pragma: no cover
    """Helper that awaits *func* if it is a coroutine function."""

    result = func(*args, **kwargs)
    if asyncio.iscoroutine(result):
        return await result
    return result


class TimingAttackAssertionError(AssertionError):
    """Raised when a timing-based security assertion fails."""


def measure_operation_timing(
    func: Callable[..., Any],
    inputs: Iterable[Any],
    *,
    iterations: int = 100,
) -> list[int]:
    """Return a list of *iterations*×len(inputs) timing measurements in **nanoseconds**.

    The helper executes *func* for each *inputs* value *iterations* times and records
    the execution time via :pyfunc:`time.perf_counter_ns`.

    Both synchronous functions and coroutine functions are supported.  For coroutines
    we create a dedicated event-loop per measurement to avoid interference.
    """

    timings: list[int] = []
    loop = None
    is_async = asyncio.iscoroutinefunction(func)

    if is_async:
        # Lazily import asyncio event loop policy once to avoid overhead.
        loop = asyncio.new_event_loop()

    try:
        for _ in range(iterations):
            for value in inputs:
                start = time.perf_counter_ns()
                if is_async:
                    loop.run_until_complete(func(value))
                else:
                    func(value)
                end = time.perf_counter_ns()
                timings.append(end - start)
    finally:
        if loop is not None:
            loop.close()

    return timings


def _relative_stddev(nums: list[int]) -> float:
    """Return relative standard deviation (coefficient of variation)."""

    mu = mean(nums)
    if mu == 0:
        return 0.0
    if len(nums) < 2:
        return 0.0
    return stdev(nums) / mu


def assert_constant_time_operation(
    func: Callable[..., Any],
    inputs: Iterable[Any],
    *,
    variance_threshold: float = 0.05,
    iterations: int = 100,
) -> None:
    """Assert that *func* runs in constant-time for the supplied *inputs*.

    The function is executed *iterations* times for each input value. We then calculate
    the coefficient of variation of all collected timings.  If it exceeds
    *variance_threshold* the assertion fails with :class:`TimingAttackAssertionError`.
    """

    timings = measure_operation_timing(func, inputs, iterations=iterations)
    rstd = _relative_stddev(timings)
    if rstd > variance_threshold:
        raise TimingAttackAssertionError(
            f"Timing variance too high (rel std dev={rstd:.4f} > {variance_threshold})"
        )


def assert_timing_attack_resistant(
    func: Callable[..., Any],
    valid_input: Any,
    invalid_inputs: Iterable[Any],
    *,
    threshold: float = 0.1,
    iterations: int = 100,
) -> None:
    """Detect timing differences between valid vs. invalid inputs.

    We measure *func(valid_input)* *iterations* times and likewise for each value in
    *invalid_inputs*.  If the absolute difference between the mean timing of the
    valid runs and *any* invalid input exceeds *threshold* fraction of the valid
    mean, the assertion fails.
    """

    valid_mean = mean(
        measure_operation_timing(func, [valid_input], iterations=iterations)
    )

    for inval in invalid_inputs:
        inval_mean = mean(
            measure_operation_timing(func, [inval], iterations=iterations)
        )
        if valid_mean == 0:
            continue
        diff_ratio = abs(inval_mean - valid_mean) / valid_mean
        if diff_ratio > threshold:
            raise TimingAttackAssertionError(
                f"Detected potential timing leak: diff_ratio={diff_ratio:.4f} exceeds {threshold}"
            )


def assert_generic_error_response(
    response: Any,
    expected_status: int = 401,
    *,
    generic_substring: str | None = None,
) -> None:
    """Assert *response* is a generic auth error without user‐specific detail."""

    status = getattr(response, "status_code", None)
    if status != expected_status:
        raise TimingAttackAssertionError(
            f"Response status {status} != expected {expected_status}"
        )

    # Try to fetch JSON body
    detail: str | None = None
    if hasattr(response, "json"):
        try:
            payload = response.json()
        except Exception as exc:  # pragma: no cover
            raise TimingAttackAssertionError(
                "Error response is not valid JSON"
            ) from exc
        if isinstance(payload, dict):
            detail = payload.get("detail")
    if detail is None:
        # fallback: maybe plain-text .text attribute
        detail = getattr(response, "text", "")

    if generic_substring and generic_substring.lower() not in str(detail).lower():
        raise TimingAttackAssertionError(
            "Error message may leak information → not generic enough"
        )


def assert_no_user_enumeration(
    auth_func: Callable[[str, str], Any],
    *,
    valid_user: tuple[str, str],
    invalid_users: Iterable[tuple[str, str]],
    threshold: float = 0.1,
    iterations: int = 20,
) -> None:
    """Ensure auth function doesn't leak enumeration info via timing or messages."""

    def _invoke(creds: tuple[str, str]):
        username, pw = creds
        res = auth_func(username, pw)
        if asyncio.iscoroutine(res):
            return asyncio.get_event_loop().run_until_complete(res)
        return res

    # Check generic error for invalid creds where response-like object
    for creds in invalid_users:
        resp = _invoke(creds)
        if hasattr(resp, "status_code"):
            assert_generic_error_response(resp, 401, generic_substring="invalid")

    valid_time = mean(
        measure_operation_timing(
            lambda _=None: _invoke(valid_user), [None], iterations=iterations
        )
    )

    for creds in invalid_users:
        inval_time = mean(
            measure_operation_timing(
                lambda _=None: _invoke(creds), [None], iterations=iterations
            )
        )
        if abs(inval_time - valid_time) / valid_time > threshold:
            raise TimingAttackAssertionError(
                "Timing difference indicates possible user enumeration leak"
            )
