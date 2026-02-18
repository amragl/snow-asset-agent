"""Shared pytest fixtures for snow-asset-agent tests.

Provides configuration objects with test values, mock HTTP session
helpers, and sample ServiceNow record factories.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from snow_asset_agent.client import ServiceNowClient
from snow_asset_agent.config import AssetAgentConfig, reset_config, set_config

# ------------------------------------------------------------------
# Config fixtures
# ------------------------------------------------------------------


@pytest.fixture()
def test_config() -> AssetAgentConfig:
    """Return a config object with safe test values."""
    cfg = AssetAgentConfig(
        servicenow_instance="https://test.service-now.com",
        servicenow_username="test_user",
        servicenow_password="test_pass",
        servicenow_timeout=5,
        servicenow_max_retries=1,
        log_level="DEBUG",
    )
    set_config(cfg)
    yield cfg  # type: ignore[misc]
    reset_config()


# ------------------------------------------------------------------
# HTTP mock helpers
# ------------------------------------------------------------------


@pytest.fixture()
def mock_session(test_config: AssetAgentConfig) -> MagicMock:
    """Patch ``requests.Session`` so no real HTTP calls are made."""
    with patch("snow_asset_agent.client.requests.Session") as sess_cls:
        session = MagicMock()
        sess_cls.return_value = session
        yield session


@pytest.fixture()
def client_with_mock_session(test_config: AssetAgentConfig, mock_session: MagicMock) -> ServiceNowClient:
    """Return a ServiceNowClient whose internal session is mocked."""
    client = ServiceNowClient(test_config)
    client._session = mock_session
    return client
