"""Test data management utilities for backup/restore end-to-end testing.

This module provides utilities for creating realistic test data sets and database
schemas for comprehensive backup and restore validation.
"""

import random
import string
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.models.historical_balance import HistoricalBalance
from app.models.portfolio_snapshot import PortfolioSnapshot
from app.models.user import User
from app.models.wallet import Wallet


class TestDataManager:
    """Manages test data creation and validation for backup/restore testing."""

    def __init__(self, dsn: str):
        """Initialize with database connection string."""
        self.dsn = dsn
        self.engine: Optional[Engine] = None

    async def create_test_database(self, schema_path: Optional[Path] = None) -> None:
        """Create test database with realistic schema and data."""
        self.engine = create_engine(self.dsn)

        # Use default schema if none provided
        if schema_path is None:
            schema_path = Path(__file__).parent / "init.sql"

        # Create tables and insert initial data
        with self.engine.connect() as conn:
            conn.execute(text(schema_path.read_text()))
            conn.commit()

        # Insert additional test data
        await self.insert_additional_test_data()

    async def insert_additional_test_data(self) -> None:
        """Insert additional test data for comprehensive testing."""
        if not self.engine:
            raise RuntimeError(
                "Database not initialized. Call create_test_database first."
            )

        # Generate additional users
        additional_users = self._generate_users(10)

        # Generate additional wallets and transactions
        additional_wallets = self._generate_wallets(additional_users, 25)
        additional_transactions = self._generate_transactions(additional_wallets, 100)
        additional_balances = self._generate_token_balances(additional_wallets, 50)

        # Insert the data
        with self.engine.connect() as conn:
            # Insert users
            for user in additional_users:
                conn.execute(
                    text(
                        """
                    INSERT INTO users (username, email)
                    VALUES (:username, :email)
                """
                    ),
                    user,
                )

            # Insert wallets
            for wallet in additional_wallets:
                conn.execute(
                    text(
                        """
                    INSERT INTO wallets (user_id, address, name)
                    VALUES (:user_id, :address, :name)
                """
                    ),
                    wallet,
                )

            # Insert transactions
            for tx in additional_transactions:
                conn.execute(
                    text(
                        """
                    INSERT INTO transactions (wallet_id, hash, block_number, value, gas_used, gas_price)
                    VALUES (:wallet_id, :hash, :block_number, :value, :gas_used, :gas_price)
                """
                    ),
                    tx,
                )

            # Insert token balances
            for balance in additional_balances:
                conn.execute(
                    text(
                        """
                    INSERT INTO token_balances (wallet_id, token_address, balance)
                    VALUES (:wallet_id, :token_address, :balance)
                """
                    ),
                    balance,
                )

            conn.commit()

    def _generate_users(self, count: int) -> List[Dict]:
        """Generate realistic user data."""
        users = []
        for i in range(count):
            username = f"testuser_{i+4}_{self._random_string(8)}"
            email = f"{username}@example.com"
            users.append({"username": username, "email": email})
        return users

    def _generate_wallets(self, users: List[Dict], count: int) -> List[Dict]:
        """Generate realistic wallet data."""
        wallets = []
        for i in range(count):
            user_id = random.randint(1, len(users) + 3)  # +3 for existing users
            address = f"0x{self._random_hex(40)}"
            name = f"Wallet {i+1}"
            wallets.append({"user_id": user_id, "address": address, "name": name})
        return wallets

    def _generate_transactions(self, wallets: List[Dict], count: int) -> List[Dict]:
        """Generate realistic transaction data."""
        transactions = []
        for i in range(count):
            wallet_id = random.randint(1, len(wallets) + 4)  # +4 for existing wallets
            tx_hash = f"0x{self._random_hex(64)}"
            block_number = random.randint(1000000, 2000000)
            value = round(random.uniform(0.001, 10.0), 6)
            gas_used = random.randint(21000, 100000)
            gas_price = random.randint(10000000000, 50000000000)

            transactions.append(
                {
                    "wallet_id": wallet_id,
                    "hash": tx_hash,
                    "block_number": block_number,
                    "value": value,
                    "gas_used": gas_used,
                    "gas_price": gas_price,
                }
            )
        return transactions

    def _generate_token_balances(self, wallets: List[Dict], count: int) -> List[Dict]:
        """Generate realistic token balance data."""
        balances = []
        token_addresses = [
            "0xA0b86a33E6441b8c4C8C8C8C8C8C8C8C8C8C8C8C",
            "0xB1c97b44E6442b9c5C9C9C9C9C9C9C9C9C9C9C9C",
            "0xC2d08c55E6443b0c6C6C6C6C6C6C6C6C6C6C6C6C",
            "0xD3e19d66E6444b1c7C7C7C7C7C7C7C7C7C7C7C7C",
            "0xE4f2a77E6445c2c8C8C8C8C8C8C8C8C8C8C8C8C8C",
        ]

        for i in range(count):
            wallet_id = random.randint(1, len(wallets) + 4)  # +4 for existing wallets
            token_address = random.choice(token_addresses)
            balance = round(random.uniform(0.1, 10000.0), 2)

            balances.append(
                {
                    "wallet_id": wallet_id,
                    "token_address": token_address,
                    "balance": balance,
                }
            )
        return balances

    def _random_string(self, length: int) -> str:
        """Generate a random string of specified length."""
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def _random_hex(self, length: int) -> str:
        """Generate a random hex string of specified length."""
        return "".join(random.choices("0123456789abcdef", k=length))

    async def validate_data_integrity(self) -> Dict[str, int]:
        """Validate that test data is consistent and return row counts."""
        if not self.engine:
            raise RuntimeError("Database not initialized.")

        with self.engine.connect() as conn:
            # Get row counts for all tables
            tables = ["users", "wallets", "transactions", "token_balances"]
            counts = {}

            for table in tables:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                counts[table] = result.scalar()

            # Validate foreign key relationships
            self._validate_foreign_keys(conn)

            return counts

    def _validate_foreign_keys(self, conn) -> None:
        """Validate foreign key relationships in the test data."""
        # Check that all wallets have valid user_id references
        result = conn.execute(
            text(
                """
            SELECT COUNT(*) FROM wallets w
            LEFT JOIN users u ON w.user_id = u.id
            WHERE u.id IS NULL
        """
            )
        )
        orphaned_wallets = result.scalar()
        if orphaned_wallets > 0:
            raise ValueError(f"Found {orphaned_wallets} wallets with invalid user_id")

        # Check that all transactions have valid wallet_id references
        result = conn.execute(
            text(
                """
            SELECT COUNT(*) FROM transactions t
            LEFT JOIN wallets w ON t.wallet_id = w.id
            WHERE w.id IS NULL
        """
            )
        )
        orphaned_transactions = result.scalar()
        if orphaned_transactions > 0:
            raise ValueError(
                f"Found {orphaned_transactions} transactions with invalid wallet_id"
            )

        # Check that all token_balances have valid wallet_id references
        result = conn.execute(
            text(
                """
            SELECT COUNT(*) FROM token_balances tb
            LEFT JOIN wallets w ON tb.wallet_id = w.id
            WHERE w.id IS NULL
        """
            )
        )
        orphaned_balances = result.scalar()
        if orphaned_balances > 0:
            raise ValueError(
                f"Found {orphaned_balances} token_balances with invalid wallet_id"
            )

    async def cleanup(self) -> None:
        """Clean up test database."""
        if self.engine:
            self.engine.dispose()


