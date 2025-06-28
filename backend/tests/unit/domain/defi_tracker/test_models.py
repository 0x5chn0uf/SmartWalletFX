"""
Unit tests for DeFi Tracker domain models.

Tests the pure domain entities that don't depend on infrastructure.
"""

from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.domain.defi_tracker.entities import AggregateMetrics, Position


class TestPosition:
    """Test cases for Position domain model."""

    def test_position_creation_with_required_fields(self):
        """Test creating a Position with required fields only."""
        position = Position(
            protocol="Aave", asset="USDC", amount=1000.0, usd_value=1000.0
        )

        assert position.protocol == "Aave"
        assert position.asset == "USDC"
        assert position.amount == 1000.0
        assert position.usd_value == 1000.0
        assert position.apy is None

    def test_position_creation_with_apy(self):
        """Test creating a Position with APY."""
        position = Position(
            protocol="Compound", asset="DAI", amount=500.0, usd_value=500.0, apy=0.08
        )

        assert position.protocol == "Compound"
        assert position.asset == "DAI"
        assert position.amount == 500.0
        assert position.usd_value == 500.0
        assert position.apy == 0.08

    def test_position_creation_with_zero_values(self):
        """Test creating a Position with zero values."""
        position = Position(
            protocol="Maker", asset="ETH", amount=0.0, usd_value=0.0, apy=0.0
        )

        assert position.protocol == "Maker"
        assert position.asset == "ETH"
        assert position.amount == 0.0
        assert position.usd_value == 0.0
        assert position.apy == 0.0

    def test_position_creation_with_negative_values(self):
        """Test creating a Position with negative values."""
        position = Position(
            protocol="Aave", asset="USDT", amount=-100.0, usd_value=-100.0, apy=-0.05
        )

        assert position.protocol == "Aave"
        assert position.asset == "USDT"
        assert position.amount == -100.0
        assert position.usd_value == -100.0
        assert position.apy == -0.05

    def test_position_creation_with_large_values(self):
        """Test creating a Position with large values."""
        position = Position(
            protocol="Compound",
            asset="WBTC",
            amount=1000000.0,
            usd_value=50000000.0,
            apy=0.12,
        )

        assert position.protocol == "Compound"
        assert position.asset == "WBTC"
        assert position.amount == 1000000.0
        assert position.usd_value == 50000000.0
        assert position.apy == 0.12

    def test_position_creation_with_special_characters(self):
        """Test creating a Position with special characters in strings."""
        position = Position(
            protocol="Aave V2!@#", asset="USDC-ETH LP", amount=100.0, usd_value=100.0
        )

        assert position.protocol == "Aave V2!@#"
        assert position.asset == "USDC-ETH LP"
        assert position.amount == 100.0
        assert position.usd_value == 100.0

    def test_position_creation_with_empty_strings(self):
        """Test creating a Position with empty strings."""
        position = Position(protocol="", asset="", amount=0.0, usd_value=0.0)

        assert position.protocol == ""
        assert position.asset == ""
        assert position.amount == 0.0
        assert position.usd_value == 0.0

    def test_position_immutability(self):
        """Test that Position instances are immutable (slots=True)."""
        position = Position(
            protocol="Aave", asset="USDC", amount=1000.0, usd_value=1000.0
        )

        # Verify slots behavior - should not allow adding new attributes
        with pytest.raises(AttributeError):
            position.new_attribute = "test"


