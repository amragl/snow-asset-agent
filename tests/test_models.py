"""Tests for snow_asset_agent.models."""

from __future__ import annotations

from datetime import date

from snow_asset_agent.models import (
    AssetBase,
    AssetContract,
    AssetHealthMetric,
    AssetLifecycle,
    HardwareAsset,
    SoftwareLicense,
    _parse_date,
    _parse_float,
    _parse_int,
)

# ------------------------------------------------------------------
# Parsing helpers
# ------------------------------------------------------------------


class TestParseDate:
    def test_valid_date_string(self):
        assert _parse_date("2024-06-15") == date(2024, 6, 15)

    def test_datetime_string(self):
        assert _parse_date("2024-06-15 10:30:00") == date(2024, 6, 15)

    def test_none(self):
        assert _parse_date(None) is None

    def test_empty_string(self):
        assert _parse_date("") is None

    def test_invalid_format(self):
        assert _parse_date("not-a-date") is None

    def test_date_object(self):
        d = date(2024, 1, 1)
        assert _parse_date(d) == d


class TestParseFloat:
    def test_valid_float_string(self):
        assert _parse_float("1200.50") == 1200.50

    def test_integer_string(self):
        assert _parse_float("100") == 100.0

    def test_none(self):
        assert _parse_float(None) is None

    def test_empty_string(self):
        assert _parse_float("") is None

    def test_invalid(self):
        assert _parse_float("abc") is None


class TestParseInt:
    def test_valid_int_string(self):
        assert _parse_int("42") == 42

    def test_float_string(self):
        assert _parse_int("42.7") == 42

    def test_none(self):
        assert _parse_int(None) is None

    def test_empty_string(self):
        assert _parse_int("") is None

    def test_invalid(self):
        assert _parse_int("abc") is None


# ------------------------------------------------------------------
# AssetBase
# ------------------------------------------------------------------


class TestAssetBase:
    def test_all_optional(self):
        asset = AssetBase()
        assert asset.sys_id is None
        assert asset.cost is None

    def test_from_snow_record_full(self):
        record = {
            "sys_id": "a1",
            "asset_tag": "TAG1",
            "display_name": "Test Asset",
            "model": "Model X",
            "model_category": "Computer",
            "install_status": "In use",
            "substatus": "In use",
            "assigned_to": "Jane Doe",
            "location": "NYC",
            "cost": "999.99",
            "purchase_date": "2023-01-15",
            "sys_created_on": "2023-01-15 08:00:00",
            "sys_updated_on": "2025-06-01 12:00:00",
        }
        asset = AssetBase.from_snow_record(record)
        assert asset.sys_id == "a1"
        assert asset.cost == 999.99
        assert asset.purchase_date == date(2023, 1, 15)

    def test_from_snow_record_dict_fields(self):
        """ServiceNow sometimes returns reference fields as dicts."""
        record = {
            "sys_id": "a1",
            "model": {"display_value": "Model Y", "value": "m1"},
            "assigned_to": {"display_value": "Bob", "value": "u1"},
            "location": {"display_value": "LA", "value": "l1"},
            "model_category": {"display_value": "Server", "value": "mc1"},
        }
        asset = AssetBase.from_snow_record(record)
        assert asset.model == "Model Y"
        assert asset.assigned_to == "Bob"
        assert asset.location == "LA"
        assert asset.model_category == "Server"

    def test_from_snow_record_empty(self):
        asset = AssetBase.from_snow_record({})
        assert asset.sys_id is None
        assert asset.cost is None

    def test_model_dump_json(self):
        asset = AssetBase(sys_id="x", cost=100.0)
        data = asset.model_dump(mode="json")
        assert data["sys_id"] == "x"
        assert data["cost"] == 100.0


# ------------------------------------------------------------------
# HardwareAsset
# ------------------------------------------------------------------


