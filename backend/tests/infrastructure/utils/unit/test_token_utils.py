import time
from datetime import datetime, timezone

from app.utils.token import generate_token, hash_token


def test_generate_token_unique_and_expiry():
    t1, h1, exp1 = generate_token(1)
    time.sleep(0.01)
    t2, h2, exp2 = generate_token(1)
    assert t1 != t2
    assert h1 == hash_token(t1)
    assert h2 == hash_token(t2)
    assert exp1 > datetime.now(timezone.utc)
    assert (exp2 - exp1).seconds <= 60


def test_hash_token_deterministic():
    token = "abc"
    assert hash_token(token) == hash_token(token)
