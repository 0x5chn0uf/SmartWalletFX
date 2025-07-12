from __future__ import annotations

import threading

from .config import Settings


class SettingsService:
    """Wrapper around the pydantic ``Settings`` for future extensibility."""

    def __init__(self) -> None:
        self._settings = Settings()
        self._lock = threading.Lock()

    @property
    def settings(self) -> Settings:
        return self._settings
