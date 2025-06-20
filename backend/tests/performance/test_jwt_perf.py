"""Performance benchmarks measuring JWT encode and decode throughput.

The benchmarks use `python-jose[cryptography]` to measure:
1. Token generation speed (encode)
2. Token validation speed (decode)

Run via `pytest --benchmark-only` or let CI `performance-tests` job collect metrics.
"""

import time
from typing import Any

import pytest
from jose import jwt

pytestmark = pytest.mark.performance

ALGORITHM = "HS256"
SECRET = "x" * 32  # deterministic secret for benchmarks
PAYLOAD: dict[str, Any] = {"sub": "benchmark-user", "iat": int(time.time())}


@pytest.mark.benchmark(group="jwt-generate")
def test_jwt_generation_benchmark(benchmark):
    """Benchmark JSON-Web-Token generation time."""

    benchmark(lambda: jwt.encode(PAYLOAD, SECRET, algorithm=ALGORITHM))


@pytest.mark.benchmark(group="jwt-validate")
def test_jwt_validation_benchmark(benchmark):
    """Benchmark JSON-Web-Token validation time."""

    token = jwt.encode(PAYLOAD, SECRET, algorithm=ALGORITHM)

    benchmark(lambda: jwt.decode(token, SECRET, algorithms=[ALGORITHM]))
