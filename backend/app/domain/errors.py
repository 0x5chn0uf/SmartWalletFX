class AuthenticationError(Exception):
    """Base class for authentication-related domain errors."""


class InvalidCredentialsError(AuthenticationError):
    """Raised when the provided username/email + password combination is invalid."""


class InactiveUserError(AuthenticationError):
    """Raised when the user exists but is marked as inactive/disabled."""


__all__ = [
    "AuthenticationError",
    "InvalidCredentialsError",
    "InactiveUserError",
]
