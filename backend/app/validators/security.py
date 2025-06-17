"""Validation helpers related to security and password hashing settings."""

from __future__ import annotations

"""Security-related validators.

Using a class allows grouping multiple validation helpers in a single cohesive
namespace while still benefiting from static methods (no instantiation
required). This pattern scales better when the number of validation rules
grows.
"""


class SecurityValidator:  # noqa: D101 – grouping utility
    """Collection of security-focused validation helpers for settings."""

    MIN_BCRYPT_ROUNDS: int = 4

    # ---------------------------------------------------------------------
    # BCrypt rounds
    # ---------------------------------------------------------------------

    @staticmethod
    def bcrypt_rounds(value: int | str) -> int:
        """Ensure **BCRYPT_ROUNDS** stays within a secure, sensible range.

        Parameters
        ----------
        value: int | str
            Raw value coming from environment/config.

        Returns
        -------
        int
            Sanitised integer rounds value.

        Raises
        ------
        ValueError
            If *value* is below the minimum secure threshold.
        """

        rounds = int(value)
        if rounds < SecurityValidator.MIN_BCRYPT_ROUNDS:
            min_rounds = SecurityValidator.MIN_BCRYPT_ROUNDS
            raise ValueError(
                (
                    "BCRYPT_ROUNDS must be >= "
                    f"{min_rounds} to maintain minimal security."
                )
            )
        return rounds
