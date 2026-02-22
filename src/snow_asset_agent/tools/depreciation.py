"""MCP tool: track_asset_depreciation.

Computes straight-line depreciation for hardware assets based on
purchase date and category-specific useful-life defaults.
"""

from __future__ import annotations

import logging
from datetime import date
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

# Default useful-life (years) by model category.
DEFAULT_USEFUL_LIFE: dict[str, int] = {
    "Computer": 3,
    "Server": 5,
    "Network Gear": 5,
}
FALLBACK_USEFUL_LIFE = 4


def _safe_float(val: Any) -> float:
    if val is None or val == "":
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def _parse_date(val: Any) -> date | None:
    if not val:
        return None
    try:
        return date.fromisoformat(str(val)[:10])
    except (ValueError, TypeError):
        return None


def track_asset_depreciation(
    *,
    model_category: str | None = None,
    useful_life_years: int | None = None,
    limit: int = 100,
    client: ServiceNowClient | None = None,
) -> dict[str, Any]:
    """Calculate accumulated depreciation for hardware assets.

    Uses straight-line depreciation: ``annual = cost / useful_life``.
    """
    if limit < 1:
        return {"error": "limit must be >= 1", "error_code": "SN_VALIDATION_ERROR"}

    try:
        _client = client or ServiceNowClient(get_config())

        query = f"model_category={model_category}" if model_category else ""
        records = _client.get_records(TABLE, query=query, limit=limit)

        today = date.today()
        items: list[dict[str, Any]] = []
        total_depreciation = 0.0

        for rec in records:
            cost = _safe_float(rec.get("cost"))
            purchase_date = _parse_date(rec.get("purchase_date"))

            if purchase_date is None or cost <= 0:
                continue

            cat = rec.get("model_category", "")
            if isinstance(cat, dict):
                cat = cat.get("display_value", "")
            life = useful_life_years or DEFAULT_USEFUL_LIFE.get(cat, FALLBACK_USEFUL_LIFE)
            years_owned = (today - purchase_date).days / 365.25
            annual_dep = cost / life
            accumulated = min(cost, annual_dep * years_owned)
            current_value = max(0.0, cost - accumulated)
            remaining_life = max(0.0, life - years_owned)

            total_depreciation += accumulated
            items.append(
                {
                    "sys_id": rec.get("sys_id"),
                    "asset_tag": rec.get("asset_tag"),
                    "cost": round(cost, 2),
                    "purchase_date": purchase_date.isoformat(),
                    "useful_life_years": life,
                    "years_owned": round(years_owned, 2),
                    "annual_depreciation": round(annual_dep, 2),
                    "accumulated_depreciation": round(accumulated, 2),
                    "current_value": round(current_value, 2),
                    "remaining_useful_life_years": round(remaining_life, 2),
                }
            )

        return {
            "assets": items,
            "count": len(items),
            "total_accumulated_depreciation": round(total_depreciation, 2),
        }
    except ServiceNowAuthError as exc:
        logger.exception("track_asset_depreciation failed: auth error")
        return {"error": str(exc), "error_code": "SN_AUTH_ERROR"}
    except ServiceNowRateLimitError as exc:
        logger.exception("track_asset_depreciation failed: rate limited")
        return {"error": str(exc), "error_code": "SN_RATE_LIMIT"}
    except ServiceNowError as exc:
        logger.exception("track_asset_depreciation failed")
        return {"error": str(exc), "error_code": getattr(exc, 'error_code', 'SN_QUERY_ERROR') or "SN_QUERY_ERROR"}
    except Exception as exc:
        logger.exception("track_asset_depreciation failed")
        return {"error": str(exc), "error_code": "SN_QUERY_ERROR"}
