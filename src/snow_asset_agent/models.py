"""Pydantic v2 models for ServiceNow Asset Management records.

Every model uses ``Optional`` fields so that partially-populated
ServiceNow records can be represented without validation errors.
Each model exposes a ``from_snow_record`` classmethod that accepts
a raw ``dict`` from the ServiceNow REST API and returns a model
instance.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_date(value: Any) -> date | None:
    """Best-effort parse of a ServiceNow date string."""
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _parse_float(value: Any) -> float | None:
    """Best-effort parse of a numeric string from ServiceNow."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _parse_int(value: Any) -> int | None:
    """Best-effort parse of an integer string from ServiceNow."""
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class AssetBase(BaseModel):
    """Minimal fields shared by all asset types."""

    sys_id: str | None = None
    asset_tag: str | None = None
    display_name: str | None = None
    model: str | None = None
    model_category: str | None = None
    install_status: str | None = None
    substatus: str | None = None
    assigned_to: str | None = None
    location: str | None = None
    cost: float | None = None
    purchase_date: date | None = None
    sys_created_on: str | None = None
    sys_updated_on: str | None = None

    @classmethod
    def from_snow_record(cls, record: dict[str, Any]) -> AssetBase:
        return cls(
            sys_id=record.get("sys_id"),
            asset_tag=record.get("asset_tag"),
            display_name=record.get("display_name"),
            model=record.get("model", {}).get("display_value")
            if isinstance(record.get("model"), dict)
            else record.get("model"),
            model_category=record.get("model_category", {}).get("display_value")
            if isinstance(record.get("model_category"), dict)
            else record.get("model_category"),
            install_status=record.get("install_status"),
            substatus=record.get("substatus"),
            assigned_to=record.get("assigned_to", {}).get("display_value")
            if isinstance(record.get("assigned_to"), dict)
            else record.get("assigned_to"),
            location=record.get("location", {}).get("display_value")
            if isinstance(record.get("location"), dict)
            else record.get("location"),
            cost=_parse_float(record.get("cost")),
            purchase_date=_parse_date(record.get("purchase_date")),
            sys_created_on=record.get("sys_created_on"),
            sys_updated_on=record.get("sys_updated_on"),
        )


# ---------------------------------------------------------------------------
# Hardware
# ---------------------------------------------------------------------------


class HardwareAsset(BaseModel):
    """Represents a record from the ``alm_hardware`` table."""

    sys_id: str | None = None
    asset_tag: str | None = None
    display_name: str | None = None
    model: str | None = None
    model_category: str | None = None
    serial_number: str | None = None
    assigned_to: str | None = None
    location: str | None = None
    install_status: str | None = None
    substatus: str | None = None
    cost: float | None = None
    purchase_date: date | None = None
    warranty_expiration: date | None = None
    ci: str | None = None
    sys_updated_on: str | None = None

    @classmethod
    def from_snow_record(cls, record: dict[str, Any]) -> HardwareAsset:
        return cls(
            sys_id=record.get("sys_id"),
            asset_tag=record.get("asset_tag"),
            display_name=record.get("display_name"),
            model=record.get("model", {}).get("display_value")
            if isinstance(record.get("model"), dict)
            else record.get("model"),
            model_category=record.get("model_category", {}).get("display_value")
            if isinstance(record.get("model_category"), dict)
            else record.get("model_category"),
            serial_number=record.get("serial_number"),
            assigned_to=record.get("assigned_to", {}).get("display_value")
            if isinstance(record.get("assigned_to"), dict)
            else record.get("assigned_to"),
            location=record.get("location", {}).get("display_value")
            if isinstance(record.get("location"), dict)
            else record.get("location"),
            install_status=record.get("install_status"),
            substatus=record.get("substatus"),
            cost=_parse_float(record.get("cost")),
            purchase_date=_parse_date(record.get("purchase_date")),
            warranty_expiration=_parse_date(record.get("warranty_expiration")),
            ci=record.get("ci", {}).get("value") if isinstance(record.get("ci"), dict) else record.get("ci"),
            sys_updated_on=record.get("sys_updated_on"),
        )


