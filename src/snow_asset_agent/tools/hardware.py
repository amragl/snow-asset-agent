"""MCP tool: query_hardware_assets.

Searches and filters hardware assets from the ``alm_hardware`` table.
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
from snow_asset_agent.models import HardwareAsset

logger = logging.getLogger(__name__)

TABLE = "alm_hardware"


def _build_query(
    *,
    status: str | None = None,
    department: str | None = None,
    model: str | None = None,
    model_category: str | None = None,
    assigned_to: str | None = None,
    location: str | None = None,
) -> str:
    """Build an encoded ServiceNow query string from filter parameters."""
    parts: list[str] = []
    if status:
        parts.append(f"install_status={status}")
    if department:
        parts.append(f"department={department}")
    if model:
        parts.append(f"modelLIKE{model}")
    if model_category:
        parts.append(f"model_category={model_category}")
    if assigned_to:
        parts.append(f"assigned_toLIKE{assigned_to}")
    if location:
        parts.append(f"locationLIKE{location}")
    return "^".join(parts)


def query_hardware_assets(
    *,
    status: str | None = None,
    department: str | None = None,
    model: str | None = None,
    model_category: str | None = None,
    assigned_to: str | None = None,
    location: str | None = None,
    limit: int = 50,
    client: ServiceNowClient | None = None,
) -> dict[str, Any]:
    """Query hardware assets from ServiceNow.

    Returns a dict with ``assets`` (list) and ``count`` (int).
    On error returns ``{"error": ..., "error_code": ...}``.
    """
    if limit < 1:
        return {"error": "limit must be >= 1", "error_code": "SN_VALIDATION_ERROR"}

    try:
        _client = client or ServiceNowClient(get_config())
        query = _build_query(
            status=status,
            department=department,
            model=model,
            model_category=model_category,
            assigned_to=assigned_to,
            location=location,
        )
        records = _client.get_records(TABLE, query=query, limit=limit)
        assets = [HardwareAsset.from_snow_record(r).model_dump(mode="json") for r in records]
        return {"assets": assets, "count": len(assets)}
    except ServiceNowAuthError as exc:
        logger.exception("query_hardware_assets failed: auth error")
        return {"error": str(exc), "error_code": "SN_AUTH_ERROR"}
    except ServiceNowRateLimitError as exc:
        logger.exception("query_hardware_assets failed: rate limited")
        return {"error": str(exc), "error_code": "SN_RATE_LIMIT"}
    except ServiceNowError as exc:
        logger.exception("query_hardware_assets failed")
        return {"error": str(exc), "error_code": getattr(exc, 'error_code', 'SN_QUERY_ERROR') or "SN_QUERY_ERROR"}
    except Exception as exc:
        logger.exception("query_hardware_assets failed")
        return {"error": str(exc), "error_code": "SN_QUERY_ERROR"}
