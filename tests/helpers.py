"""Test helper functions for snow-asset-agent tests.

Record factories and mock response builders used across test files.
Import as: ``from tests.helpers import make_hardware_record, ...``
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import requests

# ------------------------------------------------------------------
# HTTP mock helpers
# ------------------------------------------------------------------


def make_mock_response(
    *,
    status_code: int = 200,
    json_data: Any = None,
    text: str = "",
    ok: bool | None = None,
) -> MagicMock:
    """Build a ``requests.Response``-like mock."""
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    resp.ok = ok if ok is not None else (200 <= status_code < 400)
    resp.text = text or ""
    resp.json.return_value = json_data if json_data is not None else {"result": []}
    return resp


# ------------------------------------------------------------------
# Sample ServiceNow records
# ------------------------------------------------------------------


def make_hardware_record(**overrides: Any) -> dict[str, Any]:
    """Factory for a realistic ``alm_hardware`` record."""
    base: dict[str, Any] = {
        "sys_id": "abc123",
        "asset_tag": "P1000479",
        "display_name": "Dell Latitude 5520",
        "model": "Latitude 5520",
        "model_category": "Computer",
        "serial_number": "SN12345",
        "assigned_to": "John Doe",
        "location": "New York",
        "install_status": "In use",
        "substatus": "In use",
        "cost": "1200.00",
        "purchase_date": "2023-06-15",
        "warranty_expiration": "2026-06-15",
        "ci": "ci_sys_001",
        "sys_updated_on": "2025-12-01 10:00:00",
    }
    base.update(overrides)
    return base


def make_license_record(**overrides: Any) -> dict[str, Any]:
    """Factory for a realistic ``alm_license`` record."""
    base: dict[str, Any] = {
        "sys_id": "lic001",
        "asset_tag": "L2000100",
        "display_name": "Microsoft Office 365 E3",
        "software_model": "Office 365 E3",
        "vendor": "Microsoft",
        "license_key": "XXXXX-XXXXX",
        "rights": "100",
        "allocated": "85",
        "cost": "3600.00",
        "start_date": "2024-01-01",
        "end_date": "2025-12-31",
        "sys_updated_on": "2025-11-01 08:00:00",
    }
    base.update(overrides)
    return base


def make_contract_record(**overrides: Any) -> dict[str, Any]:
    """Factory for a realistic ``ast_contract`` record."""
    base: dict[str, Any] = {
        "sys_id": "con001",
        "number": "CNT0001234",
        "short_description": "Annual hardware support",
        "vendor": "Dell",
        "starts": "2024-01-01",
        "ends": "2025-12-31",
        "cost": "5000.00",
        "payment_amount": "416.67",
        "state": "Active",
        "sys_updated_on": "2025-10-01 12:00:00",
    }
    base.update(overrides)
    return base


def make_ci_record(**overrides: Any) -> dict[str, Any]:
    """Factory for a realistic ``cmdb_ci`` record."""
    base: dict[str, Any] = {
        "sys_id": "ci_sys_001",
        "name": "dell-lat-5520-jdoe",
        "asset": "abc123",
        "serial_number": "SN12345",
        "ip_address": "10.0.0.42",
    }
    base.update(overrides)
    return base
