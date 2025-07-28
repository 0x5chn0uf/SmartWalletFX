from __future__ import annotations

"""Reusable helpers for robust error-handling and logging.

This module centralises small utilities used across Serena to ensure that
exceptions are always logged **with full tracebacks** and – when desired –
converted into safe default return values instead of silently disappearing.
"""

import functools
import logging
from typing import Callable, TypeVar, Any, ParamSpec, Concatenate

_T = TypeVar("_T")
_P = ParamSpec("_P")


def log_exceptions(
    logger: logging.Logger | None = None,
    *,
    default_return: _T | None = None,
    reraise: bool = False,
) -> Callable[[Callable[Concatenate[Any, _P], _T]], Callable[Concatenate[Any, _P], _T]]:  # noqa: WPS231,E501
    """Decorator that logs unhandled exceptions with *traceback*.

    Parameters
    ----------
    logger:
        The logger instance to use.  If *None*, a logger named after the
        wrapped function's module is retrieved via :pyfunc:`logging.getLogger`.
    default_return:
        Value to return when an exception is intercepted and *reraise* is
        *False*.
    reraise:
        If *True*, re-raise the original exception after logging it.  When
        *False* (default) the decorator swallows the exception and returns
        *default_return*.
    """

    def decorator(func: Callable[Concatenate[Any, _P], _T]) -> Callable[Concatenate[Any, _P], _T]:  # noqa: WPS231,E501
        log = logger or logging.getLogger(func.__module__)

        @functools.wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:  # type: ignore[misc]
            try:
                return func(*args, **kwargs)
            except Exception:  # noqa: BLE001
                # Log full traceback for easier post-mortem debugging
                log.exception("Unhandled exception in %s", func.__qualname__)
                if reraise:
                    raise
                return default_return  # type: ignore[return-value]

        return wrapper

    return decorator


__all__ = [
    "log_exceptions",
] 