# ---------------------------------------------------------------------------
# Software License
# ---------------------------------------------------------------------------


class SoftwareLicense(BaseModel):
    """Represents a record from the ``alm_license`` table."""

    sys_id: str | None = None
    asset_tag: str | None = None
    display_name: str | None = None
    product: str | None = None
    vendor: str | None = None
    license_key: str | None = None
    rights: int | None = None
    allocated: int | None = None
    cost: float | None = None
    start_date: date | None = None
    end_date: date | None = None
    sys_updated_on: str | None = None

    @classmethod
    def from_snow_record(cls, record: dict[str, Any]) -> SoftwareLicense:
        return cls(
            sys_id=record.get("sys_id"),
            asset_tag=record.get("asset_tag"),
            display_name=record.get("display_name"),
            product=record.get("software_model", {}).get("display_value")
            if isinstance(record.get("software_model"), dict)
            else record.get("software_model"),
            vendor=record.get("vendor", {}).get("display_value")
            if isinstance(record.get("vendor"), dict)
            else record.get("vendor"),
            license_key=record.get("license_key"),
            rights=_parse_int(record.get("rights")),
            allocated=_parse_int(record.get("allocated")),
            cost=_parse_float(record.get("cost")),
            start_date=_parse_date(record.get("start_date")),
            end_date=_parse_date(record.get("end_date")),
            sys_updated_on=record.get("sys_updated_on"),
        )


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------


class AssetContract(BaseModel):
    """Represents a record from the ``ast_contract`` table."""

    sys_id: str | None = None
    contract_number: str | None = None
    short_description: str | None = None
    vendor: str | None = None
    starts: date | None = None
    ends: date | None = None
    cost: float | None = None
    payment_amount: float | None = None
    state: str | None = None
    sys_updated_on: str | None = None

    @classmethod
    def from_snow_record(cls, record: dict[str, Any]) -> AssetContract:
        return cls(
            sys_id=record.get("sys_id"),
            contract_number=record.get("number"),
            short_description=record.get("short_description"),
            vendor=record.get("vendor", {}).get("display_value")
            if isinstance(record.get("vendor"), dict)
            else record.get("vendor"),
            starts=_parse_date(record.get("starts")),
            ends=_parse_date(record.get("ends")),
            cost=_parse_float(record.get("cost")),
            payment_amount=_parse_float(record.get("payment_amount")),
            state=record.get("state"),
            sys_updated_on=record.get("sys_updated_on"),
        )


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


class AssetLifecycle(BaseModel):
    """Lifecycle stage information for an asset."""

    sys_id: str | None = None
    asset_tag: str | None = None
    display_name: str | None = None
    stage: str | None = None
    install_status: str | None = None
    substatus: str | None = None
    install_date: date | None = None
    retired_date: date | None = None
    disposal_date: date | None = None
    sys_updated_on: str | None = None
    days_in_stage: int | None = None

    @classmethod
    def from_snow_record(
        cls, record: dict[str, Any], *, stage: str | None = None, days_in_stage: int | None = None
    ) -> AssetLifecycle:
        return cls(
            sys_id=record.get("sys_id"),
            asset_tag=record.get("asset_tag"),
            display_name=record.get("display_name"),
            stage=stage,
            install_status=record.get("install_status"),
            substatus=record.get("substatus"),
            install_date=_parse_date(record.get("install_date")),
            retired_date=_parse_date(record.get("retired_date")),
            disposal_date=_parse_date(record.get("disposal_date")),
            sys_updated_on=record.get("sys_updated_on"),
            days_in_stage=days_in_stage,
        )


# ---------------------------------------------------------------------------
# Health Metric (for the dashboard tool)
# ---------------------------------------------------------------------------


class AssetHealthMetric(BaseModel):
    """Aggregate health metrics returned by the health-metrics tool."""

    total_assets: int = 0
    active_assets: int = 0
    retired_assets: int = 0
    missing_assets: int = 0
    in_stock_assets: int = 0
    expiring_contracts_30d: int = 0
    underutilized_count: int = 0
    total_asset_value: float | None = Field(default=None)
