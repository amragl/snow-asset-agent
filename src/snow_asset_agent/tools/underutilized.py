"""MCP tool: find_underutilized_assets.

Identifies hardware assets that appear inactive (not updated within a
configurable threshold of days) or are unassigned while marked as "in use".
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from snow_asset_agent.client import ServiceNowClient
from snow_asset_agent.config import get_config
from snow_asset_agent.exceptions import (
    ServiceNowAuthError,
    ServiceNowError,
    ServiceNowRateLimitError,
)

logger = logging.getLogger(__name__)

TABLE = "alm_hardware"


def _safe_float(val: Any) -> float:
    if val is None or val == "":
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def find_underutilized_assets(
    *,
    days_threshold: int = 90,
    limit: int = 50,
    client: ServiceNowClient | None = None,
) -> dict[str, Any]:
    """Find hardware assets whose ``sys_updated_on`` is older than
    *days_threshold* days or that have no ``assigned_to`` while
    marked as in-use.
    """
    if limit < 1:
        return {"error": "limit must be >= 1", "error_code": "SN_VALIDATION_ERROR"}
    if days_threshold < 1:
        return {"error": "days_threshold must be >= 1", "error_code": "SN_VALIDATION_ERROR"}

    try:
        _client = client or ServiceNowClient(get_config())

        cutoff = (date.today() - timedelta(days=days_threshold)).isoformat()
        # Assets marked in-use but not updated recently
        query = f"install_statusINIn use,Installed^sys_updated_on<{cutoff}"
        records = _client.get_records(TABLE, query=query, limit=limit)

        items: list[dict[str, Any]] = []
        total_waste = 0.0

        for rec in records:
            cost = _safe_float(rec.get("cost"))
            assigned = rec.get("assigned_to")
            reason = "inactive"
            if not assigned or assigned == "":
                reason = "unassigned"

            total_waste += cost
            items.append(
                {
                    "sys_id": rec.get("sys_id"),
                    "asset_tag": rec.get("asset_tag"),
                    "display_name": rec.get("display_name"),
                    "install_status": rec.get("install_status"),
                    "assigned_to": assigned,
                    "sys_updated_on": rec.get("sys_updated_on"),
                    "cost": round(cost, 2),
                    "reason": reason,
                }
            )

        return {
            "underutilized_assets": items,
            "count": len(items),
            "estimated_waste_cost": round(total_waste, 2),
        }
    except ServiceNowAuthError as exc:
        logger.exception("find_underutilized_assets failed: auth error")
        return {"error": str(exc), "error_code": "SN_AUTH_ERROR"}
    except ServiceNowRateLimitError as exc:
        logger.exception("find_underutilized_assets failed: rate limited")
        return {"error": str(exc), "error_code": "SN_RATE_LIMIT"}
    except ServiceNowError as exc:
        logger.exception("find_underutilized_assets failed")
        return {"error": str(exc), "error_code": getattr(exc, 'error_code', 'SN_QUERY_ERROR') or "SN_QUERY_ERROR"}
    except Exception as exc:
        logger.exception("find_underutilized_assets failed")
        return {"error": str(exc), "error_code": "SN_QUERY_ERROR"}
