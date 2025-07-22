import logging
import sys
from io import StringIO
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.core.config import Configuration
from app.core.logging import CoreLogging


class TestCoreLogging:
    """Test CoreLogging class."""

    def test_init(self):
        """Test CoreLogging initialization."""
        config = Mock(spec=Configuration)
        core_logging = CoreLogging(config)

        assert core_logging.config is config
        assert core_logging._is_setup is False

    def test_setup_logging_first_time(self):
        """Test setup_logging when called for the first time."""
        config = Mock(spec=Configuration)
        config.LOG_LEVEL = "INFO"

        # Mock the root logger to have no handlers initially
        with patch("app.core.logging.logging.getLogger") as mock_get_logger, patch(
            "app.core.logging.logging.basicConfig"
        ) as mock_basic_config, patch(
            "app.core.logging.structlog.configure"
        ) as mock_structlog_configure, patch(
            "app.core.logging.sys.stdout"
        ):
            mock_root_logger = Mock()
            mock_root_logger.hasHandlers.return_value = False
            mock_get_logger.return_value = mock_root_logger

            core_logging = CoreLogging(config)
            core_logging.setup_logging()

            # Check that basicConfig was called with correct parameters
            mock_basic_config.assert_called_once_with(
                level=logging.INFO,
                format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
                stream=sys.stdout,
            )

            # Check that structlog was configured
            mock_structlog_configure.assert_called_once()

            # Check that noisy loggers were silenced
            assert mock_get_logger.call_count >= 4  # root + 3 noisy loggers

            assert core_logging._is_setup is True

    def test_setup_logging_with_existing_handlers(self):
        """Test setup_logging when handlers already exist."""
        config = Mock(spec=Configuration)
        config.LOG_LEVEL = "DEBUG"

        # Mock the root logger to have existing handlers
        with patch("app.core.logging.logging.getLogger") as mock_get_logger, patch(
            "app.core.logging.logging.basicConfig"
        ) as mock_basic_config, patch(
            "app.core.logging.structlog.configure"
        ) as mock_structlog_configure, patch(
            "app.core.logging.logging.Formatter"
        ) as mock_formatter:
            mock_handler = Mock()
            mock_root_logger = Mock()
            mock_root_logger.hasHandlers.return_value = True
            mock_root_logger.handlers = [mock_handler]
            mock_get_logger.return_value = mock_root_logger

            core_logging = CoreLogging(config)
            core_logging.setup_logging()

            # Check that basicConfig was NOT called
            mock_basic_config.assert_not_called()

            # Check that existing handler was configured
            mock_handler.setLevel.assert_called_once_with(logging.DEBUG)
            mock_handler.setFormatter.assert_called_once()

            # Check that formatter was created with correct format
            mock_formatter.assert_called_once_with(
                "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
            )

            # Check that structlog was configured
            mock_structlog_configure.assert_called_once()

            assert core_logging._is_setup is True

    def test_setup_logging_duplicate_calls(self):
        """Test that setup_logging avoids duplicate setup."""
        config = Mock(spec=Configuration)
        config.LOG_LEVEL = "INFO"

        with patch("app.core.logging.logging.getLogger") as mock_get_logger, patch(
            "app.core.logging.logging.basicConfig"
        ) as mock_basic_config:
            mock_root_logger = Mock()
            mock_root_logger.hasHandlers.return_value = False
            mock_get_logger.return_value = mock_root_logger

            core_logging = CoreLogging(config)

            # First call
            core_logging.setup_logging()
            assert mock_basic_config.call_count == 1

            # Second call should not trigger setup again
            core_logging.setup_logging()
            assert mock_basic_config.call_count == 1  # Still only 1 call

    def test_setup_logging_invalid_log_level(self):
        """Test setup_logging with invalid log level defaults to INFO."""
        config = Mock(spec=Configuration)
        config.LOG_LEVEL = "INVALID_LEVEL"

        with patch("app.core.logging.logging.getLogger") as mock_get_logger, patch(
            "app.core.logging.logging.basicConfig"
        ) as mock_basic_config:
            mock_root_logger = Mock()
            mock_root_logger.hasHandlers.return_value = False
            mock_get_logger.return_value = mock_root_logger

            core_logging = CoreLogging(config)
            core_logging.setup_logging()

            # Check that INFO level was used as default
            mock_basic_config.assert_called_once()
            args, kwargs = mock_basic_config.call_args
            assert kwargs["level"] == logging.INFO

    def test_get_logger_without_setup(self):
        """Test get_logger calls setup_logging if not already set up."""
        config = Mock(spec=Configuration)
        config.LOG_LEVEL = "INFO"

        with patch("app.core.logging.logging.getLogger") as mock_get_logger, patch(
            "app.core.logging.structlog.get_logger"
        ) as mock_structlog_get_logger:
            mock_root_logger = Mock()
            mock_root_logger.hasHandlers.return_value = False
            mock_get_logger.return_value = mock_root_logger

            mock_bound_logger = Mock()
            mock_structlog_get_logger.return_value = mock_bound_logger

            core_logging = CoreLogging(config)

            # get_logger should trigger setup_logging
            result = core_logging.get_logger("test_logger")

            assert core_logging._is_setup is True
            assert result is mock_bound_logger
            mock_structlog_get_logger.assert_called_once_with("test_logger")

    def test_get_logger_with_setup(self):
        """Test get_logger when setup has already been called."""
        config = Mock(spec=Configuration)
        config.LOG_LEVEL = "INFO"

        with patch("app.core.logging.logging.getLogger") as mock_get_logger, patch(
            "app.core.logging.structlog.get_logger"
        ) as mock_structlog_get_logger:
            mock_root_logger = Mock()
            mock_root_logger.hasHandlers.return_value = False
            mock_get_logger.return_value = mock_root_logger

            mock_bound_logger = Mock()
            mock_structlog_get_logger.return_value = mock_bound_logger

            core_logging = CoreLogging(config)
            core_logging.setup_logging()

            # Reset call count after setup
            mock_get_logger.reset_mock()

            # get_logger should NOT trigger setup_logging again
            result = core_logging.get_logger("test_logger")

            assert result is mock_bound_logger
            mock_structlog_get_logger.assert_called_once_with("test_logger")
            # Should not call getLogger again for setup
            mock_get_logger.assert_not_called()

    def test_is_setup_initial_state(self):
        """Test is_setup returns False initially."""
        config = Mock(spec=Configuration)
        core_logging = CoreLogging(config)

        assert core_logging.is_setup() is False

    def test_is_setup_after_setup(self):
        """Test is_setup returns True after setup_logging."""
        config = Mock(spec=Configuration)
        config.LOG_LEVEL = "INFO"

        with patch("app.core.logging.logging.getLogger") as mock_get_logger:
            mock_root_logger = Mock()
            mock_root_logger.hasHandlers.return_value = False
            mock_get_logger.return_value = mock_root_logger

            core_logging = CoreLogging(config)
            core_logging.setup_logging()

            assert core_logging.is_setup() is True

    def test_setup_logging_silences_noisy_loggers(self):
        """Test that setup_logging silences noisy dependencies."""
        config = Mock(spec=Configuration)
        config.LOG_LEVEL = "INFO"

        with patch("app.core.logging.logging.getLogger") as mock_get_logger:
            mock_root_logger = Mock()
            mock_root_logger.hasHandlers.return_value = False

            # Mock the noisy loggers
            mock_sql_logger = Mock()
            mock_uvicorn_error_logger = Mock()
            mock_uvicorn_access_logger = Mock()

            def get_logger_side_effect(name=None):
                if name is None or name == "":
                    return mock_root_logger
                elif name == "sqlalchemy.engine":
                    return mock_sql_logger
                elif name == "uvicorn.error":
                    return mock_uvicorn_error_logger
                elif name == "uvicorn.access":
                    return mock_uvicorn_access_logger
                return Mock()

            mock_get_logger.side_effect = get_logger_side_effect

            core_logging = CoreLogging(config)
            core_logging.setup_logging()

            # Check that noisy loggers were set to WARNING level
            mock_sql_logger.setLevel.assert_called_once_with(logging.WARNING)
            mock_uvicorn_error_logger.setLevel.assert_called_once_with(logging.WARNING)
            mock_uvicorn_access_logger.setLevel.assert_called_once_with(logging.WARNING)
