"""MCP tool: reconcile_assets_to_cis.

Compares ``alm_hardware`` records against ``cmdb_ci`` to find
assets with no matching configuration item.
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
CI_TABLE = "cmdb_ci"


def reconcile_assets_to_cis(
    *,
    model_category: str | None = None,
    limit: int = 200,
    client: ServiceNowClient | None = None,
) -> dict[str, Any]:
    """Reconcile hardware assets against CMDB CIs.

    Returns matched, unmatched-assets (no CI), and unmatched-CIs (no asset).
    """
    if limit < 1:
        return {"error": "limit must be >= 1", "error_code": "SN_VALIDATION_ERROR"}

    try:
        _client = client or ServiceNowClient(get_config())

        asset_query = f"model_category={model_category}" if model_category else ""
        assets = _client.get_records(ASSET_TABLE, query=asset_query, limit=limit)
        cis = _client.get_records(CI_TABLE, limit=limit)

        # Build lookup: CI sys_id -> CI record
        ci_by_id: dict[str, dict[str, Any]] = {}
        for ci in cis:
            sid = ci.get("sys_id")
            if sid:
                ci_by_id[sid] = ci

        matched: list[dict[str, Any]] = []
        unmatched_assets: list[dict[str, Any]] = []

        seen_ci_ids: set[str] = set()

        for asset in assets:
            ci_ref = asset.get("ci")
            # ci might be a dict with 'value' key or a plain string
            if isinstance(ci_ref, dict):
                ci_id = ci_ref.get("value") or ""
            else:
                ci_id = ci_ref or ""

            if ci_id and ci_id in ci_by_id:
                matched.append(
                    {
                        "asset_sys_id": asset.get("sys_id"),
                        "asset_tag": asset.get("asset_tag"),
                        "ci_sys_id": ci_id,
                        "ci_name": ci_by_id[ci_id].get("name"),
                    }
                )
                seen_ci_ids.add(ci_id)
            else:
                unmatched_assets.append(
                    {
                        "sys_id": asset.get("sys_id"),
                        "asset_tag": asset.get("asset_tag"),
                        "display_name": asset.get("display_name"),
                    }
                )

        unmatched_cis = [
            {"sys_id": ci.get("sys_id"), "name": ci.get("name")} for ci in cis if ci.get("sys_id") not in seen_ci_ids
        ]

        return {
            "matched": matched,
            "matched_count": len(matched),
            "unmatched_assets": unmatched_assets,
            "unmatched_assets_count": len(unmatched_assets),
            "unmatched_cis": unmatched_cis,
            "unmatched_cis_count": len(unmatched_cis),
        }
    except ServiceNowAuthError as exc:
        logger.exception("reconcile_assets_to_cis failed: auth error")
        return {"error": str(exc), "error_code": "SN_AUTH_ERROR"}
    except ServiceNowRateLimitError as exc:
        logger.exception("reconcile_assets_to_cis failed: rate limited")
        return {"error": str(exc), "error_code": "SN_RATE_LIMIT"}
    except ServiceNowError as exc:
        logger.exception("reconcile_assets_to_cis failed")
        return {"error": str(exc), "error_code": getattr(exc, 'error_code', 'SN_QUERY_ERROR') or "SN_QUERY_ERROR"}
    except Exception as exc:
        logger.exception("reconcile_assets_to_cis failed")
        return {"error": str(exc), "error_code": "SN_QUERY_ERROR"}
