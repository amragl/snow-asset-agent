"""FastMCP server entry point for snow-asset-agent.

Registers all 13 asset-management tools plus a health-check endpoint.
Start with: ``python -m snow_asset_agent``
"""

from __future__ import annotations

import logging
from typing import Any

from fastmcp import FastMCP

from snow_asset_agent.client import ServiceNowClient
from snow_asset_agent.config import get_config
from snow_asset_agent.tools.compliance import check_license_compliance
from snow_asset_agent.tools.contracts import get_asset_contracts
from snow_asset_agent.tools.costs import calculate_asset_costs
from snow_asset_agent.tools.depreciation import track_asset_depreciation
from snow_asset_agent.tools.details import get_asset_details
from snow_asset_agent.tools.expiring import find_expiring_contracts
from snow_asset_agent.tools.hardware import query_hardware_assets
from snow_asset_agent.tools.health import get_asset_health_metrics
from snow_asset_agent.tools.lifecycle import get_asset_lifecycle
from snow_asset_agent.tools.reconcile import reconcile_assets_to_cis
from snow_asset_agent.tools.software import query_software_licenses
from snow_asset_agent.tools.underutilized import find_underutilized_assets
from snow_asset_agent.tools.utilization import get_license_utilization

logger = logging.getLogger(__name__)

mcp = FastMCP("snow-asset-agent")


# ------------------------------------------------------------------
# Health check
# ------------------------------------------------------------------


@mcp.tool()
def health_check() -> dict[str, Any]:
    """Verify connectivity to the ServiceNow instance.

    Returns server version, instance URL, connection status, and
    response time.
    """
    from snow_asset_agent import __version__

    cfg = get_config()
    client = ServiceNowClient(cfg)
    ping = client.ping()
    return {
        "server": "snow-asset-agent",
        "version": __version__,
        "instance": cfg.servicenow_instance,
        **ping,
    }


# ------------------------------------------------------------------
# Hardware / Software queries
# ------------------------------------------------------------------


@mcp.tool()
def tool_query_hardware_assets(
    status: str | None = None,
    department: str | None = None,
    model: str | None = None,
    model_category: str | None = None,
    assigned_to: str | None = None,
    location: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Search and filter hardware assets from the alm_hardware table."""
    return query_hardware_assets(
        status=status,
        department=department,
        model=model,
        model_category=model_category,
        assigned_to=assigned_to,
        location=location,
        limit=limit,
    )


@mcp.tool()
def tool_query_software_licenses(
    vendor: str | None = None,
    product: str | None = None,
    expiring_soon: int | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Search and filter software licenses from the alm_license table."""
    return query_software_licenses(
        vendor=vendor,
        product=product,
        expiring_soon=expiring_soon,
        limit=limit,
    )


# ------------------------------------------------------------------
# Detail / Lifecycle / Contracts
# ------------------------------------------------------------------


@mcp.tool()
def tool_get_asset_details(
    sys_id: str | None = None,
    asset_tag: str | None = None,
) -> dict[str, Any]:
    """Get full details for a single asset by sys_id or asset_tag."""
    return get_asset_details(sys_id=sys_id, asset_tag=asset_tag)


@mcp.tool()
def tool_get_asset_lifecycle(
    sys_id: str | None = None,
    asset_tag: str | None = None,
) -> dict[str, Any]:
    """Get lifecycle stage and duration for an asset."""
    return get_asset_lifecycle(sys_id=sys_id, asset_tag=asset_tag)


@mcp.tool()
def tool_get_asset_contracts(
    asset_sys_id: str | None = None,
    vendor: str | None = None,
    state: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Get contracts linked to an asset or filtered by vendor/state."""
    return get_asset_contracts(
        asset_sys_id=asset_sys_id,
        vendor=vendor,
        state=state,
        limit=limit,
    )


# ------------------------------------------------------------------
# Financial / Compliance
# ------------------------------------------------------------------


@mcp.tool()
def tool_calculate_asset_costs(
    department: str | None = None,
    model_category: str | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    """Calculate total cost of ownership for hardware assets."""
    return calculate_asset_costs(
        department=department,
        model_category=model_category,
        limit=limit,
    )


@mcp.tool()
def tool_check_license_compliance(
    product: str | None = None,
    vendor: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Check software licence compliance (installed vs licensed)."""
    return check_license_compliance(
        product=product,
        vendor=vendor,
        limit=limit,
    )


@mcp.tool()
def tool_get_license_utilization(
    product: str | None = None,
    vendor: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Get licence utilisation metrics (used/total seats per product)."""
    return get_license_utilization(
        product=product,
        vendor=vendor,
        limit=limit,
    )


@mcp.tool()
def tool_track_asset_depreciation(
    model_category: str | None = None,
    useful_life_years: int | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Calculate depreciation for hardware assets (straight-line method)."""
    return track_asset_depreciation(
        model_category=model_category,
        useful_life_years=useful_life_years,
        limit=limit,
    )


# ------------------------------------------------------------------
# Analytics / Reconciliation
# ------------------------------------------------------------------


@mcp.tool()
def tool_find_underutilized_assets(
    days_threshold: int = 90,
    limit: int = 50,
) -> dict[str, Any]:
    """Find hardware assets with low or no recent activity."""
    return find_underutilized_assets(days_threshold=days_threshold, limit=limit)


@mcp.tool()
def tool_reconcile_assets_to_cis(
    model_category: str | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    """Reconcile hardware assets against CMDB configuration items."""
    return reconcile_assets_to_cis(model_category=model_category, limit=limit)


@mcp.tool()
def tool_get_asset_health_metrics(
    location: str | None = None,
    model_category: str | None = None,
) -> dict[str, Any]:
    """Get aggregate asset health dashboard metrics."""
    return get_asset_health_metrics(
        location=location,
        model_category=model_category,
    )


@mcp.tool()
def tool_find_expiring_contracts(
    days_ahead: int = 90,
    vendor: str | None = None,
    include_expired: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    """Find contracts expiring within N days, categorised by urgency."""
    return find_expiring_contracts(
        days_ahead=days_ahead,
        vendor=vendor,
        include_expired=include_expired,
        limit=limit,
    )
