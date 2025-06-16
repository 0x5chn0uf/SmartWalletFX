from app.utils.security import (
    get_password_hash,
    validate_password_strength,
    verify_password,
)


def test_password_hash_and_verify():
    password = "StrongPass1!"
    hashed = get_password_hash(password)
    assert hashed != password  # hash should differ
    assert verify_password(password, hashed)
    assert not verify_password("WrongPass1!", hashed)


def test_validate_password_strength():
    assert validate_password_strength("Abcd1234!")
    assert not validate_password_strength("weak")
