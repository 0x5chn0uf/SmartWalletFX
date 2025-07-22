import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.core.config import Configuration
from app.utils.security import PasswordHasher


@pytest.fixture
def password_hasher():
    """Create a PasswordHasher instance for testing."""
    return PasswordHasher(Configuration())


@pytest.mark.parametrize(
    "password",
    [
        "StrongPass1!",
        "Another$Tr0ngP@ss",
    ],
)
def test_hash_and_verify(password_hasher, password: str):
    hashed = password_hasher.hash_password(password)
    # Hash must differ from plaintext
    assert hashed != password
    # Correct password verifies
    assert password_hasher.verify_password(password, hashed)
    # Wrong password fails
    assert not password_hasher.verify_password("wrong" + password, hashed)


@settings(max_examples=10, deadline=None)
@given(
    st.text(min_size=8, max_size=32).filter(
        lambda s: (
            "\x00" not in s  # bcrypt disallows NUL bytes
            and any(c.isdigit() for c in s)
            and any(not c.isalnum() for c in s)
        )
    )
)
def test_round_trip_random(password: str):
    password_hasher = PasswordHasher(Configuration())
    hashed = password_hasher.hash_password(password)
    assert password_hasher.verify_password(password, hashed)
