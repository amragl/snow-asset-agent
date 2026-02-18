"""MCP tool: get_asset_lifecycle.

Returns lifecycle stage information for an asset, including how long
the asset has been in its current stage.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

from snow_asset_agent.client import ServiceNowClient
from snow_asset_agent.config import get_config
from snow_asset_agent.models import AssetLifecycle

logger = logging.getLogger(__name__)

TABLE = "alm_asset"

# Map ServiceNow install_status to human-readable lifecycle stages.
STAGE_MAP: dict[str, str] = {
    "On order": "Procurement",
    "In stock": "Received/Stocked",
    "In transit": "In Transit",
    "Installed": "Active/Deployed",
    "In use": "Active/Deployed",
    "In maintenance": "Maintenance",
    "Retired": "Retired",
    "Missing": "Missing",
    "Disposed": "Disposed",
    "Absent": "Missing",
}


def _days_since(date_str: str | None) -> int | None:
    """Return number of days since a ServiceNow date string, or None."""
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        return (date.today() - dt).days
    except (ValueError, TypeError):
        return None


def get_asset_lifecycle(
    *,
    sys_id: str | None = None,
    asset_tag: str | None = None,
    client: ServiceNowClient | None = None,
) -> dict[str, Any]:
    """Return lifecycle stage and duration for an asset."""
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

        install_status = record.get("install_status", "")
        stage = STAGE_MAP.get(install_status, install_status or "Unknown")
        days_in_stage = _days_since(record.get("sys_updated_on"))
        lifecycle = AssetLifecycle.from_snow_record(record, stage=stage, days_in_stage=days_in_stage)
        return {"lifecycle": lifecycle.model_dump(mode="json")}
    except Exception as exc:
        logger.exception("get_asset_lifecycle failed")
        return {"error": str(exc), "error_code": "SN_QUERY_ERROR"}
