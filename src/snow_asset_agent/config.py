"""Configuration management for snow-asset-agent.

Uses pydantic-settings to load configuration from environment variables
and an optional ``.env`` file.  A cached singleton is exposed via
:func:`get_config`.
"""

from __future__ import annotations

import functools
import logging

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class AssetAgentConfig(BaseSettings):
    """ServiceNow Asset Agent configuration loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    servicenow_instance: str = Field(
        ...,
        alias="SERVICENOW_INSTANCE",
        description="ServiceNow instance URL, e.g. https://dev12345.service-now.com",
    )
    servicenow_username: str = Field(
        ...,
        alias="SERVICENOW_USERNAME",
        description="ServiceNow user with asset-read roles",
    )
    servicenow_password: str = Field(
        ...,
        alias="SERVICENOW_PASSWORD",
        description="ServiceNow password (kept out of logs)",
    )
    servicenow_timeout: int = Field(
        30,
        alias="SERVICENOW_TIMEOUT",
        description="HTTP request timeout in seconds",
    )
    servicenow_max_retries: int = Field(
        3,
        alias="SERVICENOW_MAX_RETRIES",
        description="Max retry attempts for transient errors",
    )
    log_level: str = Field(
        "INFO",
        alias="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    # ------------------------------------------------------------------
    # Derived helpers
    # ------------------------------------------------------------------

    @property
    def base_url(self) -> str:
        """Return the REST API base URL."""
        return self.servicenow_instance.rstrip("/") + "/api/now"

    @property
    def auth(self) -> tuple[str, str]:
        """Return (username, password) tuple for requests basic auth."""
        return (self.servicenow_username, self.servicenow_password)


# Optional config reference used by tools when config is not injected.
_override_config: AssetAgentConfig | None = None


def set_config(config: AssetAgentConfig) -> None:
    """Override the singleton config (useful for testing)."""
    global _override_config
    _override_config = config


def reset_config() -> None:
    """Clear the override and cached config."""
    global _override_config
    _override_config = None
    get_config.cache_clear()


@functools.lru_cache(maxsize=1)
def get_config() -> AssetAgentConfig:
    """Return the (cached) configuration singleton."""
    if _override_config is not None:
        return _override_config
    return AssetAgentConfig()  # type: ignore[call-arg]
