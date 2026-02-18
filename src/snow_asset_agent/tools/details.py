"""MCP tool: get_asset_details.

Retrieves full details for a single asset by ``sys_id`` or ``asset_tag``.
"""

from __future__ import annotations

import logging
from typing import Any

from snow_asset_agent.client import ServiceNowClient
from snow_asset_agent.config import get_config
from snow_asset_agent.models import AssetBase

logger = logging.getLogger(__name__)

TABLE = "alm_asset"


def get_asset_details(
    *,
    sys_id: str | None = None,
    asset_tag: str | None = None,
    client: ServiceNowClient | None = None,
) -> dict[str, Any]:
    """Return full asset record from the ``alm_asset`` table.

    At least one of *sys_id* or *asset_tag* must be provided.
    """
    if not sys_id and not asset_tag:
        return {"error": "Provide either sys_id or asset_tag", "error_code": "SN_VALIDATION_ERROR"}

    try:
        _client = client or ServiceNowClient(get_config())

        if sys_id:
            record = _client.get_record(TABLE, sys_id)
        else:
            records = _client.get_records(TABLE, query=f"asset_tag={asset_tag}", limit=1)
            if not records:
                return {"error": f"Asset not found: asset_tag={asset_tag}", "error_code": "SN_NOT_FOUND"}
            record = records[0]

        asset = AssetBase.from_snow_record(record).model_dump(mode="json")
        return {"asset": asset}
    except Exception as exc:
        logger.exception("get_asset_details failed")
        return {"error": str(exc), "error_code": "SN_QUERY_ERROR"}
