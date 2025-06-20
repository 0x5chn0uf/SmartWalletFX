from __future__ import annotations

"""Hypothesis strategy helpers for security and authentication related tests.

The functions defined here will be imported by property-based test templates
and feature-specific tests.  For now the implementation is minimal so that the
initial failing unit test can import the module; real strategies will be
implemented in the subsequent BUILD steps.
"""

# NOTE: Hypothesis is optional at import-time in production runtime, so we
# import lazily inside functions to avoid adding a hard dependency at module
# import when running non-test code.

__all__ = [
    "strong_passwords",
    "email_addresses",
    "jwt_tokens",
    "safe_sql_strings",
]


def strong_passwords():  # pragma: no cover – will be properly implemented later
    """Return a Hypothesis strategy that generates strong passwords.

    Requirements enforced by the generated examples:
    * At least 8 characters long
    * Contains at least one ASCII digit (0-9)
    * Contains at least one punctuation / symbol from ``string.punctuation``.
    The strategy uses Hypothesis' :pyfunc:`~hypothesis.strategies.composite`
    helper to guarantee inclusion of the required character classes while
    still producing varied, realistic passwords.
    """

    import string

    from hypothesis import strategies as st  # local import

    # Character pools
    lowers = st.text(alphabet=string.ascii_lowercase, min_size=1)
    uppers = st.text(alphabet=string.ascii_uppercase, min_size=1)
    digits = st.text(alphabet=string.digits, min_size=1)
    allowed_symbols = "!@#$%^&*()_+=-"
    symbols = st.text(alphabet=allowed_symbols, min_size=1)

    @st.composite  # type: ignore[misc]
    def _password(draw):  # pragma: no cover
        # Draw mandatory parts first to guarantee presence
        part_lower = draw(lowers)
        part_upper = draw(uppers)
        part_digits = draw(digits)
        part_symbols = draw(symbols)

        # Draw optional additional characters from the full pool to reach ≥8
        remaining_len = max(
            0,
            8
            - (
                len(part_lower) + len(part_upper) + len(part_digits) + len(part_symbols)
            ),
        )
        rest = draw(
            st.text(
                alphabet=string.ascii_letters + string.digits + allowed_symbols,
                min_size=remaining_len,
            )
        )

        # Combine and shuffle to avoid predictable ordering
        password_chars = list(
            part_lower + part_upper + part_digits + part_symbols + rest
        )
        draw(st.permutations(password_chars))  # shuffle in-place via draw side effect
        return "".join(password_chars)

    return _password()


def email_addresses():  # pragma: no cover
    """Return a Hypothesis strategy for realistic email addresses.

    Uses :pydata:`hypothesis.strategies.emails` which already conforms to RFC
    standards and produces diverse domain / local-part combinations.
    """

    from hypothesis import strategies as st

    return st.emails()


def jwt_tokens():  # pragma: no cover
    """Return a strategy for syntactically valid *unsigned* JWT strings.

    The payload is random base64url strings (without padding) separated by
    dots.  Signature part is placeholder ("signature").  Consumers that need
    a signed token can post-process within their tests.
    """

    import string

    from hypothesis import strategies as st

    b64chars = string.ascii_letters + string.digits + "-_"
    part = st.text(alphabet=b64chars, min_size=4, max_size=20)

    return st.builds(lambda a, b: f"{a}.{b}.signature", part, part)


def safe_sql_strings():  # pragma: no cover
    """Return a strategy generating simple, harmless SQL statements.

    Useful for fuzzing SQL-string handling without risking injection of
    destructive commands.
    """

    from hypothesis import strategies as st

    keywords = st.sampled_from(["SELECT", "VALUES", "WITH", "EXPLAIN"])
    ints = st.integers(min_value=0, max_value=1000)

    return st.builds(lambda kw, num: f"{kw} {num};", keywords, ints)
