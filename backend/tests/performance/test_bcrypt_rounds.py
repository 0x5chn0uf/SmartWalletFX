"""Performance benchmarks for bcrypt hashing with different round settings.

Run with: pytest --benchmark-only
"""

import pytest
from passlib.hash import bcrypt

PASSWORD = "CorrectHorseBatteryStaple!"


@pytest.mark.benchmark(group="bcrypt-hash")
@pytest.mark.parametrize("rounds", [12, 14, 15])
def test_bcrypt_hash_performance(benchmark, rounds):
    """Benchmark bcrypt hash generation with varying cost factors.

    • `rounds` values represent log2 of iterations (common secure defaults).
    • The benchmark measures the time for a single hash operation.
    """

    def _hash():
        bcrypt.using(rounds=rounds).hash(PASSWORD)

    benchmark(_hash)