class TestAggregateMetrics:
    """Test cases for AggregateMetrics domain model."""

    def test_aggregate_metrics_creation_with_all_fields(self):
        """Test creating AggregateMetrics with all fields."""
        wallet_id = "0x1234567890abcdef"
        as_of = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        positions = [
            Position("Aave", "USDC", 1000.0, 1000.0, 0.08),
            Position("Compound", "DAI", 500.0, 500.0, 0.05),
        ]

        metrics = AggregateMetrics(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            wallet_id=wallet_id,
            tvl=1500.0,
            total_borrowings=200.0,
            aggregate_apy=0.07,
            as_of=as_of,
            positions=positions,
        )

        assert metrics.id == UUID("12345678-1234-5678-1234-567812345678")
        assert metrics.wallet_id == wallet_id
        assert metrics.tvl == 1500.0
        assert metrics.total_borrowings == 200.0
        assert metrics.aggregate_apy == 0.07
        assert metrics.as_of == as_of
        assert len(metrics.positions) == 2
        assert metrics.positions[0].protocol == "Aave"
        assert metrics.positions[1].protocol == "Compound"

    def test_aggregate_metrics_creation_with_none_apy(self):
        """Test creating AggregateMetrics with None APY."""
        wallet_id = "0x1234567890abcdef"
        as_of = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        metrics = AggregateMetrics(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            wallet_id=wallet_id,
            tvl=1000.0,
            total_borrowings=0.0,
            aggregate_apy=None,
            as_of=as_of,
            positions=[],
        )

        assert metrics.wallet_id == wallet_id
        assert metrics.tvl == 1000.0
        assert metrics.total_borrowings == 0.0
        assert metrics.aggregate_apy is None
        assert metrics.as_of == as_of
        assert len(metrics.positions) == 0

    def test_aggregate_metrics_creation_with_zero_values(self):
        """Test creating AggregateMetrics with zero values."""
        wallet_id = "0x1234567890abcdef"
        as_of = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        metrics = AggregateMetrics(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            wallet_id=wallet_id,
            tvl=0.0,
            total_borrowings=0.0,
            aggregate_apy=0.0,
            as_of=as_of,
            positions=[],
        )

        assert metrics.wallet_id == wallet_id
        assert metrics.tvl == 0.0
        assert metrics.total_borrowings == 0.0
        assert metrics.aggregate_apy == 0.0
        assert metrics.as_of == as_of
        assert len(metrics.positions) == 0

    def test_aggregate_metrics_creation_with_negative_values(self):
        """Test creating AggregateMetrics with negative values."""
        wallet_id = "0x1234567890abcdef"
        as_of = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        metrics = AggregateMetrics(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            wallet_id=wallet_id,
            tvl=-100.0,
            total_borrowings=-50.0,
            aggregate_apy=-0.05,
            as_of=as_of,
            positions=[],
        )

        assert metrics.wallet_id == wallet_id
        assert metrics.tvl == -100.0
        assert metrics.total_borrowings == -50.0
        assert metrics.aggregate_apy == -0.05
        assert metrics.as_of == as_of

    def test_aggregate_metrics_creation_with_large_values(self):
        """Test creating AggregateMetrics with large values."""
        wallet_id = "0x1234567890abcdef"
        as_of = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        positions = [
            Position("Aave", "WBTC", 1000000.0, 50000000.0, 0.12),
            Position("Compound", "ETH", 500000.0, 10000000.0, 0.08),
        ]

        metrics = AggregateMetrics(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            wallet_id=wallet_id,
            tvl=60000000.0,
            total_borrowings=10000000.0,
            aggregate_apy=0.10,
            as_of=as_of,
            positions=positions,
        )

        assert metrics.wallet_id == wallet_id
        assert metrics.tvl == 60000000.0
        assert metrics.total_borrowings == 10000000.0
        assert metrics.aggregate_apy == 0.10
        assert len(metrics.positions) == 2

    def test_aggregate_metrics_creation_with_special_characters(self):
        """Test creating AggregateMetrics with special characters in wallet_id."""
        wallet_id = "0x1234567890abcdef!@#$%^&*()"
        as_of = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        metrics = AggregateMetrics(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            wallet_id=wallet_id,
            tvl=1000.0,
            total_borrowings=0.0,
            aggregate_apy=0.05,
            as_of=as_of,
            positions=[],
        )

        assert metrics.wallet_id == wallet_id
        assert metrics.tvl == 1000.0
        assert metrics.total_borrowings == 0.0
        assert metrics.aggregate_apy == 0.05

    def test_aggregate_metrics_creation_with_empty_wallet_id(self):
        """Test creating AggregateMetrics with empty wallet_id."""
        wallet_id = ""
        as_of = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        metrics = AggregateMetrics(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            wallet_id=wallet_id,
            tvl=1000.0,
            total_borrowings=0.0,
            aggregate_apy=0.05,
            as_of=as_of,
            positions=[],
        )

        assert metrics.wallet_id == ""
        assert metrics.tvl == 1000.0
        assert metrics.total_borrowings == 0.0
        assert metrics.aggregate_apy == 0.05

    def test_aggregate_metrics_immutability(self):
        """Test that AggregateMetrics instances are immutable (slots=True)."""
        wallet_id = "0x1234567890abcdef"
        as_of = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        metrics = AggregateMetrics(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            wallet_id=wallet_id,
            tvl=1000.0,
            total_borrowings=0.0,
            aggregate_apy=0.05,
            as_of=as_of,
            positions=[],
        )

        # Verify slots behavior - should not allow adding new attributes
        with pytest.raises(AttributeError):
            metrics.new_attribute = "test"

    def test_new_class_method_with_default_as_of(self):
        """Test the new class method with default as_of timestamp."""
        wallet_id = "0x1234567890abcdef"

        metrics = AggregateMetrics.new(wallet_id)

        assert isinstance(metrics.id, UUID)
        assert metrics.wallet_id == wallet_id
        assert metrics.tvl == 0.0
        assert metrics.total_borrowings == 0.0
        assert metrics.aggregate_apy is None
        assert isinstance(metrics.as_of, datetime)
        assert len(metrics.positions) == 0

        # Verify timestamp is recent (within last minute)
        now = datetime.utcnow()
        time_diff = abs((now - metrics.as_of).total_seconds())
        assert time_diff < 60  # Should be within 60 seconds

    def test_new_class_method_with_custom_as_of(self):
        """Test the new class method with custom as_of timestamp."""
        wallet_id = "0x1234567890abcdef"
        custom_as_of = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        metrics = AggregateMetrics.new(wallet_id, as_of=custom_as_of)

        assert isinstance(metrics.id, UUID)
        assert metrics.wallet_id == wallet_id
        assert metrics.tvl == 0.0
        assert metrics.total_borrowings == 0.0
        assert metrics.aggregate_apy is None
        assert metrics.as_of == custom_as_of
        assert len(metrics.positions) == 0

    def test_new_class_method_with_empty_wallet_id(self):
        """Test the new class method with empty wallet_id."""
        wallet_id = ""

        metrics = AggregateMetrics.new(wallet_id)

        assert isinstance(metrics.id, UUID)
        assert metrics.wallet_id == wallet_id
        assert metrics.tvl == 0.0
        assert metrics.total_borrowings == 0.0
        assert metrics.aggregate_apy is None
        assert isinstance(metrics.as_of, datetime)
        assert len(metrics.positions) == 0

    def test_new_class_method_with_special_characters_wallet_id(self):
        """Test the new class method with special characters in wallet_id."""
        wallet_id = "0x1234567890abcdef!@#$%^&*()"

        metrics = AggregateMetrics.new(wallet_id)

        assert isinstance(metrics.id, UUID)
        assert metrics.wallet_id == wallet_id
        assert metrics.tvl == 0.0
        assert metrics.total_borrowings == 0.0
        assert metrics.aggregate_apy is None
        assert isinstance(metrics.as_of, datetime)
        assert len(metrics.positions) == 0

    def test_new_class_method_multiple_calls_generate_different_ids(self):
        """Test that multiple calls to new() generate different UUIDs."""
        wallet_id = "0x1234567890abcdef"

        metrics1 = AggregateMetrics.new(wallet_id)
        metrics2 = AggregateMetrics.new(wallet_id)

        assert metrics1.id != metrics2.id
        assert metrics1.wallet_id == metrics2.wallet_id
        assert metrics1.tvl == metrics2.tvl
        assert metrics1.total_borrowings == metrics2.total_borrowings
        assert metrics1.aggregate_apy == metrics2.aggregate_apy
        assert len(metrics1.positions) == len(metrics2.positions)