async def create_large_test_dataset(dsn: str, target_size_mb: int = 100) -> None:
    """Create a large test dataset for performance testing."""
    manager = TestDataManager(dsn)
    await manager.create_test_database()

    # Calculate how many records we need to reach target size
    # This is a rough estimate - actual size will vary
    records_per_mb = 1000  # Rough estimate
    target_records = target_size_mb * records_per_mb

    # Generate additional data to reach target size
    additional_users = manager._generate_users(target_records // 100)
    additional_wallets = manager._generate_wallets(
        additional_users, target_records // 10
    )
    additional_transactions = manager._generate_transactions(
        additional_wallets, target_records
    )

    # Insert the additional data
    with manager.engine.connect() as conn:
        for user in additional_users:
            conn.execute(
                text(
                    """
                INSERT INTO users (username, email)
                VALUES (:username, :email)
            """
                ),
                user,
            )

        for wallet in additional_wallets:
            conn.execute(
                text(
                    """
                INSERT INTO wallets (user_id, address, name)
                VALUES (:user_id, :address, :name)
            """
                ),
                wallet,
            )

        for tx in additional_transactions:
            conn.execute(
                text(
                    """
                INSERT INTO transactions (wallet_id, hash, block_number, value, gas_used, gas_price)
                VALUES (:wallet_id, :hash, :block_number, :value, :gas_used, :gas_price)
            """
                ),
                tx,
            )

        conn.commit()

    await manager.cleanup()


async def verify_backup_integrity(original_dsn: str, restored_dsn: str) -> bool:
    """Verify that a restored backup matches the original data."""
    original_manager = TestDataManager(original_dsn)
    restored_manager = TestDataManager(restored_dsn)

    try:
        # Get row counts from both databases
        original_counts = await original_manager.validate_data_integrity()
        restored_counts = await restored_manager.validate_data_integrity()

        # Compare row counts
        for table, original_count in original_counts.items():
            if original_count != restored_counts.get(table, 0):
                print(
                    f"Row count mismatch in {table}: {original_count} vs {restored_counts.get(table, 0)}"
                )
                return False

        # Compare sample data
        if not await _compare_sample_data(original_dsn, restored_dsn):
            return False

        return True

    finally:
        await original_manager.cleanup()
        await restored_manager.cleanup()


async def _compare_sample_data(original_dsn: str, restored_dsn: str) -> bool:
    """Compare sample data between original and restored databases."""
    original_engine = create_engine(original_dsn)
    restored_engine = create_engine(restored_dsn)

    try:
        with original_engine.connect() as orig_conn, restored_engine.connect() as rest_conn:
            # Compare a sample of users
            orig_users = orig_conn.execute(
                text("SELECT * FROM users LIMIT 10")
            ).fetchall()
            rest_users = rest_conn.execute(
                text("SELECT * FROM users LIMIT 10")
            ).fetchall()

            if len(orig_users) != len(rest_users):
                return False

            for orig_user, rest_user in zip(orig_users, rest_users):
                if orig_user != rest_user:
                    return False

            # Compare a sample of wallets
            orig_wallets = orig_conn.execute(
                text("SELECT * FROM wallets LIMIT 10")
            ).fetchall()
            rest_wallets = rest_conn.execute(
                text("SELECT * FROM wallets LIMIT 10")
            ).fetchall()

            if len(orig_wallets) != len(rest_wallets):
                return False

            for orig_wallet, rest_wallet in zip(orig_wallets, rest_wallets):
                if orig_wallet != rest_wallet:
                    return False

            return True

    finally:
        original_engine.dispose()
        restored_engine.dispose()


# Sample data fixtures for testing
@pytest.fixture
def sample_user():
    """Create a sample User for testing."""
    return User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        created_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_wallet(sample_user):
    """Create a sample Wallet for testing."""
    return Wallet(
        id=uuid4(),
        user_id=sample_user.id,
        address="0x1234567890abcdef",
        name="Test Wallet",
    )


@pytest.fixture
def sample_portfolio_snapshot(sample_wallet):
    """Create a sample PortfolioSnapshot for testing."""
    return PortfolioSnapshot(
        id=uuid4(),
        user_address=sample_wallet.address,
        timestamp=int(datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc).timestamp()),
        total_collateral=1000.0,
        total_borrowings=200.0,
        total_collateral_usd=1500.0,
        total_borrowings_usd=300.0,
        aggregate_health_score=0.85,
        aggregate_apy=0.08,
        collaterals={},
        borrowings={},
        staked_positions={},
        health_scores={},
        protocol_breakdown={},
    )


