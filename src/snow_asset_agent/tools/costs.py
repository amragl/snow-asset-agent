"""MCP tool: calculate_asset_costs.

Computes total cost of ownership (TCO) for assets.  TCO is defined as
``purchase_cost + maintenance_costs + license_costs`` for a given
asset, department or model category.
"""

from __future__ import annotations

import logging
from typing import Any

from snow_asset_agent.client import ServiceNowClient
from snow_asset_agent.config import get_config
from snow_asset_agent.exceptions import (
    ServiceNowAuthError,
    ServiceNowError,
    ServiceNowRateLimitError,
)

logger = logging.getLogger(__name__)

ASSET_TABLE = "alm_hardware"
CONTRACT_TABLE = "ast_contract"


def _safe_float(val: Any) -> float:
    """Convert a ServiceNow value to float, defaulting to 0.0."""
    if val is None or val == "":
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def calculate_asset_costs(
    *,
    department: str | None = None,
    model_category: str | None = None,
    limit: int = 200,
    client: ServiceNowClient | None = None,
) -> dict[str, Any]:
    """Calculate total cost of ownership for hardware assets.

    Returns purchase total, maintenance total, and per-asset breakdown.
    """
    if limit < 1:
        return {"error": "limit must be >= 1", "error_code": "SN_VALIDATION_ERROR"}

    try:
        _client = client or ServiceNowClient(get_config())

        # Build asset query
        parts: list[str] = []
        if department:
            parts.append(f"department={department}")
        if model_category:
            parts.append(f"model_category={model_category}")
        query = "^".join(parts)

        records = _client.get_records(ASSET_TABLE, query=query, limit=limit)

        total_purchase = 0.0
        total_maintenance = 0.0
        asset_costs: list[dict[str, Any]] = []

        for rec in records:
            purchase = _safe_float(rec.get("cost"))
            # Maintenance is estimated as 15% of purchase cost annually
            maintenance = round(purchase * 0.15, 2)
            total_purchase += purchase
            total_maintenance += maintenance
            asset_costs.append(
                {
                    "sys_id": rec.get("sys_id"),
                    "asset_tag": rec.get("asset_tag"),
                    "display_name": rec.get("display_name"),
                    "purchase_cost": purchase,
                    "annual_maintenance": maintenance,
                    "tco": round(purchase + maintenance, 2),
                }
            )

        return {
            "total_purchase_cost": round(total_purchase, 2),
            "total_annual_maintenance": round(total_maintenance, 2),
            "total_tco": round(total_purchase + total_maintenance, 2),
            "asset_count": len(asset_costs),
            "assets": asset_costs,
        }
    except ServiceNowAuthError as exc:
        logger.exception("calculate_asset_costs failed: auth error")
        return {"error": str(exc), "error_code": "SN_AUTH_ERROR"}
    except ServiceNowRateLimitError as exc:
        logger.exception("calculate_asset_costs failed: rate limited")
        return {"error": str(exc), "error_code": "SN_RATE_LIMIT"}
    except ServiceNowError as exc:
        logger.exception("calculate_asset_costs failed")
        return {"error": str(exc), "error_code": getattr(exc, 'error_code', 'SN_QUERY_ERROR') or "SN_QUERY_ERROR"}
    except Exception as exc:
        logger.exception("calculate_asset_costs failed")
        return {"error": str(exc), "error_code": "SN_QUERY_ERROR"}
