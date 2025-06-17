import pytest

from app.validators.security import SecurityValidator


@pytest.mark.parametrize("input_val, expected", [(4, 4), (6, 6), ("12", 12)])
def test_bcrypt_rounds_valid(input_val, expected):
    assert SecurityValidator.bcrypt_rounds(input_val) == expected


def test_bcrypt_rounds_invalid():
    with pytest.raises(ValueError):
        SecurityValidator.bcrypt_rounds(3)
