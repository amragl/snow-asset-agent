"""MCP tool: check_license_compliance.

Compares installed software counts against licensed entitlements
to identify over-allocated or under-utilised licences.
"""

from __future__ import annotations

import logging
from typing import Any

from snow_asset_agent.client import ServiceNowClient
from snow_asset_agent.config import get_config

logger = logging.getLogger(__name__)

LICENSE_TABLE = "alm_license"


def check_license_compliance(
    *,
    product: str | None = None,
    vendor: str | None = None,
    limit: int = 100,
    client: ServiceNowClient | None = None,
) -> dict[str, Any]:
    """Check software licence compliance.

    Compares ``rights`` (entitlements) against ``allocated`` for each
    licence record and categorises as compliant, over-allocated, or
    under-utilised.
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

        results: list[dict[str, Any]] = []
        compliant = 0
        non_compliant = 0
        under_utilised = 0

        for rec in records:
            rights = _safe_int(rec.get("rights"))
            allocated = _safe_int(rec.get("allocated"))

            if rights == 0:
                status = "unknown"
            elif allocated > rights:
                status = "over-allocated"
                non_compliant += 1
            elif allocated < rights * 0.5:
                status = "under-utilised"
                under_utilised += 1
                compliant += 1
            else:
                status = "compliant"
                compliant += 1

            gap = allocated - rights

            results.append(
                {
                    "sys_id": rec.get("sys_id"),
                    "product": rec.get("software_model")
                    if isinstance(rec.get("software_model"), str)
                    else (rec.get("software_model", {}) or {}).get("display_value"),
                    "rights": rights,
                    "allocated": allocated,
                    "gap": gap,
                    "status": status,
                }
            )

        return {
            "compliance_results": results,
            "count": len(results),
            "compliant": compliant,
            "non_compliant": non_compliant,
            "under_utilised": under_utilised,
        }
    except Exception as exc:
        logger.exception("check_license_compliance failed")
        return {"error": str(exc), "error_code": "SN_QUERY_ERROR"}


def _safe_int(val: Any) -> int:
    if val is None or val == "":
        return 0
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0
