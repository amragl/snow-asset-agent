"""MCP tool: get_asset_contracts.

Retrieves contracts linked to an asset from the ``ast_contract`` table.
"""

from __future__ import annotations

import logging
from typing import Any

from snow_asset_agent.client import ServiceNowClient
from snow_asset_agent.config import get_config
from snow_asset_agent.models import AssetContract

logger = logging.getLogger(__name__)

TABLE = "ast_contract"


def _build_query(
    *,
    asset_sys_id: str | None = None,
    vendor: str | None = None,
    state: str | None = None,
) -> str:
    parts: list[str] = []
    if asset_sys_id:
        parts.append(f"asset={asset_sys_id}")
    if vendor:
        parts.append(f"vendorLIKE{vendor}")
    if state:
        parts.append(f"state={state}")
    return "^".join(parts)


def get_asset_contracts(
    *,
    asset_sys_id: str | None = None,
    vendor: str | None = None,
    state: str | None = None,
    limit: int = 50,
    client: ServiceNowClient | None = None,
) -> dict[str, Any]:
    """Fetch contracts from ServiceNow, optionally filtered by asset/vendor/state."""
    if limit < 1:
        return {"error": "limit must be >= 1", "error_code": "SN_VALIDATION_ERROR"}

    try:
        _client = client or ServiceNowClient(get_config())
        query = _build_query(asset_sys_id=asset_sys_id, vendor=vendor, state=state)
        records = _client.get_records(TABLE, query=query, limit=limit)
        contracts = [AssetContract.from_snow_record(r).model_dump(mode="json") for r in records]
        return {"contracts": contracts, "count": len(contracts)}
    except Exception as exc:
        logger.exception("get_asset_contracts failed")
        return {"error": str(exc), "error_code": "SN_QUERY_ERROR"}
