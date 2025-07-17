import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.utils.security import PasswordHasher


@pytest.mark.parametrize(
    "password",
    [
        "StrongPass1!",
        "Another$Tr0ngP@ss",
    ],
)
def test_hash_and_verify(password: str):
    hashed = PasswordHasher.hash_password(password)
    # Hash must differ from plaintext
    assert hashed != password
    # Correct password verifies
    assert PasswordHasher.verify_password(password, hashed)
    # Wrong password fails
    assert not PasswordHasher.verify_password("wrong" + password, hashed)


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
    hashed = PasswordHasher.hash_password(password)
    assert PasswordHasher.verify_password(password, hashed)
