"""Tests for snow_asset_agent.config."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from snow_asset_agent.config import AssetAgentConfig, get_config, reset_config, set_config


class TestAssetAgentConfig:
    """Test configuration loading, defaults, and validation."""

    def test_required_fields_present(self, test_config):
        assert test_config.servicenow_instance == "https://test.service-now.com"
        assert test_config.servicenow_username == "test_user"
        assert test_config.servicenow_password == "test_pass"

    def test_defaults(self):
        cfg = AssetAgentConfig(
            servicenow_instance="https://x.service-now.com",
            servicenow_username="u",
            servicenow_password="p",
        )
        assert cfg.servicenow_timeout == 30
        assert cfg.servicenow_max_retries == 3
        assert cfg.log_level == "INFO"

    def test_custom_timeout(self):
        cfg = AssetAgentConfig(
            servicenow_instance="https://x.service-now.com",
            servicenow_username="u",
            servicenow_password="p",
            servicenow_timeout=60,
        )
        assert cfg.servicenow_timeout == 60

    def test_custom_max_retries(self):
        cfg = AssetAgentConfig(
            servicenow_instance="https://x.service-now.com",
            servicenow_username="u",
            servicenow_password="p",
            servicenow_max_retries=5,
        )
        assert cfg.servicenow_max_retries == 5

    def test_log_level_override(self):
        cfg = AssetAgentConfig(
            servicenow_instance="https://x.service-now.com",
            servicenow_username="u",
            servicenow_password="p",
            log_level="DEBUG",
        )
        assert cfg.log_level == "DEBUG"

    def test_base_url_strips_trailing_slash(self):
        cfg = AssetAgentConfig(
            servicenow_instance="https://x.service-now.com/",
            servicenow_username="u",
            servicenow_password="p",
        )
        assert cfg.base_url == "https://x.service-now.com/api/now"

    def test_base_url_no_trailing_slash(self):
        cfg = AssetAgentConfig(
            servicenow_instance="https://x.service-now.com",
            servicenow_username="u",
            servicenow_password="p",
        )
        assert cfg.base_url == "https://x.service-now.com/api/now"

    def test_auth_tuple(self, test_config):
        assert test_config.auth == ("test_user", "test_pass")

    def test_missing_instance_raises(self):
        with pytest.raises((ValueError, TypeError)):
            AssetAgentConfig(
                servicenow_username="u",
                servicenow_password="p",
            )

    def test_missing_username_raises(self):
        with pytest.raises((ValueError, TypeError)):
            AssetAgentConfig(
                servicenow_instance="https://x.service-now.com",
                servicenow_password="p",
            )

    def test_missing_password_raises(self):
        with pytest.raises((ValueError, TypeError)):
            AssetAgentConfig(
                servicenow_instance="https://x.service-now.com",
                servicenow_username="u",
            )

    def test_env_alias_loading(self):
        env = {
            "SERVICENOW_INSTANCE": "https://alias.service-now.com",
            "SERVICENOW_USERNAME": "alias_u",
            "SERVICENOW_PASSWORD": "alias_p",
            "SERVICENOW_TIMEOUT": "10",
            "LOG_LEVEL": "WARNING",
        }
        with patch.dict(os.environ, env, clear=False):
            cfg = AssetAgentConfig()  # type: ignore[call-arg]
            assert cfg.servicenow_instance == "https://alias.service-now.com"
            assert cfg.servicenow_timeout == 10
            assert cfg.log_level == "WARNING"

    def test_extra_ignored(self):
        """Extra env vars should not cause validation errors."""
        cfg = AssetAgentConfig(
            servicenow_instance="https://x.service-now.com",
            servicenow_username="u",
            servicenow_password="p",
            SOME_EXTRA_VAR="ignored",  # type: ignore[call-arg]
        )
        assert cfg.servicenow_instance == "https://x.service-now.com"


class TestGetConfig:
    """Test the singleton config accessor."""

    def setup_method(self):
        reset_config()

    def teardown_method(self):
        reset_config()

    def test_set_and_get(self):
        cfg = AssetAgentConfig(
            servicenow_instance="https://singleton.service-now.com",
            servicenow_username="u",
            servicenow_password="p",
        )
        set_config(cfg)
        assert get_config().servicenow_instance == "https://singleton.service-now.com"

    def test_reset_clears(self):
        cfg = AssetAgentConfig(
            servicenow_instance="https://resettable.service-now.com",
            servicenow_username="u",
            servicenow_password="p",
        )
        set_config(cfg)
        reset_config()
        # After reset, calling get_config without env vars should fail
        with pytest.raises((ValueError, TypeError)):
            get_config()
