from __future__ import annotations

from app.core.config import Settings


class ConfigurationService:
    """Wrap :class:`Settings` for DI-friendly usage."""

    def __init__(self) -> None:
        self.__settings = Settings()

    @property
    def settings(self) -> Settings:
        return self.__settings
