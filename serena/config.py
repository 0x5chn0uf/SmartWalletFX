"""
Centralised configuration helper for Serena

Provides layered config resolution with precedence:
    1. Command-line overrides (supplied at call-site)
    2. Environment variables
    3. serena/config.json file (user-editable)
    4. Hard-coded defaults

Only a subset of settings is exposed for now; add more as
needed to avoid configuration sprawl.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
_DEFAULTS: Dict[str, Any] = {
    # Paths
    "memory_db": str(Path(__file__).parent / "database" / "memory_index.db"),
    "maintenance_config": str(
        Path(__file__).parent / "database" / "maintenance_config.json"
    ),
    # Features
    "disable_embeddings": False,
    "server_url": "http://localhost:8765",  # Default local API server
    # CORS settings
    "cors_origins": "http://localhost:3000,http://localhost:8080",  # Development defaults
    "cors_allow_credentials": True,
    "cors_allow_methods": "GET,POST,PUT,DELETE,OPTIONS",
    "cors_allow_headers": "*",
}

_CONFIG_PATH = Path(__file__).with_suffix(".json")  # serena/config.json


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _load_file_config() -> Dict[str, Any]:
    if _CONFIG_PATH.exists():
        try:
            with _CONFIG_PATH.open("r", encoding="utf-8") as fp:
                data: Dict[str, Any] = json.load(fp)
                return data  # noqa: WPS331
        except Exception:
            # Corrupt or invalid file – ignore gracefully
            return {}
    return {}


_FILE_CONFIG: Dict[str, Any] = _load_file_config()


def _env_bool(name: str, default: bool = False) -> bool:  # noqa: WPS110
    val = os.getenv(name)
    if val is None:
        return default
    return val.lower() in {"1", "true", "yes", "on"}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get(
    key: str, *, cli_override: Optional[Any] = None, default: Any = None
) -> Any:  # noqa: ANN001
    """Retrieve a config value with layered precedence."""
    if cli_override is not None:
        return cli_override

    # Environment lookup – env keys are upper-case with SERENA_ prefix
    env_key = f"SERENA_{key.upper()}"
    if env_key in os.environ:
        return os.environ[env_key]

    # Config file
    if key in _FILE_CONFIG:
        return _FILE_CONFIG[key]

    # Hard-coded default or provided default
    return _DEFAULTS.get(key, default)


def get_bool(
    key: str, *, cli_override: Optional[bool] = None, default: bool = False
) -> bool:  # noqa: ANN001
    """Specialised getter for boolean flags."""
    if cli_override is not None:
        return cli_override

    env_key = f"SERENA_{key.upper()}"
    if env_key in os.environ:
        return _env_bool(env_key, default)

    if key in _FILE_CONFIG:
        return bool(_FILE_CONFIG[key])

    return _DEFAULTS.get(key, default)


def dump_effective_config() -> Dict[str, Any]:
    """Return the effective configuration after merging all layers."""
    cfg: Dict[str, Any] = {}
    keys = {*_DEFAULTS.keys(), *_FILE_CONFIG.keys()}
    for key in keys:
        cfg[key] = get(key)
    return cfg


# Convenience helpers -------------------------------------------------------


def memory_db_path(cli_override: Optional[str] = None) -> str:
    return str(get("memory_db", cli_override=cli_override))


def maintenance_config_path(cli_override: Optional[str] = None) -> str:
    return str(get("maintenance_config", cli_override=cli_override))


def embeddings_enabled(cli_override: Optional[bool] = None) -> bool:
    return not get_bool("disable_embeddings", cli_override=cli_override)


def server_url(cli_override: Optional[str] = None) -> str:
    """Return configured API server base URL."""
    return str(get("server_url", cli_override=cli_override))

def cors_origins(cli_override: Optional[str] = None) -> list[str]:
    """Return configured CORS origins as a list."""
    origins_str = str(get("cors_origins", cli_override=cli_override))
    return [origin.strip() for origin in origins_str.split(",") if origin.strip()]


def cors_allow_credentials(cli_override: Optional[bool] = None) -> bool:
    """Return CORS allow credentials setting."""
    return get_bool("cors_allow_credentials", cli_override=cli_override)


def cors_allow_methods(cli_override: Optional[str] = None) -> list[str]:
    """Return configured CORS methods as a list."""
    methods_str = str(get("cors_allow_methods", cli_override=cli_override))
    return [method.strip() for method in methods_str.split(",") if method.strip()]


def cors_allow_headers(cli_override: Optional[str] = None) -> str:
    """Return configured CORS headers."""
    return str(get("cors_allow_headers", cli_override=cli_override))


def fast_cli_search_enabled(cli_override: Optional[bool] = None) -> bool:
    """Return whether fast CLI search mode is enabled."""
    return get_bool("fast_cli_search", cli_override=cli_override)
