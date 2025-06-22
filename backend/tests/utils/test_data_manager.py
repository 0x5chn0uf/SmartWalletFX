import hashlib
from typing import Literal

import psycopg2


class TestDataManager:
    """
    Manages test data generation and validation for E2E backup/restore tests.
    Provides utilities to:
      - Generate realistic schemas
      - Populate test data
      - Validate data integrity between two databases
      - Measure database size
    """

    def __init__(self, db_url: str):
        self.db_url = db_url

    def generate_realistic_schema(
        self, size: Literal["small", "large"] = "small"
    ) -> None:
        """
        Create tables, indexes, and optionally triggers/views for the test DB.
        """
        schema_file = (
            "backend/tests/fixtures/init.sql"
            if size == "small"
            else "backend/tests/fixtures/large_dataset.sql"
        )
        with open(schema_file, "r") as f:
            sql = f.read()
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()

    def populate_test_data(self, volume: Literal["small", "large"] = "small") -> None:
        """
        Populate the database with test data. For 'large', assumes schema already includes data.
        """
        # For 'large', data is already inserted by schema
        if volume == "large":
            return
        # For 'small', insert a few rows
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (username, email) VALUES
                        ('alice', 'alice@example.com'),
                        ('bob', 'bob@example.com');
                    INSERT INTO wallets (user_id, address, name) VALUES
                        (1, '0x1111111111111111111111111111111111111111', 'Alice Main'),
                        (2, '0x2222222222222222222222222222222222222222', 'Bob Main');
                    INSERT INTO transactions (wallet_id, hash, block_number, value, gas_used, gas_price) VALUES
                        (1, '0xaaa', 100, 1.5, 21000, 20000000000),
                        (2, '0xbbb', 101, 2.5, 22000, 21000000000);
                    INSERT INTO token_balances (wallet_id, token_address, balance) VALUES
                        (1, '0xTokenA', 100.0),
                        (2, '0xTokenB', 200.0);
                """
                )
            conn.commit()

    def validate_data_integrity(self, db_url_1: str, db_url_2: str) -> bool:
        """
        Compare row counts and table checksums between two databases.
        Returns True if all match, False otherwise.
        """
        tables = ["users", "wallets", "transactions", "token_balances"]

        def get_table_checksums(db_url):
            checksums = {}
            with psycopg2.connect(db_url) as conn:
                with conn.cursor() as cur:
                    for table in tables:
                        cur.execute(
                            f"SELECT COUNT(*), COALESCE(SUM(CAST(hashtext(row_to_json(t)) AS BIGINT)), 0) FROM {table} t;"
                        )
                        count, checksum = cur.fetchone()
                        checksums[table] = (count, checksum)
            return checksums

        c1 = get_table_checksums(db_url_1)
        c2 = get_table_checksums(db_url_2)
        return c1 == c2

    def measure_database_size(self) -> int:
        """
        Return the total size of the database in bytes.
        """
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_database_size(current_database());")
                (size,) = cur.fetchone()
        return size
