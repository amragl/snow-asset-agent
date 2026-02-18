"""MCP tool: get_asset_health_metrics.

Returns an aggregate health dashboard: counts of assets by status,
overdue items, and expiring contracts.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from snow_asset_agent.client import ServiceNowClient
from snow_asset_agent.config import get_config
from snow_asset_agent.models import AssetHealthMetric

logger = logging.getLogger(__name__)

ASSET_TABLE = "alm_asset"
CONTRACT_TABLE = "ast_contract"


def _safe_float(val: Any) -> float:
    if val is None or val == "":
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def get_asset_health_metrics(
    *,
    location: str | None = None,
    model_category: str | None = None,
    client: ServiceNowClient | None = None,
) -> dict[str, Any]:
    """Return aggregate asset health metrics."""
    try:
        _client = client or ServiceNowClient(get_config())

        # Build base query for scoping
        parts: list[str] = []
        if location:
            parts.append(f"locationLIKE{location}")
        if model_category:
            parts.append(f"model_category={model_category}")
        base_q = "^".join(parts)

        all_assets = _client.get_records(ASSET_TABLE, query=base_q, limit=500)

        total = len(all_assets)
        active = 0
        retired = 0
        missing = 0
        in_stock = 0
        total_value = 0.0

        for a in all_assets:
            status = (a.get("install_status") or "").lower()
            if status in ("in use", "installed"):
                active += 1
            elif status == "retired":
                retired += 1
            elif status == "missing":
                missing += 1
            elif status == "in stock":
                in_stock += 1
            total_value += _safe_float(a.get("cost"))

        # Expiring contracts within 30 days
        today = date.today().isoformat()
        future30 = (date.today() + timedelta(days=30)).isoformat()
        contract_q = f"ends>={today}^ends<={future30}"
        expiring = _client.get_records(CONTRACT_TABLE, query=contract_q, limit=500)

        metrics = AssetHealthMetric(
            total_assets=total,
            active_assets=active,
            retired_assets=retired,
            missing_assets=missing,
            in_stock_assets=in_stock,
            expiring_contracts_30d=len(expiring),
            total_asset_value=round(total_value, 2),
        )
        return {"metrics": metrics.model_dump(mode="json")}
    except Exception as exc:
        logger.exception("get_asset_health_metrics failed")
        return {"error": str(exc), "error_code": "SN_QUERY_ERROR"}
