"""MCP tool: get_license_utilization.

Calculates usage/entitlement ratios for software licences.
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

LICENSE_TABLE = "alm_license"


def _safe_int(val: Any) -> int:
    if val is None or val == "":
        return 0
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def get_license_utilization(
    *,
    product: str | None = None,
    vendor: str | None = None,
    limit: int = 50,
    client: ServiceNowClient | None = None,
) -> dict[str, Any]:
    """Return licence utilisation metrics (used/total seats).

    Each licence entry includes a ``utilization_pct`` field.
    """
    if limit < 1:
        return {"error": "limit must be >= 1", "error_code": "SN_VALIDATION_ERROR"}

    try:
        _client = client or ServiceNowClient(get_config())

        parts: list[str] = []
        if product:
            parts.append(f"software_modelLIKE{product}")
        if vendor:
            parts.append(f"vendorLIKE{vendor}")
        query = "^".join(parts)

        records = _client.get_records(LICENSE_TABLE, query=query, limit=limit)

        items: list[dict[str, Any]] = []
        for rec in records:
            rights = _safe_int(rec.get("rights"))
            allocated = _safe_int(rec.get("allocated"))
            utilization_pct = round((allocated / rights) * 100, 1) if rights > 0 else 0.0

            items.append(
                {
                    "sys_id": rec.get("sys_id"),
                    "product": rec.get("software_model")
                    if isinstance(rec.get("software_model"), str)
                    else (rec.get("software_model", {}) or {}).get("display_value"),
                    "rights": rights,
                    "allocated": allocated,
                    "utilization_pct": utilization_pct,
                }
            )

        # Sort by utilization descending
        items.sort(key=lambda x: x["utilization_pct"], reverse=True)

        return {"utilization": items, "count": len(items)}
    except ServiceNowAuthError as exc:
        logger.exception("get_license_utilization failed: auth error")
        return {"error": str(exc), "error_code": "SN_AUTH_ERROR"}
    except ServiceNowRateLimitError as exc:
        logger.exception("get_license_utilization failed: rate limited")
        return {"error": str(exc), "error_code": "SN_RATE_LIMIT"}
    except ServiceNowError as exc:
        logger.exception("get_license_utilization failed")
        return {"error": str(exc), "error_code": getattr(exc, 'error_code', 'SN_QUERY_ERROR') or "SN_QUERY_ERROR"}
    except Exception as exc:
        logger.exception("get_license_utilization failed")
        return {"error": str(exc), "error_code": "SN_QUERY_ERROR"}