@pytest.fixture
def sample_historical_balance(sample_wallet):
    """Create a sample HistoricalBalance for testing."""
    return HistoricalBalance(
        id=uuid4(),
        wallet_id=sample_wallet.id,
        token_id=uuid4(),
        balance=100.0,
        balance_usd=150.0,
        timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_wallet_data():
    """Create sample wallet data for testing."""
    return {
        "address": "0x1234567890abcdef",
        "name": "Test Wallet",
        "total_value": 1000.0,
        "total_balance": 500.0,
        "total_borrowings": 200.0,
        "net_apy": 0.08,
    }


@pytest.fixture
def sample_historical_data():
    """Create sample historical data for testing."""
    return {
        "wallet_id": "0x1234567890abcdef",
        "token_id": str(uuid4()),
        "balance": 100.0,
        "balance_usd": 150.0,
        "timestamp": datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    }


@pytest.fixture
def sample_portfolio_data():
    """Create sample portfolio data for testing."""
    return {
        "wallet_id": "0x1234567890abcdef",
        "total_value": 1000.0,
        "total_balance": 500.0,
        "total_borrowings": 200.0,
        "net_apy": 0.08,
        "positions": [
            {
                "token_address": "0xA0b86a33E6441b8c4C8C8C8C8C8C8C8C8C8C8C8C",
                "balance": 100.0,
                "price_usd": 1.5,
                "value_usd": 150.0,
            }
        ],
    }
