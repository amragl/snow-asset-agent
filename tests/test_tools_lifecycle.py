"""Tests for snow_asset_agent.tools.lifecycle."""

from __future__ import annotations

import requests

from snow_asset_agent.tools.lifecycle import STAGE_MAP, _days_since, get_asset_lifecycle
from tests.helpers import make_hardware_record, make_mock_response


class TestStageMap:
    def test_in_use(self):
        assert STAGE_MAP["In use"] == "Active/Deployed"

    def test_installed(self):
        assert STAGE_MAP["Installed"] == "Active/Deployed"

    def test_retired(self):
        assert STAGE_MAP["Retired"] == "Retired"

    def test_on_order(self):
        assert STAGE_MAP["On order"] == "Procurement"

    def test_in_stock(self):
        assert STAGE_MAP["In stock"] == "Received/Stocked"

    def test_in_maintenance(self):
        assert STAGE_MAP["In maintenance"] == "Maintenance"

    def test_missing(self):
        assert STAGE_MAP["Missing"] == "Missing"


class TestDaysSince:
    def test_valid_date(self):
        days = _days_since("2020-01-01")
        assert days is not None
        assert days > 0

    def test_none(self):
        assert _days_since(None) is None

    def test_empty_string(self):
        assert _days_since("") is None

    def test_invalid_format(self):
        assert _days_since("not-a-date") is None


class TestGetAssetLifecycle:
    def test_by_sys_id(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            json_data={"result": make_hardware_record(install_status="In use")}
        )
        result = get_asset_lifecycle(sys_id="abc123", client=client)
        assert "lifecycle" in result
        assert result["lifecycle"]["stage"] == "Active/Deployed"

    def test_by_asset_tag(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            json_data={"result": [make_hardware_record(install_status="Retired")]}
        )
        result = get_asset_lifecycle(asset_tag="TAG1", client=client)
        assert result["lifecycle"]["stage"] == "Retired"

    def test_no_id_provided(self, client_with_mock_session):
        result = get_asset_lifecycle(client=client_with_mock_session)
        assert "error" in result
        assert result["error_code"] == "SN_VALIDATION_ERROR"

    def test_not_found_by_tag(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        result = get_asset_lifecycle(asset_tag="MISSING", client=client)
        assert "error" in result
        assert result["error_code"] == "SN_NOT_FOUND"

    def test_connection_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.ConnectionError("fail")
        result = get_asset_lifecycle(sys_id="abc", client=client)
        assert "error" in result

    def test_unknown_status_uses_raw(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            json_data={"result": make_hardware_record(install_status="Custom Status")}
        )
        result = get_asset_lifecycle(sys_id="abc", client=client)
        assert result["lifecycle"]["stage"] == "Custom Status"

    def test_days_in_stage_calculated(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            json_data={"result": make_hardware_record(sys_updated_on="2020-01-01 00:00:00")}
        )
        result = get_asset_lifecycle(sys_id="abc", client=client)
        assert result["lifecycle"]["days_in_stage"] is not None
        assert result["lifecycle"]["days_in_stage"] > 0

    def test_output_structure(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": make_hardware_record()})
        result = get_asset_lifecycle(sys_id="abc", client=client)
        lc = result["lifecycle"]
        assert "sys_id" in lc
        assert "stage" in lc
        assert "install_status" in lc
        assert "days_in_stage" in lc

    def test_500_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=500, ok=False, json_data={"error": {"message": "internal"}}
        )
        result = get_asset_lifecycle(sys_id="abc", client=client)
        assert "error" in result

    def test_timeout_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.Timeout("timed out")
        result = get_asset_lifecycle(sys_id="abc", client=client)
        assert "error" in result

    def test_empty_install_status(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_hardware_record(install_status="")
        client._session.get.return_value = make_mock_response(json_data={"result": rec})
        result = get_asset_lifecycle(sys_id="abc", client=client)
        assert result["lifecycle"]["stage"] == "Unknown"

    def test_missing_updated_on(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_hardware_record()
        rec.pop("sys_updated_on", None)
        client._session.get.return_value = make_mock_response(json_data={"result": rec})
        result = get_asset_lifecycle(sys_id="abc", client=client)
        assert result["lifecycle"]["days_in_stage"] is None

    def test_401_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=401, ok=False, json_data={"error": {"message": "unauth"}}
        )
        result = get_asset_lifecycle(sys_id="abc", client=client)
        assert "error" in result

    def test_both_none(self, client_with_mock_session):
        result = get_asset_lifecycle(sys_id=None, asset_tag=None, client=client_with_mock_session)
        assert "error" in result

    def test_empty_strings(self, client_with_mock_session):
        result = get_asset_lifecycle(sys_id="", asset_tag="", client=client_with_mock_session)
        assert "error" in result
