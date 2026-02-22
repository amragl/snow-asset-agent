"""MCP tool: find_expiring_contracts.

Finds asset contracts expiring within a configurable number of days,
categorised by urgency level.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from snow_asset_agent.client import ServiceNowClient
from snow_asset_agent.config import get_config
from snow_asset_agent.exceptions import (
    ServiceNowAuthError,
    ServiceNowError,
    ServiceNowRateLimitError,
)
from snow_asset_agent.models import AssetContract

logger = logging.getLogger(__name__)

TABLE = "ast_contract"


def _urgency(days_remaining: int) -> str:
    if days_remaining < 0:
        return "expired"
    if days_remaining <= 30:
        return "critical"
    if days_remaining <= 60:
        return "warning"
    if days_remaining <= 90:
        return "notice"
    return "info"


def find_expiring_contracts(
    *,
    days_ahead: int = 90,
    vendor: str | None = None,
    include_expired: bool = False,
    limit: int = 50,
    client: ServiceNowClient | None = None,
) -> dict[str, Any]:
    """Find contracts expiring within *days_ahead* days.

    Optionally includes contracts that expired in the last 30 days
    when *include_expired* is True.
    """
    if limit < 1:
        return {"error": "limit must be >= 1", "error_code": "SN_VALIDATION_ERROR"}
    if days_ahead < 1:
        return {"error": "days_ahead must be >= 1", "error_code": "SN_VALIDATION_ERROR"}

    try:
        _client = client or ServiceNowClient(get_config())

        today = date.today()
        future = today + timedelta(days=days_ahead)
        parts: list[str] = []

        if include_expired:
            past = today - timedelta(days=30)
            parts.append(f"ends>={past.isoformat()}")
        else:
            parts.append(f"ends>={today.isoformat()}")
        parts.append(f"ends<={future.isoformat()}")

        if vendor:
            parts.append(f"vendorLIKE{vendor}")

        query = "^".join(parts)
        records = _client.get_records(TABLE, query=query, limit=limit)

        items: list[dict[str, Any]] = []
        total_value = 0.0

        for rec in records:
            contract = AssetContract.from_snow_record(rec)
            days_remaining = (contract.ends - today).days if contract.ends else None
            urgency = _urgency(days_remaining) if days_remaining is not None else "unknown"
            cost = contract.cost or 0.0
            total_value += cost

            entry = contract.model_dump(mode="json")
            entry["days_remaining"] = days_remaining
            entry["urgency"] = urgency
            items.append(entry)

        # Sort by days remaining ascending (soonest first)
        items.sort(key=lambda x: x.get("days_remaining") if x.get("days_remaining") is not None else 9999)

        return {
            "contracts": items,
            "count": len(items),
            "total_value_at_risk": round(total_value, 2),
        }
    except ServiceNowAuthError as exc:
        logger.exception("find_expiring_contracts failed: auth error")
        return {"error": str(exc), "error_code": "SN_AUTH_ERROR"}
    except ServiceNowRateLimitError as exc:
        logger.exception("find_expiring_contracts failed: rate limited")
        return {"error": str(exc), "error_code": "SN_RATE_LIMIT"}
    except ServiceNowError as exc:
        logger.exception("find_expiring_contracts failed")
        return {"error": str(exc), "error_code": getattr(exc, 'error_code', 'SN_QUERY_ERROR') or "SN_QUERY_ERROR"}
    except Exception as exc:
        logger.exception("find_expiring_contracts failed")
        return {"error": str(exc), "error_code": "SN_QUERY_ERROR"}
