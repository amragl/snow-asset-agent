"""Snow Asset Agent -- MCP server for ServiceNow Asset Management.

Provides MCP tools for lifecycle tracking, license compliance,
hardware/software inventory, and cost optimization against ServiceNow
Asset Management tables.
"""

from __future__ import annotations

from snow_asset_agent.client import ServiceNowClient
from snow_asset_agent.config import AssetAgentConfig, get_config
from snow_asset_agent.exceptions import (
    ServiceNowAPIError,
    ServiceNowAuthError,
    ServiceNowConnectionError,
    ServiceNowError,
    ServiceNowNotFoundError,
    ServiceNowPermissionError,
    ServiceNowRateLimitError,
)
from snow_asset_agent.models import (
    AssetBase,
    AssetContract,
    AssetHealthMetric,
    AssetLifecycle,
    HardwareAsset,
    SoftwareLicense,
)

__version__ = "0.1.0"
__author__ = "amragl"

__all__ = [
    "AssetAgentConfig",
    "AssetBase",
    "AssetContract",
    "AssetHealthMetric",
    "AssetLifecycle",
    "HardwareAsset",
    "ServiceNowAPIError",
    "ServiceNowAuthError",
    "ServiceNowClient",
    "ServiceNowConnectionError",
    "ServiceNowError",
    "ServiceNowNotFoundError",
    "ServiceNowPermissionError",
    "ServiceNowRateLimitError",
    "SoftwareLicense",
    "get_config",
]
