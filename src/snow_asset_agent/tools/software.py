"""MCP tool: query_software_licenses.

Searches and filters software licenses from the ``alm_license`` table.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from snow_asset_agent.client import ServiceNowClient
from snow_asset_agent.config import get_config
from snow_asset_agent.models import SoftwareLicense

logger = logging.getLogger(__name__)

TABLE = "alm_license"


def _build_query(
    *,
    vendor: str | None = None,
    product: str | None = None,
    expiring_soon: int | None = None,
) -> str:
    """Build an encoded ServiceNow query string."""
    parts: list[str] = []
    if vendor:
        parts.append(f"vendorLIKE{vendor}")
    if product:
        parts.append(f"software_modelLIKE{product}")
    if expiring_soon is not None and expiring_soon > 0:
        today = date.today().isoformat()
        future = (date.today() + timedelta(days=expiring_soon)).isoformat()
        parts.append(f"end_date>={today}")
        parts.append(f"end_date<={future}")
    return "^".join(parts)


def query_software_licenses(
    *,
    vendor: str | None = None,
    product: str | None = None,
    expiring_soon: int | None = None,
    limit: int = 50,
    client: ServiceNowClient | None = None,
) -> dict[str, Any]:
    """Query software licenses from ServiceNow.

    Returns ``{"licenses": [...], "count": N}``.
    """
    if limit < 1:
        return {"error": "limit must be >= 1", "error_code": "SN_VALIDATION_ERROR"}

    try:
        _client = client or ServiceNowClient(get_config())
        query = _build_query(vendor=vendor, product=product, expiring_soon=expiring_soon)
        records = _client.get_records(TABLE, query=query, limit=limit)
        licenses = [SoftwareLicense.from_snow_record(r).model_dump(mode="json") for r in records]
        return {"licenses": licenses, "count": len(licenses)}
    except Exception as exc:
        logger.exception("query_software_licenses failed")
        return {"error": str(exc), "error_code": "SN_QUERY_ERROR"}
