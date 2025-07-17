"""Property-based template tests for authentication user input.

Ensures strategy helpers generate values that satisfy runtime validators.
"""
from __future__ import annotations

import re

import pydantic
from hypothesis import given, settings
from pydantic import EmailStr

from app.utils import security as sec_utils
from tests.strategies import security as strat

# ---------------------------------------------------------------------------
# Password strength invariants
# ---------------------------------------------------------------------------


@given(pwd=strat.strong_passwords())
@settings(max_examples=50)
def test_generated_passwords_pass_strength_validator(
    pwd: str,
) -> None:  # pragma: no cover
    """Every generated password must pass the runtime strength validator."""

    assert sec_utils.validate_password_strength(pwd)


# ---------------------------------------------------------------------------
# Email address invariants
# ---------------------------------------------------------------------------


@given(email=strat.email_addresses())
@settings(max_examples=50)
def test_generated_emails_validate_via_pydantic(email: str) -> None:  # pragma: no cover
    """Generated email strings must be valid according to Pydantic's EmailStr."""

    # Round-trip through Pydantic model to assert validity
    from pydantic import BaseModel

    class EmailModel(BaseModel):
        email: EmailStr

    try:
        validated = EmailModel(email=email)
        parsed_email = validated.email
    except pydantic.ValidationError as exc:  # pragma: no cover
        raise AssertionError(f"Generated email failed validation: {email}") from exc

    # Simple regex sanity check – contains '@' and at least one dot in domain
    assert re.match(r"^[^@]+@[^@]+\.[^@]+$", str(parsed_email))
