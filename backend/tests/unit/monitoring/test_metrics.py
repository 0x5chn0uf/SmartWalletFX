"""Unit tests for Prometheus metrics functionality."""

from unittest.mock import patch

import pytest

from app.monitoring.prometheus import (
    generate_metrics,
    get_registry,
    is_available,
    start_metrics_server,
)


class TestPrometheusMetrics:
    """Test Prometheus metrics functionality."""

    def test_is_available_with_prometheus_client(self):
        """Test is_available() when prometheus_client is available."""
        # This test should pass if prometheus_client is available
        # and fail if it's not (which is expected in test environment)
        result = is_available()
        # The test will fail if prometheus_client is not available
        # This is the expected RED state for TDD
        assert (
            result is True
        ), "Prometheus client should be available for metrics to work"

    def test_get_registry_with_prometheus_client(self):
        """Test get_registry() when prometheus_client is available."""
        registry = get_registry()
        # This test should pass if prometheus_client is available
        # and fail if it's not (which is expected in test environment)
        assert (
            registry is not None
        ), "Registry should be available when prometheus_client is installed"

    def test_generate_metrics_with_prometheus_client(self):
        """Test generate_metrics() when prometheus_client is available."""
        # This test should pass if prometheus_client is available
        # and fail if it's not (which is expected in test environment)
        metrics_data, content_type = generate_metrics()
        assert isinstance(metrics_data, bytes), "Metrics data should be bytes"
        assert (
            content_type == "text/plain; version=0.0.4; charset=utf-8"
        ), "Content type should match Prometheus format"

    def test_start_metrics_server_with_prometheus_client(self):
        """Test start_metrics_server() when prometheus_client is available."""
        # This test should pass if prometheus_client is available
        # and fail if it's not (which is expected in test environment)
        # We'll mock the start_http_server to avoid actually starting a server
        with patch("app.monitoring.prometheus.start_http_server") as mock_start:
            start_metrics_server(port=9090, addr="127.0.0.1")
            mock_start.assert_called_once_with(
                9090, "127.0.0.1", registry=get_registry()
            )

    @patch("app.monitoring.prometheus._PROMETHEUS_AVAILABLE", False)
    def test_is_available_without_prometheus_client(self):
        """Test is_available() when prometheus_client is not available."""
        result = is_available()
        assert (
            result is False
        ), "Should return False when prometheus_client is not available"

    @patch("app.monitoring.prometheus._PROMETHEUS_AVAILABLE", False)
    def test_get_registry_without_prometheus_client(self):
        """Test get_registry() when prometheus_client is not available."""
        registry = get_registry()
        assert (
            registry is None
        ), "Should return None when prometheus_client is not available"

    @patch("app.monitoring.prometheus._PROMETHEUS_AVAILABLE", False)
    def test_generate_metrics_without_prometheus_client(self):
        """Test generate_metrics() when prometheus_client is not available."""
        with pytest.raises(RuntimeError, match="Prometheus client not available"):
            generate_metrics()

    @patch("app.monitoring.prometheus._PROMETHEUS_AVAILABLE", False)
    def test_start_metrics_server_without_prometheus_client(self):
        """Test start_metrics_server() when prometheus_client is not available."""
        with pytest.raises(RuntimeError, match="Prometheus client not available"):
            start_metrics_server()