class TestHardwareAsset:
    def test_all_optional(self):
        hw = HardwareAsset()
        assert hw.serial_number is None
        assert hw.ci is None

    def test_from_snow_record(self):
        record = {
            "sys_id": "hw1",
            "asset_tag": "P100",
            "serial_number": "SN999",
            "cost": "1500",
            "purchase_date": "2023-03-01",
            "warranty_expiration": "2026-03-01",
            "ci": "ci001",
        }
        hw = HardwareAsset.from_snow_record(record)
        assert hw.serial_number == "SN999"
        assert hw.cost == 1500.0
        assert hw.warranty_expiration == date(2026, 3, 1)
        assert hw.ci == "ci001"

    def test_ci_as_dict(self):
        record = {"ci": {"value": "ci002", "display_value": "Server A"}}
        hw = HardwareAsset.from_snow_record(record)
        assert hw.ci == "ci002"

    def test_from_snow_record_empty(self):
        hw = HardwareAsset.from_snow_record({})
        assert hw.sys_id is None


# ------------------------------------------------------------------
# SoftwareLicense
# ------------------------------------------------------------------


class TestSoftwareLicense:
    def test_all_optional(self):
        lic = SoftwareLicense()
        assert lic.rights is None

    def test_from_snow_record(self):
        record = {
            "sys_id": "lic1",
            "software_model": "Office 365",
            "vendor": "Microsoft",
            "rights": "50",
            "allocated": "30",
            "cost": "1200.00",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        }
        lic = SoftwareLicense.from_snow_record(record)
        assert lic.product == "Office 365"
        assert lic.rights == 50
        assert lic.allocated == 30
        assert lic.end_date == date(2024, 12, 31)

    def test_from_snow_record_dict_fields(self):
        record = {
            "software_model": {"display_value": "Photoshop", "value": "ps1"},
            "vendor": {"display_value": "Adobe", "value": "v1"},
        }
        lic = SoftwareLicense.from_snow_record(record)
        assert lic.product == "Photoshop"
        assert lic.vendor == "Adobe"

    def test_from_snow_record_empty(self):
        lic = SoftwareLicense.from_snow_record({})
        assert lic.rights is None


# ------------------------------------------------------------------
# AssetContract
# ------------------------------------------------------------------


class TestAssetContract:
    def test_all_optional(self):
        c = AssetContract()
        assert c.vendor is None

    def test_from_snow_record(self):
        record = {
            "sys_id": "c1",
            "number": "CNT001",
            "short_description": "Support",
            "vendor": "Dell",
            "starts": "2024-01-01",
            "ends": "2025-01-01",
            "cost": "5000",
            "payment_amount": "416.67",
            "state": "Active",
        }
        c = AssetContract.from_snow_record(record)
        assert c.contract_number == "CNT001"
        assert c.cost == 5000.0
        assert c.starts == date(2024, 1, 1)

    def test_vendor_as_dict(self):
        record = {"vendor": {"display_value": "HP", "value": "v1"}}
        c = AssetContract.from_snow_record(record)
        assert c.vendor == "HP"

    def test_from_snow_record_empty(self):
        c = AssetContract.from_snow_record({})
        assert c.contract_number is None


# ------------------------------------------------------------------
# AssetLifecycle
# ------------------------------------------------------------------


class TestAssetLifecycle:
    def test_all_optional(self):
        lc = AssetLifecycle()
        assert lc.stage is None

    def test_from_snow_record(self):
        record = {
            "sys_id": "a1",
            "asset_tag": "TAG1",
            "install_status": "In use",
            "install_date": "2023-06-01",
        }
        lc = AssetLifecycle.from_snow_record(record, stage="Active/Deployed", days_in_stage=180)
        assert lc.stage == "Active/Deployed"
        assert lc.days_in_stage == 180
        assert lc.install_date == date(2023, 6, 1)

    def test_from_snow_record_empty(self):
        lc = AssetLifecycle.from_snow_record({})
        assert lc.sys_id is None


# ------------------------------------------------------------------
# AssetHealthMetric
# ------------------------------------------------------------------


class TestAssetHealthMetric:
    def test_defaults(self):
        m = AssetHealthMetric()
        assert m.total_assets == 0
        assert m.active_assets == 0
        assert m.total_asset_value is None

    def test_custom_values(self):
        m = AssetHealthMetric(
            total_assets=100,
            active_assets=80,
            retired_assets=10,
            missing_assets=5,
            in_stock_assets=5,
            expiring_contracts_30d=3,
            total_asset_value=500000.0,
        )
        assert m.total_assets == 100
        assert m.total_asset_value == 500000.0

    def test_model_dump(self):
        m = AssetHealthMetric(total_assets=10)
        data = m.model_dump()
        assert "total_assets" in data
