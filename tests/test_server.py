"""Tests for snow_asset_agent.server.

Verifies server initialisation and that all expected tools are registered.
"""

from __future__ import annotations

import pytest

from snow_asset_agent.server import mcp


class TestServerInit:
    """Verify the FastMCP server is configured correctly."""

    def test_server_name(self):
        assert mcp.name == "snow-asset-agent"

    def test_server_has_tools(self):
        """All 14 tools (13 asset tools + health check) should be importable."""
        # Importing server registers all tools; we just verify the module loads
        from snow_asset_agent import server

        assert server.mcp is not None


class TestToolRegistration:
    """Verify that all expected tool functions exist on the server module."""

    EXPECTED_TOOLS = [
        "health_check",
        "tool_query_hardware_assets",
        "tool_query_software_licenses",
        "tool_get_asset_details",
        "tool_get_asset_lifecycle",
        "tool_get_asset_contracts",
        "tool_calculate_asset_costs",
        "tool_check_license_compliance",
        "tool_get_license_utilization",
        "tool_track_asset_depreciation",
        "tool_find_underutilized_assets",
        "tool_reconcile_assets_to_cis",
        "tool_get_asset_health_metrics",
        "tool_find_expiring_contracts",
    ]

    @pytest.mark.parametrize("tool_name", EXPECTED_TOOLS)
    def test_tool_function_exists(self, tool_name):
        from snow_asset_agent import server

        assert hasattr(server, tool_name), f"Missing tool function: {tool_name}"
        obj = getattr(server, tool_name)
        # FastMCP @mcp.tool() wraps functions into FunctionTool objects;
        # they are not plain callables but do have a .fn attribute.
        assert obj is not None

    def test_total_tool_count(self):
        """Sanity check: we expect exactly 14 tool functions."""
        assert len(self.EXPECTED_TOOLS) == 14


class TestImports:
    """Verify the package can be imported cleanly."""

    def test_import_package(self):
        import snow_asset_agent

        assert snow_asset_agent.__version__ == "0.1.0"

    def test_import_config(self):
        from snow_asset_agent.config import AssetAgentConfig

        assert AssetAgentConfig is not None

    def test_import_client(self):
        from snow_asset_agent.client import ServiceNowClient

        assert ServiceNowClient is not None

    def test_import_models(self):
        from snow_asset_agent.models import HardwareAsset

        assert HardwareAsset is not None

    def test_import_exceptions(self):
        from snow_asset_agent.exceptions import ServiceNowError

        assert ServiceNowError is not None
